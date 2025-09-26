import typing
import time
from io import StringIO
from math import exp, log
from typing import override, Literal

import contextlib
from transformers import AutoTokenizer, AutoModel

from metric import BaseMetric


class RampUpMetric(BaseMetric):
    metric_name: str = "RampUpTime"

    def __init__(
        self,
        half_score_time_minutes: float,
        device_type: Literal["cpu", "mps", "cuda", "cuda:0"],
    ):
        super().__init__()
        assert half_score_time_minutes > 0.0
        self.device_type: Literal["cpu", "mps", "cuda", "cuda:0"] = device_type
        self.exponential_coefficient: float = -log(0.5) / half_score_time_minutes
        self.model_name: str = ""

    @override
    def setup_resources(self):
        try:
            split_url = self.url.split("huggingface.co/")
            self.model_name = split_url[1]
        except Exception:
            raise NameError(
                f"URL provided to RampUpMetric {self.url} is of invalid format"
            )

    def installation_spin_up_score(self, force_download: bool):
        start_load_time: float = time.time()
        buf: StringIO = StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            tokenizer: typing.Any = AutoTokenizer.from_pretrained(
                self.model_name, force_download=force_download
            )
            model: typing.Any = AutoModel.from_pretrained(
                self.model_name, force_download=force_download
            ).to(self.device_type)

            total_time: float = time.time() - start_load_time

        return exp(-self.exponential_coefficient * (total_time / 60))

    @override
    def calculate_score(self) -> float:
        try:
            initial_install: float = self.installation_spin_up_score(True)
            cache_install: float = self.installation_spin_up_score(False)

            return (initial_install + cache_install) / 2
        except ValueError:
            print("No URL access to specified model")
            return 0.0
