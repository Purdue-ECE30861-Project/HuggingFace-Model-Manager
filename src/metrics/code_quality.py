import os
import re
from io import StringIO
from typing import override
from pylint.lint import pylinter, Run
from pylint.reporters.text import TextReporter

from metric import BaseMetric


class CodeQualityMetric(BaseMetric):
    metric_name: str = "code_quality"

    def __init__(self):
        super().__init__()
        self.file_list: list[str] = []

    @override
    def setup_resources(self):
        for root, _, files in os.walk(self.local_directory.codebase):
            for file in files:
                if file.endswith(".py"):
                    #print(file)
                    self.file_list.append(os.path.join(root, file))

    @override
    def calculate_score(self) -> float:
        if not self.file_list:
            return 0.0

        pylinter.MANAGER.clear_cache()

        output_stream: StringIO = StringIO()
        reporter: TextReporter = TextReporter(output_stream)

        Run(
            ["--disable=line-too-long"] + self.file_list, reporter=reporter, exit=False
        )
        match = re.search(r"rated at ([0-9]+\.[0-9]+)/10", output_stream.getvalue())

        if match is None:
            return 0.0
        return float(match.group(1)) / 10
