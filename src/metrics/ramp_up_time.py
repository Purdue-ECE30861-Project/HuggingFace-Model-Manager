import os
import re
from io import StringIO
from typing import override
from pylint.lint import pylinter, Run
from pylint.reporters.text import TextReporter
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from metric import BaseMetric


class RampUpMetric(BaseMetric):
    metric_name: str = "RampUpTime"
    def __init__(self):
        super().__init__()

    @override
    def setup_resources(self):
        pass

    @override
    def calculate_score(self) -> float:
        start_load_time = time.time()
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
        end_load_time = time.time()
        load_time = end_load_time - start_load_time

        start_warmup_time = time.time()
        _ = model.generate(**inputs, max_new_tokens=10, num_return_sequences=1)
        end_warmup_time = time.time()
        warmup_time = end_warmup_time - start_warmup_time

        total_time = load_time + warmup_time
        minutes = total_time / 60

        if minutes <= 1:
            return 1.0
        return 1.0 / minutes