import typer
from pathlib import Path
import subprocess
import sys
import json
from typing import List
from metric import ModelURLs
from database import SQLiteAccessor, FloatMetric, DictMetric, ModelStats, PROD_DATABASE_PATH
from workflow import MetricStager, ConfigContract, run_workflow
from metrics.performance_claims import PerformanceClaimsMetric
from metrics.dataset_and_code import DatasetAndCodeScoreMetric
from metrics.bus_factor import BusFactorMetric
from metrics.ramp_up_time import RampUpMetric
from metrics.license import LicenseMetric
from metrics.code_quality import CodeQualityMetric
from metrics.size_score import SizeScoreMetric

def parse_url_file(url_file: Path) -> List[ModelURLs]:
    """
    Parses a file containing comma-separated URLs and returns ModelURLs objects.
    Format: code_link, dataset_link, model_link (per line)
    """
    try:
        model_groups = []
        
        lines = url_file.read_text().splitlines()
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            #Split by comma and clean up whitespace
            parts = [part.strip() for part in line.split(',')]
                
            code_link, dataset_link, model_link = parts[0], parts[1], parts[2]
            
            #Clean up empty strings and "blank" indicators
            code_link = code_link if code_link and code_link.lower() not in ['', 'blank', 'none', 'n/a'] else None
            dataset_link = dataset_link if dataset_link and dataset_link.lower() not in ['', 'blank', 'none', 'n/a'] else None
            model_link = model_link if model_link and model_link.lower() not in ['', 'blank', 'none', 'n/a'] else None
            
            model_urls = ModelURLs(
                model=model_link,
                dataset=dataset_link,
                codebase=code_link
            )
            model_groups.append(model_urls)
            
        return model_groups
        
    except FileNotFoundError:
        typer.echo(f"Error: URL file '{url_file}' not found.", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error reading URL file: {e}", err=True)
        raise typer.Exit(code=1)
    
def calculate_metrics(model_urls: ModelURLs) -> ModelStats:
    """
    Calculate all metrics for a given model
    """
    #Using these values for now, will have to use config file to actually configure
    config = ConfigContract(num_processes=1, priority_function='PFReciprocal',target_platform='desktop_pc')
    
    metrics = [
        RampUpMetric(),
        BusFactorMetric(), 
        PerformanceClaimsMetric(),
        LicenseMetric(),
        SizeScoreMetric(),
        DatasetAndCodeScoreMetric(),
        CodeQualityMetric()
    ]
    model_name = model_urls.model.split('/')[-1] if '/' in model_urls.model else model_urls.model
    
    for metric in metrics:
        #Set dataset URL for metrics that need it
        if hasattr(metric, 'dataset_url') and model_urls.dataset:
            metric.dataset_url = model_urls.dataset
        
        #Set codebase URL for metrics that need it
        if hasattr(metric, 'codebase_url') and model_urls.codebase:
            metric.codebase_url = model_urls.codebase
        
    stager = MetricStager(config)
    
    stager.attach_metric('model', metrics[0], 1)
    stager.attach_metric('model', metrics[1], 2)
    stager.attach_metric('model', metrics[2], 2)
    stager.attach_metric('model', metrics[3], 1)
    stager.attach_metric('model', metrics[4], 3)
    stager.attach_metric('model', metrics[5], 2)
    
    if model_urls.codebase:
        stager.attach_metric('codebase', metrics[6], 2)
        
    analyzer_output = run_workflow(stager, model_urls, config)
    
    db_metrics = []
    for metric in metrics:
        metric_name = metric.metric_name
        if metric_name == "size_score":
            #Handle special case for size_score (returns dictionary)
            size_scores = analyzer_output.individual_scores.get(metric_name, {
                "raspberry_pi": 0.0,
                "jetson_nano": 0.0,
                "desktop_pc": 0.0,
                "aws_server": 0.0
            })
            latency_ms = int(metric.runtime * 1000) if hasattr(metric, 'runtime') else 0
            db_metrics.append(DictMetric(metric_name, size_scores, latency_ms))
        else:
            #Regular float metrics
            score = analyzer_output.individual_scores.get(metric_name, 0.0)
            latency_ms = int(metric.runtime * 1000) if hasattr(metric, 'runtime') else 0
            db_metrics.append(FloatMetric(metric_name, score, latency_ms))
    
    # Calculate net score latency
    net_latency = sum(m.latency for m in db_metrics)
    
    return ModelStats(
        url=model_urls.model,
        name=model_name, 
        net_score=analyzer_output.score,
        net_score_latency=net_latency,
        metrics=db_metrics
    )
       
app = typer.Typer()

@app.command()
def install():
    """
    Installs necessary dependencies from dependencies.txt
    """
    typer.echo("Installing dependencies...")
    try:
        deps_file = Path(__file__).parent.parent / "dependencies.txt"
        if deps_file.exists():
            result = subprocess.run(["pip", "install", "--user", "-r", str(deps_file)])
            if result.returncode != 0:
                typer.echo(f"An error occurred while installing dependencies:\n{result.stderr}", err = True)
                raise typer.Exit(code=1)
            typer.echo("Dependencies installed successfully.")
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}", err = True)
        raise typer.Exit(code=1)
    
@app.command()
def test(): 
    import unittest
    import os
    
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        
    tests_path = Path(__file__).parent.parent / "tests"
    if str(tests_path) not in sys.path:
        sys.path.insert(0, str(tests_path))
        
    try:
        import coverage
        
        cov = coverage.Coverage(source=[str(src_path)])
        cov.start()
        
        loader = unittest.TestLoader()
        start_dir = str(tests_path)
        suite = loader.discover(start_dir, pattern='*.py')
        total_tests = 0
        
        #Count total tests
        def count_tests(test_suite):
            nonlocal total_tests
            for test in test_suite:
                if isinstance(test, unittest.TestSuite):
                    count_tests(test)
                else:
                    total_tests += 1
        
        count_tests(suite)
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        cov.stop()
        cov.save()
        coverage_report = cov.report(show_missing=False, file=open(os.devnull, 'w'))
        coverage_data = cov.get_data()
        
        #Find line coverage
        total_lines = 0
        covered_lines = 0
        for filename in coverage_data.measured_files():
            if str(src_path) in filename:
                analysis = cov.analysis2(filename)
                total_lines += len(analysis[1]) + len(analysis[2])
                covered_lines += len(analysis[1])
        
        coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        passed_tests = total_tests - len(result.failures) - len(result.errors)
        typer.echo(f"{passed_tests}/{total_tests} test cases passed. {coverage_percent:.0f}% line coverage achieved.")
        
        if result.failures or result.errors:
            raise typer.Exit(code=1)
        raise typer.Exit(code=1)
    except ImportError:
        typer.echo("Error: 'coverage' package not installed. Please run 'install' command first.", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error running tests: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def analyze(url_file: Path):
    """
    Analyzes models based on URLs provided in a file. 
    Will add model to database if not already present.
    """
    typer.echo("Analyzing model...")
    
    try:
        model_groups = parse_url_file(url_file)
        if not model_groups:
            typer.echo("Error: No valid model URLs found in file.", err=True)
            raise typer.Exit(code=1)
        
        basic_schema = [
                FloatMetric("ramp_up_time", 0.0, 0),
                FloatMetric("bus_factor", 0.0, 0),
                FloatMetric("performance_claims", 0.0, 0),
                FloatMetric("license", 0.0, 0),
                DictMetric("size_score", {
                    "raspberry_pi": 0.0,
                    "jetson_nano": 0.0,
                    "desktop_pc": 0.0,
                    "aws_server": 0.0
                }, 0),
                FloatMetric("dataset_and_code score", 0.0, 0),
                FloatMetric("dataset_quality", 0.0, 0),
                FloatMetric("code_quality", 0.0, 0),
            ]
        
        db = SQLiteAccessor(PROD_DATABASE_PATH, basic_schema)
        
        for model_urls in model_groups:
            model_url = model_urls.model
            
            #Check if model already analyzed
            if db.check_entry_in_db(model_url):
                typer.echo("Model already analyzed. Fetching from database...")
                stats = db.get_model_statistics(model_url)
            else:
            #Calculate metrics and add to database
                stats = calculate_metrics(model_urls)
                db.add_to_db(stats)
            
            results = {
                "name": stats.name,
                "category": "MODEL",
                "net_score": stats.net_score,
                "net_score_latency": stats.net_score_latency
                }

            for metric in stats.metrics:
                if isinstance(metric, FloatMetric):
                    results[metric.metric_name] = metric.data
                    results[f"{metric.metric_name}_latency"] = metric.latency
                elif isinstance(metric, DictMetric):
                    results[metric.metric_name] = metric.data
                    results[f"{metric.metric_name}_latency"] = metric.latency
                    
            typer.echo(json.dumps(results))
        
    except Exception as e:
        typer.echo(f"An error occurred during analysis: {e}", err = True)
        raise typer.Exit(code=1)
        
if __name__ == "__main__":
    app()