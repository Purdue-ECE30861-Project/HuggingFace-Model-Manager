from multiprocessing import Pool
from typing import Literal, Optional
from metric import *


DATASET = 'dataset'
CODEBASE = 'codebase'
MODEL = 'model'


class ConfigContract(BaseModel):
    num_processes: int = 1
    priority_function: Literal['PFReciprocal', 'PFExponentialDecay'] = 'PFReciprocal'
    target_platform: str


class MetricRunner:
    def __init__(self, metrics: list[BaseMetric]): # single threaded by default
        self.metrics: list[BaseMetric] = metrics
        self.multiprocessing_pool: Optional[Pool] = None

    def run(self) -> list[BaseMetric]:
        if self.multiprocessing_pool:
            with self.multiprocessing_pool as pool:
                results: list[BaseMetric] = pool.map(lambda metric: metric.run(), self.metrics)
        else:
            raise Exception("No multiprocessing pool has been created")

        return results

    def set_num_processes(self, num_processes: int) -> typing.Self:
        self.multiprocessing_pool = Pool(num_processes)
        return self


class MetricStager:
    def __init__(self, config: ConfigContract):
        self.metrics: dict[str, list[BaseMetric]] = {
            'dataset': [],
            'codebase': [],
            'model': []
        }
        self.config: ConfigContract = config

    def attach_metric(self, group: str, metric: BaseMetric, priority: int) -> typing.Self:
        metric.set_params(priority, self.config.target_platform)
        try:
            self.metrics[group].append(metric)
        except KeyError:
            raise KeyError(f"Invalid group: {group}")

        return self

    def attach_model_urls(self, model_metadata: ModelURLs) -> MetricRunner:
        dictionary_urls: dict[str, str | None] = model_metadata.dict()
        staged_metrics: list[BaseMetric] = []

        for url_type, url in dictionary_urls.items():
            if url:
                for metric in self.metrics[url_type]:
                    metric.set_url(url)
                    staged_metrics.append(metric)

        return MetricRunner(staged_metrics)


def run_workflow(metric_stager: MetricStager, input_urls: ModelURLs, config: ConfigContract) -> AnalyzerOutput:
    # HERE it should check if the inputted models are already stored locally
    metric_runner: MetricRunner = metric_stager.attach_model_urls(input_urls).set_num_processes(config.num_processes)
    processed_metrics: list[BaseMetric] = metric_runner.run()

    return AnalyzerOutput(PRIORITY_FUNCTIONS[config.priority_function], processed_metrics, input_urls)



