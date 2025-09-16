from metric import BaseMetric
from typing import Self, override

class BusFactorMetric(BaseMetric):
    def __init__(self):
        """
        Initializes the BaseMetric with default values.
        """
        self.score: float = 0.0
        self.metric_name = "bus_factor"
        self.url: str = ""
        self.priority: int = 2
        self.target_platform: str = ""

    @override
    def run(self) -> Self:
        ...
