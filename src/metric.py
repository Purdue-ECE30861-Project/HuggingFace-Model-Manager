import abc
import typing
from pydantic import BaseModel
from sortedcontainers import SortedDict


class ModelMetadata(BaseModel):
    model_url: typing.Optional[str]
    code_url: typing.Optional[str]
    dataset_url: typing.Optional[str]


class BaseMetric(abc.ABC):
    metric_name: str
    priority: int


    def __init__(self):
        self.score: float = 0.0

    def run(self):
        self.setup_resources()
        self.score = self.calculate_score()

    @abc.abstractmethod
    # we make this an abstract method because it may be best to set up necessary resources in multithreaded environment for high speed cli
    def setup_resources(self):
        pass

    @abc.abstractmethod
    def calculate_score(self) -> float:
        pass


class NetScore:
    def __init__(self, metrics: typing.Iterable[BaseMetric], model_metadata: ModelMetadata):
        self.individual_scores: dict[str, float] = {metric.metric_name: metric.score for metric in metrics}

    def __calculate_net_score(self, metrics: typing.Iterable[BaseMetric]):
        priority_organized_scores: SortedDict[int, list[float]] = SortedDict()
        num_metrics: int = len(priority_organized_scores)

        for metric in metrics:
            if metric.priority in priority_organized_scores:
                priority_organized_scores[metric.priority].append(metric.score)
            else:
                priority_organized_scores[metric.priority] = [metric.score]

        compressed_scores: list[list[float]] = self.__compress_priorities(priority_organized_scores)
        priority_proportions: list[float] = self.__get_priority_proportions(compressed_scores, num_metrics)
        aggregated_scores: list[float] = [sum(scores) for scores in compressed_scores]

        volume_adjusted_scores: list[float] = [volume * raw_score for volume, raw_score in zip(priority_proportions, aggregated_scores)]
        normalized_scores: list[float]

    def __compress_priorities(self, priority_organized_scores: SortedDict[int, list[float]]) -> list[list[float]]:
        """
        Trims out intermediary space. Say you accidentally assigned priority 1 and 3, you would be left with priority 1 and 2. Outputs list where index correspond to prioritiy of scores
        :param priority_organized_scores:
        :return:
        """
        scores: list[list[float]] = []

        for value in priority_organized_scores.values():
            scores.append(value)

        return priority_organized_scores

    def __get_priority_proportions(self, compressed_scores: list[list[float]], total_size: int) -> list[float]:
        priority_proportions: list[float] = []

        for scores in compressed_scores:
            priority_proportions.append(len(scores) / total_size)

        return priority_proportions


    def append_to_db(self, database_interface: typing.Any) -> bool:
        pass

    def __str__(self):
        pass

