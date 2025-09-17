from metric import BaseMetric

class BusFactorMetric(BaseMetric):
    metric_name: str = "bus_factor"
    def __init__(self):
        super().__init__()

    def calculate_score(self) -> float:
        """
        Abstract method to calculate the metric score.
        Should be implemented by subclasses.
        Returns:
            float: The calculated score.
        """
        ...
