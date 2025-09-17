import abc
import typing
import os
from itertools import starmap
from pydantic import BaseModel
from sortedcontainers import SortedDict


class ModelURLs(BaseModel):
    """
    Stores URLs related to a model, including model, codebase, and dataset URLs.
    """
    model: typing.Optional[str] = None
    codebase: typing.Optional[str] = None
    dataset: typing.Optional[str] = None


class BaseMetric(abc.ABC):
    """
    Abstract base class for defining a metric.
    """
    metric_name: str

    def __init__(self):
        """
        Initializes the BaseMetric with default values.
        """
        self.score: float = 0.0
        self.url: str = ""
        self.priority: int = 1
        self.target_platform: typing.Optional[str] = None
        self.local_directory: typing.Optional[str] = None

    def run(self) -> typing.Self:
        """
        Sets up resources and calculates the metric score.
        Returns:
            Self: The metric instance with updated score.
        """
        self.setup_resources()
        self.score = self.calculate_score()

        return self

    def set_params(self, priority: int, platform: str) -> typing.Self:
        """
        Sets the priority and target platform for the metric.
        Args:
            priority (int): The priority value (must be > 0).
            platform (str): The target platform.
        Returns:
            Self: The metric instance with updated parameters.
        """
        assert(priority > 0)
        self.priority = priority
        self.target_platform = platform
        
        return self

    def set_url(self, url: str):
        """
        Sets the URL for the metric.
        Args:
            url (str): The URL to set.
        Raises:
            IOError: If the provided URL is invalid.
        """
        if not url:
            raise IOError("The provided URL was invalid") # cli will handle this error if invalid url

        self.url = url

    def set_local_directory(self, local_directory: str):
        if not local_directory:
            raise IOError("The provided local directory was invalid")
        self.local_directory = local_directory

    @abc.abstractmethod
    def setup_resources(self):
        """
        Abstract method to set up necessary resources for the metric.
        Should be implemented by subclasses.
        """
        pass

    @abc.abstractmethod
    def calculate_score(self) -> float:
        """
        Abstract method to calculate the metric score.
        Should be implemented by subclasses.
        Returns:
            float: The calculated score.
        """
        pass


class PriorityFunction(abc.ABC):
    """
    Abstract base class for priority weighting functions.
    """
    @abc.abstractmethod
    def calculate_priority_weight(self, priority: int) -> float:
        """
        Calculates the weight for a given priority.
        Args:
            priority (int): The priority value.
        Returns:
            float: The calculated weight.
        """
        pass


class PFExponentialDecay(PriorityFunction):
    """
    Priority function using exponential decay.
    """
    def __init__(self, base_coefficient: int):
        """
        Initializes the exponential decay function.
        Args:
            base_coefficient (int): The base coefficient (> 1).
        """
        assert(base_coefficient > 1)
        self.base_coefficient: int = base_coefficient

    @typing.override
    def calculate_priority_weight(self, priority: int) -> float:
        """
        Calculates the weight using exponential decay.
        Args:
            priority (int): The priority value.
        Returns:
            float: The calculated weight.
        """
        return self.base_coefficient ** -(priority - 1)


class PFReciprocal(PriorityFunction):
    """
    Priority function using reciprocal weighting.
    """

    @typing.override
    def calculate_priority_weight(self, priority: int) -> float:
        """
        Calculates the weight as the reciprocal of the priority.
        Args:
            priority (int): The priority value.
        Returns:
            float: The calculated weight.
        """
        return 1 / priority


PRIORITY_FUNCTIONS: dict[str, typing.Type[PriorityFunction]] = {
    'PFExponentialDecay': PFExponentialDecay,
    'PFReciprocal': PFReciprocal
}


class NetScoreCalculator:
    """
    Calculates the net score for a set of metrics using a priority function.
    """
    def __init__(self, priority_function: typing.Type[PriorityFunction]):
        """
        Initializes the NetScoreCalculator.
        Args:
            priority_function (Type[PriorityFunction]): The priority function class to use.
        """
        self.priority_function: typing.Type[PriorityFunction] = priority_function

    def calculate_net_score(self, metrics: list[BaseMetric]):
        """
        Calculates the net score for a list of metrics.
        Args:
            metrics (list[BaseMetric]): The list of metric instances.
        Returns:
            float: The calculated net score.
        """
        num_metrics: int = len(metrics)

        priority_organized_scores: SortedDict = self.generate_scores_priority_dict(metrics) # sorted dict holds [int, list[float]]
        compressed_scores: list[list[float]] = self.compress_priorities(priority_organized_scores)
        priority_weights: list[float] = self.get_priority_weights(compressed_scores, num_metrics)
        aggregated_scores: list[float] = [self.sum_scores(scores) for scores in compressed_scores]

        net_score: float = sum(
            list(
                starmap(lambda score, weight: score * weight, zip(aggregated_scores, priority_weights))
            )
        )

        return net_score

    def generate_scores_priority_dict(self, metrics: list[BaseMetric]) -> SortedDict:
        """
        Organizes metric scores by their priority.
        Args:
            metrics (list[BaseMetric]): The list of metric instances.
        Returns:
            SortedDict[int, list[float]]: Scores organized by priority.
        """
        priority_organized_scores: SortedDict = SortedDict()
        for metric in metrics:
            assert(metric.score >= 0 and metric.score <= 1)
            if metric.priority in priority_organized_scores:
                priority_organized_scores[metric.priority].append(metric.score)
            else:
                priority_organized_scores[metric.priority] = [metric.score]

        return priority_organized_scores

    def sum_scores(self, scores: list[float]) -> float:
        """
        Sums the scores, normalizing by the number of scores.
        Args:
            scores (list[float]): The list of scores.
        Returns:
            float: The summed score.
        """
        scores: list[float] = [score / len(scores) for score in scores]
        return sum(scores)

    def compress_priorities(self, priority_organized_scores: SortedDict) -> list[list[float]]:
        """
        Compresses priorities to remove gaps and outputs a list where the index corresponds to the priority.
        Args:
            priority_organized_scores (SortedDict[int, list[float]]): Scores organized by priority.
        Returns:
            list[list[float]]: Compressed list of scores by priority.
        """
        scores: list[list[float]] = []

        for value in priority_organized_scores.values():
            scores.append(value)

        return scores

    def get_priority_weights(self, compressed_scores: list[list[float]], total_size: int) -> list[float]:
        """
        Calculates normalized weights for each priority group.
        Args:
            compressed_scores (list[list[float]]): Compressed scores by priority.
            total_size (int): Total number of metrics.
        Returns:
            list[float]: Normalized priority weights.
        """
        priority_proportions: list[float] = []

        for priority, scores in enumerate(compressed_scores):
            priority_weight: float = self.priority_function.calculate_priority_weight(priority + 1)
            priority_proportions.append(priority_weight * len(scores) / total_size)

        normalized_weights: list[float] = list(map(lambda x: x / sum(priority_proportions), priority_proportions))

        return normalized_weights


class AnalyzerOutput:
    """
    Stores the output of an analysis, including individual metric scores, model metadata, and the net score.
    """
    def __init__(self, priority_function: typing.Type[PriorityFunction], metrics: list[BaseMetric], model_metadata: ModelURLs):
        """
        Initializes the AnalyzerOutput.
        Args:
            priority_function (Type[PriorityFunction]): The priority function class used.
            metrics (list[BaseMetric]): The list of metric instances.
            model_metadata (ModelURLs): Metadata for the model.
        """
        self.individual_scores: dict[str, float] = {metric.metric_name: metric.score for metric in metrics}
        self.model_metadata: ModelURLs = model_metadata
        self.score: float = NetScoreCalculator(priority_function).calculate_net_score(metrics)

    def __str__(self):
        """
        Returns a string representation of the analysis output.
        Returns:
            str: The string representation.
        """
        return ""

