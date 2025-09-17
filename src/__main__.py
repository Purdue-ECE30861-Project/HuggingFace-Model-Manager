import typer
from pathlib import Path
import subprocess
import sys
import json
from typing import List
from metric import ModelURLs, BaseMetric, AnalyzerOutput, PFExponentialDecay
from database import SQLiteAccessor, FloatMetric, DictMetric, ModelStats, PROD_DATABASE_PATH, ModelSetDatabase

def parse_url_file(url_file: Path) -> List[str]:
    """
    Parses a file containing URLs and categorizes them into model, codebase, and dataset URLs.
    """
    try:
        urls = [line.strip() for line in url_file.read_text().splitlines() if line.strip()]
        return urls
    except FileNotFoundError:
        print(f"Error: URL file '{url_file}' not found.", err=True)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading URL file: {e}", err=True)
        sys.exit(1)
       
app = typer.Typer()

@app.command()
def install():
    """
    Installs necessary dependencies from dependencies.txt
    """
    print("Installing dependencies...")
    try:
        deps_file = Path(__file__).parent.parent / "dependencies.txt"
        if deps_file.exists():
            result = subprocess.run(["pip", "install", "--user", "-r", str(deps_file)])# capture_output=True, text=True)
            if result.returncode != 0:
                print(f"An error occurred while installing dependencies:\n{result.stderr}", err = True)
                sys.exit(1)
            print("Dependencies installed successfully.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}", err = True)
        sys.exit(1)
    
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
        suite = loader.discover(start_dir, pattern='test*.py')
        total_tests = 0
        
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
        
        total_lines = 0
        covered_lines = 0
        for filename in coverage_data.measured_files():
            if str(src_path) in filename:  # Only count source files
                analysis = cov.analysis2(filename)
                total_lines += len(analysis[1]) + len(analysis[2])  # executed + missing
                covered_lines += len(analysis[1])  # executed lines
        
        coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        passed_tests = total_tests - len(result.failures) - len(result.errors)
        print(f"{passed_tests}/{total_tests} test cases passed. {coverage_percent:.0f}% line coverage achieved.")
        
        if result.failures or result.errors:
            sys.exit(1)
        sys.exit(0)
    except ImportError:
        print("Error: 'coverage' package not installed. Please run 'install' command first.", err=True)
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        sys.exit(1)


@app.callback(invoke_without_command=True)
def analyze(url_file: Path):
    print("Analyzing model...")
    
    urls = parse_url_file(url_file)
    if not urls:
        print("Error: No URLs found in file.", err=True)
        sys.exit(1)
    
    dataset_url, code_url, model_url = None, None, None
    for url in urls:
        if "huggingface.co/datasets" in url:
            dataset_url = url
        elif "github.com" in url:
            code_url = url
        elif "huggingface.co" in url:
            model_url = url
    
    model_name = model_url.split('/')[-1]
    model_db = ModelSetDatabase()
    entry_id = model_db.add_if_not_exists(model_url, code_url, dataset_url)
    
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
    
    try:
        if db.check_entry_in_db(model_url):
            print("Model already analyzed. Fetching from database...")
            stats = db.get_model_statistics(model_url)
        else:
            model_urls = ModelURLs(
                model=model_url,
                dataset=dataset_url,
                codebase=code_url
            )
            
            #TODO: implement actual metric calculations
            stats = ModelStats(model_url, model_name, 0.0, 0, basic_schema)
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
                
        print(json.dumps(results))
        
    except Exception as e:
        print(f"An error occurred during analysis: {e}", err = True)
        sys.exit(1)
        
if __name__ == "__main__":
    app()