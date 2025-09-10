import abc
import typing
from itertools import starmap
from pydantic import BaseModel
from sortedcontainers import SortedDict


class ModelURLs(BaseModel):
    model: typing.Optional[str]
    codebase: typing.Optional[str]
    dataset: typing.Optional[str]


class BaseMetric(abc.ABC):
    metric_name: str

    def __init__(self):
        self.score: float = 0.0
        self.url: str = ""
        self.priority = 1
        self.target_platform: str = ""

    def run(self) -> typing.Self:
        self.setup_resources()
        self.score = self.calculate_score()

        return self

    def set_params(self, priority: int, platform: str) -> typing.Self:
        assert(priority > 0)
        self.priority = priority
        self.target_platform = platform
        
        return self

    def set_url(self, url: str):
        if not url:
            raise IOError("The provided URL was invalid") # cli will handle this error if invalid url

        self.url = url

    @abc.abstractmethod
    # we make this an abstract method because it may be best to set up necessary resources in multithreaded environment for high speed cli
    def setup_resources(self):
        pass

    @abc.abstractmethod
    def calculate_score(self) -> float:
        pass


class PriorityFunction(abc.ABC):
    @abc.abstractmethod
    def calculate_priority_weight(self, priority: int) -> float:
        pass


class PFExponentialDecay(PriorityFunction):
    def __init__(self, base_coefficient: int):
        assert(base_coefficient > 1)
        self.base_coefficient: int = base_coefficient

    def calculate_priority_weight(self, priority: int) -> float:
        return self.base_coefficient ** -(priority - 1)


class PFReciprocal(PriorityFunction):
    def calculate_priority_weight(self, priority: int) -> float:
        return 1 / priority


PRIORITY_FUNCTIONS: dict[str, typing.Type[PriorityFunction]] = {
    'PFExponentialDecay': PFExponentialDecay,
    'PFReciprocal': PFReciprocal
}


class NetScoreCalculator:
    def __init__(self, priority_function: typing.Type[PriorityFunction]):
        self.priority_function: typing.Type[PriorityFunction] = priority_function

    def calculate_net_score(self, metrics: list[BaseMetric]):
        num_metrics: int = len(metrics)

        priority_organized_scores: SortedDict[int, list[float]] = self.generate_scores_priority_dict(metrics)
        compressed_scores: list[list[float]] = self.compress_priorities(priority_organized_scores)
        priority_weights: list[float] = self.get_priority_weights(compressed_scores, num_metrics)
        aggregated_scores: list[float] = [self.sum_scores(scores) for scores in compressed_scores]

        net_score: float = sum(
            list(
                starmap(lambda score, weight: score * weight, zip(aggregated_scores, priority_weights))
            )
        )

        return net_score

    def generate_scores_priority_dict(self, metrics: list[BaseMetric]) -> SortedDict[int, list[float]]:
        priority_organized_scores: SortedDict[int, list[float]] = SortedDict()
        for metric in metrics:
            if metric.priority in priority_organized_scores:
                priority_organized_scores[metric.priority].append(metric.score)
            else:
                priority_organized_scores[metric.priority] = [metric.score]

        return priority_organized_scores

    def sum_scores(self, scores: list[float]) -> float:
        scores: list[float] = [score / len(scores) for score in scores]
        return sum(scores)

    def compress_priorities(self, priority_organized_scores: SortedDict[int, list[float]]) -> list[list[float]]:
        """
        Trims out intermediary space. Say you accidentally assigned priority 1 and 3, you would be left with priority 1 and 2. Outputs list where index correspond to prioritiy of scores
        :param priority_organized_scores:
        :return:
        """
        scores: list[list[float]] = []

        for value in priority_organized_scores.values():
            scores.append(value)

        return scores

    def get_priority_weights(self, compressed_scores: list[list[float]], total_size: int) -> list[float]:
        priority_proportions: list[float] = []

        for priority, scores in enumerate(compressed_scores):
            priority_weight: float = self.priority_function.calculate_priority_weight(priority + 1)
            priority_proportions.append(priority_weight * len(scores) / total_size)

        normalized_weights: list[float] = list(map(lambda x: x / sum(priority_proportions), priority_proportions))

        return normalized_weights


class AnalyzerOutput:
    def __init__(self, priority_function: typing.Type[PriorityFunction], metrics: list[BaseMetric], model_metadata: ModelURLs):
        self.individual_scores: dict[str, float] = {metric.metric_name: metric.score for metric in metrics}
        self.model_metadata: ModelURLs = model_metadata
        self.score: float = NetScoreCalculator(priority_function).calculate_net_score(metrics)

    def append_to_db(self, database_interface: typing.Any) -> bool:
        pass

    def __str__(self):
        pass

