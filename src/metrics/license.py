from metric import BaseMetric
from typing import Self, override

class LicenseMetric(BaseMetric):
    def __init__(self):
        """
        Initializes the BaseMetric with default values.
        """
        self.score: float = 0.0
        self.metric_name = "license"
        self.url: str = ""
        self.priority: int = 1
        self.target_platform: str = ""

    @override
    def run(self) -> Self:
        ...

    