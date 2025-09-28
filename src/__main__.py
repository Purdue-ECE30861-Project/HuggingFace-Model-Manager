import typer
from pathlib import Path
import subprocess
import sys
import json
import os
import time
import logging
from typing import List
from database import (
    SQLiteAccessor,
    FloatMetric,
    DictMetric,
    ModelStats,
    PROD_DATABASE_PATH,
)
from workflow import MetricStager, run_workflow
from config import *
from metrics.performance_claims import PerformanceClaimsMetric
from metrics.dataset_and_code import DatasetAndCodeScoreMetric
from metrics.bus_factor import BusFactorMetric
from metrics.ramp_up_time import RampUpMetric
from metrics.license import LicenseMetric
from metrics.code_quality import CodeQualityMetric
from metrics.size_metric import SizeMetric


def setup_logging():
    """
    Setup logging based on environment variables
    """
    log_level = int(os.environ.get("LOG_LEVEL", 0))
    log_file = os.environ.get("LOG_FILE")

    if log_level == 0:
        logging.disable(logging.CRITICAL)
        return

    level = logging.INFO if log_level == 1 else logging.DEBUG

    if log_file:
        logging.basicConfig(
            filename=log_file,
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        logging.basicConfig(level=level)


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

            # Split by comma and clean up whitespace
            parts = [part.strip() for part in line.split(",")]

            code_link, dataset_link, model_link = parts[0], parts[1], parts[2]

            # Clean up empty strings and "blank" indicators
            code_link = (
                code_link
                if code_link and code_link.lower() not in ["", "blank", "none", "n/a"]
                else None
            )
            dataset_link = (
                dataset_link
                if dataset_link
                and dataset_link.lower() not in ["", "blank", "none", "n/a"]
                else None
            )
            model_link = (
                model_link
                if model_link and model_link.lower() not in ["", "blank", "none", "n/a"]
                else None
            )

            if not model_link:
                logging.warning(f"Line {line_num}: No model link found, skipping")
                continue

            model_urls = ModelURLs(
                model=model_link, dataset=dataset_link, codebase=code_link
            )
            model_groups.append(model_urls)

        logging.info(f"Parsed {len(model_groups)} models from {url_file}")
        return model_groups

    except FileNotFoundError:
        typer.echo(f"Error: URL file '{url_file}' not found.", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error reading URL file: {e}", err=True)
        raise typer.Exit(code=1)


def calculate_metrics(model_urls: ModelURLs) -> ModelStats: # do we have a funciton to infer urls?
    """
    Calculate all metrics for a given model
    """
    
    config = ConfigContract(
        num_processes=5,
        priority_function="PFReciprocal",
        target_platform="desktop_pc",
        local_storage_directory = os.path.dirname(os.path.abspath(__file__)) + "local_storage",
        model_path_name = "models",
        code_path_name = "code",
        dataset_path_name = "dataset"
    )

    model_paths: ModelPaths = generate_model_paths(config, model_urls)

    start_time: float = time.time()

    split_url = model_urls.model.split("huggingface.co/")
    parts = split_url[1].split("/")
    if len(parts) > 2:
        model_name = '/'.join(parts[0:2])
   
    stager = MetricStager(config)

    stager.attach_metric(RampUpMetric(1.0, "cpu"), 1)
    stager.attach_metric(BusFactorMetric(), 2)
    stager.attach_metric(PerformanceClaimsMetric(), 2)
    stager.attach_metric(LicenseMetric(), 1)
    stager.attach_metric(SizeMetric(), 3)
    stager.attach_metric(DatasetAndCodeScoreMetric(model_urls.dataset, model_urls.codebase), 2)
    stager.attach_metric(CodeQualityMetric(), 1)

    analyzer_output = run_workflow(stager, model_urls, model_paths, config)
    db_metrics = []

    individual_scores: dict = analyzer_output.individual_scores

    for metric in analyzer_output.metrics:
        latency_ms = int(metric.runtime * 1000)
        if isinstance(metric.score, dict):
            db_metrics.append(DictMetric(metric.metric_name, metric.score, latency_ms))
        else:
            db_metrics.append(FloatMetric(metric.metric_name, metric.score, latency_ms))
    # Calculate net score latency
    net_latency: float = time.time() - start_time

    return ModelStats(
        model_url=model_urls.model,
        database_url=model_urls.dataset,
        code_url=model_urls.codebase,
        name=model_name,
        net_score=analyzer_output.score,
        net_score_latency=net_latency,
        metrics=db_metrics,
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
            result = subprocess.run(["pip", "install", "-r", str(deps_file)])
            if result.returncode != 0:
                typer.echo(
                    f"An error occurred while installing dependencies:\n{result.stderr}",
                    err=True,
                )
                raise typer.Exit(code=1)
            typer.echo("Dependencies installed successfully.")
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def test():
    import unittest

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
        suite = loader.discover(start_dir, pattern="test*.py")
        total_tests = suite.countTestCases()

        runner = unittest.TextTestRunner(verbosity=2)#, stream=open(os.devnull, "w"))
        result = runner.run(suite)
        cov.stop()
        cov.save()
        coverage_data = cov.get_data()

        # Find line coverage
        total_lines = 0
        covered_lines = 0
        for filename in coverage_data.measured_files():
            if str(src_path) in filename:
                analysis = cov.analysis2(filename)
                total_lines += len(analysis[1]) + len(analysis[2])
                covered_lines += len(analysis[1])

        coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        passed_tests = total_tests - len(result.failures) - len(result.errors)
        typer.echo(
            f"{passed_tests}/{total_tests} test cases passed. {coverage_percent:.0f}% line coverage achieved."
        )
        
        if result.failures:
            typer.echo(f"\nFailures: {len(result.failures)}")
        if result.errors:
            typer.echo(f"Errors: {len(result.errors)}")
        
        if result.failures or result.errors:
            raise typer.Exit(code=1)
        else:
            raise typer.Exit(code=0)
        
    except ImportError:
        typer.echo(
            "Error: 'coverage' package not installed. Please run 'install' command first.",
            err=True,
        )
        raise typer.Exit(code=1)


@app.command()
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

        setup_logging()
        basic_schema = [
            FloatMetric("ramp_up_time", 0.0, 0),
            FloatMetric("bus_factor", 0.0, 0),
            FloatMetric("performance_claims", 0.0, 0),
            FloatMetric("license", 0.0, 0),
            DictMetric(
                "size_score",
                {
                    "raspberry_pi": 0.0,
                    "jetson_nano": 0.0,
                    "desktop_pc": 0.0,
                    "aws_server": 0.0,
                },
                0,
            ),
            FloatMetric("dataset_and_code_score", 0.0, 0),
            FloatMetric("dataset_quality", 0.0, 0),
            FloatMetric("code_quality", 0.0, 0),
        ]

        db = SQLiteAccessor(PROD_DATABASE_PATH, basic_schema)

        for model_urls in model_groups:
            model_url = model_urls.model

            # Check if model already analyzed
            if db.check_entry_in_db(model_url):
                logging.info(
                    f"Model {model_url} already analyzed. Fetching from database..."
                )
                stats = db.get_model_statistics(model_url)
            else:
                logging.info(f"Analyzing model {model_url}...")

                # Calculate metrics and add to database
                #print("HERE!!!")
                stats = calculate_metrics(model_urls)
                db.add_to_db(stats)

            results = {
                "name": stats.name,
                "category": "MODEL",
                "net_score": stats.net_score,
                "net_score_latency": stats.net_score_latency,
            }

            for metric in stats.metrics:
                if isinstance(metric, FloatMetric):
                    results[metric.name] = metric.data
                    results[f"{metric.name}_latency"] = metric.latency
                elif isinstance(metric, DictMetric):
                    results[metric.name] = metric.data
                    results[f"{metric.name}_latency"] = metric.latency

            typer.echo(json.dumps(results))

    except Exception as e:
        typer.echo(f"An error occurred during analysis: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
