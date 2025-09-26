import unittest
from metrics.code_quality import *


class TestCodeQuality(unittest.TestCase):
    def test_score_calculation(self):
        metric: CodeQualityMetric = CodeQualityMetric()
        metric.local_directory = os.path.dirname(os.path.abspath(__file__))
        metric: CodeQualityMetric = metric.run()
        score: float = metric.score
        self.assertGreater(score, 0.0)

    def test_no_python(self):
        metric: CodeQualityMetric = CodeQualityMetric()
        metric.local_directory = os.path.dirname(os.path.abspath(__file__)) + "/dummy_bad_dir"
        metric: CodeQualityMetric = metric.run()
        score: float = metric.score
        self.assertAlmostEqual(score, 0.0)