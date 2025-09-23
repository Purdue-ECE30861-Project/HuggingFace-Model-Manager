import unittest
import os
from metrics.code_quality import *


class TestCodeQuality(unittest.TestCase):
    def test_score_calculation(self):
        metric: MetricCodeQuality = MetricCodeQuality()
        metric.local_directory = os.path.dirname(os.path.abspath(__file__))
        metric: MetricCodeQuality = metric.run()
        score: float = metric.score
        self.assertGreater(score, 0.0)

    def test_nopython(self):
        metric: MetricCodeQuality = MetricCodeQuality()
        metric.local_directory = os.path.dirname(os.path.abspath(__file__)) + "../dummy_bad_dir"
        metric: MetricCodeQuality = metric.run()
        score: float = metric.score
        self.assertAlmostEquals(score, 0.0)