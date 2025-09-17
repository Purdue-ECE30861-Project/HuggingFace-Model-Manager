from io import StringIO
from typing import override
from pylint import run_pylint, run_pyreverse, run_symilar
from pylint.lint import pylinter, Run
from pylint.reporters.json_reporter import JSONReporter
from pylint.reporters.text import TextReporter


from metric import BaseMetric

output_stream = StringIO()
reporter = TextReporter(output_stream)
pylinter.MANAGER.clear_cache()
Run(["--disable=line-too- long", "/home/malinkyzubr/Desktop/ECE30861/Fun-ECE-Project/src/metric.py", "/home/malinkyzubr/Desktop/ECE30861/Fun-ECE-Project/src/workflow.py"], reporter=reporter, exit=False)
print(output_stream.getvalue())


class MetricCodeQuality(BaseMetric):
    def __init__(self):
        super().__init__()

    @override
    def setup_resources(self):
        pass
