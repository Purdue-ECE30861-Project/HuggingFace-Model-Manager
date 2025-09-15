from multiprocessing import Pool
from typing import Literal, Optional
from pydantic import BaseModel
import typing
from metric import BaseMetric, ModelURLs, AnalyzerOutput, PRIORITY_FUNCTIONS


DATASET = 'dataset'
CODEBASE = 'codebase'
MODEL = 'model'


class ConfigContract(BaseModel):
    """
    Configuration contract for the workflow, specifying number of processes,
    priority function, and target platform.
    """
    num_processes: int = 1
    priority_function: Literal['PFReciprocal', 'PFExponentialDecay'] = 'PFReciprocal'
    target_platform: str = ""


def run_metric(metric: BaseMetric) -> BaseMetric:
    """
    Runs a single metric by calling its run method.
    Args:
        metric (BaseMetric): The metric instance to run.
    Returns:
        BaseMetric: The metric instance after running.
    """
    return metric.run()


class MetricRunner:
    def __init__(self, metrics: list[BaseMetric]): # single threaded by default
        self.metrics: list[BaseMetric] = metrics
        self.multiprocessing_pool: Optional[Pool] = None

    def run(self) -> list[BaseMetric]:
        """
        Runs all metrics using the configured multiprocessing pool.
        Returns:
            list[BaseMetric]: List of processed metric instances.
        Raises:
            Exception: If no multiprocessing pool has been created.
        """
        if self.multiprocessing_pool:
            with self.multiprocessing_pool as pool:
                results: list[BaseMetric] = pool.map(run_metric, self.metrics)
        else:
            raise Exception("No multiprocessing pool has been created")

        return results

    def set_num_processes(self, num_processes: int) -> typing.Self:
        """
        Sets the number of processes for multiprocessing.
        Args:
            num_processes (int): Number of processes to use.
        Returns:
            Self: The MetricRunner instance with updated pool.
        """
        self.multiprocessing_pool = Pool(num_processes)
        return self


class MetricStager:
    """
    Stages metrics by grouping them and attaching configuration and URLs.
    """
    def __init__(self, config: ConfigContract):
        """
        Initializes the MetricStager.
        Args:
            config (ConfigContract): Configuration for staging metrics.
        """
        self.metrics: dict[str, list[BaseMetric]] = {
            'dataset': [],
            'codebase': [],
            'model': []
        }
        self.config: ConfigContract = config

    def attach_metric(self, group: str, metric: BaseMetric, priority: int) -> typing.Self:
        """
        Attaches a metric to a group with a given priority and platform.
        Args:
            group (str): The group to attach the metric to ('dataset', 'codebase', or 'model').
            metric (BaseMetric): The metric instance to attach.
            priority (int): The priority value for the metric.
        Returns:
            Self: The MetricStager instance with the metric attached.
        Raises:
            KeyError: If the group is invalid.
        """
        metric.set_params(priority, self.config.target_platform)
        try:
            self.metrics[group].append(metric)
        except KeyError:
            raise KeyError(f"Invalid group: {group}")

        return self

    def attach_model_urls(self, model_metadata: ModelURLs) -> MetricRunner:
        """
        Attaches URLs from model metadata to the corresponding metrics.
        Args:
            model_metadata (ModelURLs): The model metadata containing URLs.
        Returns:
            MetricRunner: A MetricRunner instance with staged metrics.
        """
        dictionary_urls: dict[str, str | None] = model_metadata.dict()
        staged_metrics: list[BaseMetric] = []

        for url_type, url in dictionary_urls.items():
            if url:
                for metric in self.metrics[url_type]:
                    metric.set_url(url)
                    staged_metrics.append(metric)

        return MetricRunner(staged_metrics)


def run_workflow(metric_stager: MetricStager, input_urls: ModelURLs, config: ConfigContract) -> AnalyzerOutput:
    """
    Runs the complete workflow: attaches URLs, sets up multiprocessing, runs metrics,
    and returns the analysis output.
    Args:
        metric_stager (MetricStager): The metric stager with staged metrics.
        input_urls (ModelURLs): The input model URLs.
        config (ConfigContract): The workflow configuration.
    Returns:
        AnalyzerOutput: The output of the analysis.
    """
    # HERE it should check if the inputted models are already stored locally
    metric_runner: MetricRunner = metric_stager.attach_model_urls(input_urls).set_num_processes(config.num_processes)
    processed_metrics: list[BaseMetric] = metric_runner.run()

    return AnalyzerOutput(PRIORITY_FUNCTIONS[config.priority_function], processed_metrics, input_urls)



