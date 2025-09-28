import unittest
from metrics.code_quality import *
from metric import ModelPaths
from pathlib import Path


class TestCodeQuality(unittest.TestCase):
    def test_score_calculation(self):
        metric: CodeQualityMetric = CodeQualityMetric()
        dirs = ModelPaths(codebase=Path(os.path.dirname(os.path.abspath(__file__))))
        metric.set_local_directory(dirs)
        metric: CodeQualityMetric = metric.run()
        self.assertIsInstance(metric.score, float)
        if isinstance(metric.score, dict):
            return
        score: float = metric.score
        self.assertGreater(score, 0.0)

    def test_no_python(self):
        metric: CodeQualityMetric = CodeQualityMetric()
        dirs = ModelPaths(
            codebase=Path(os.path.dirname(os.path.abspath(__file__))) / "/dummy_bad_dir"
        )
        metric.set_local_directory(dirs)
        metric: CodeQualityMetric = metric.run()
        self.assertIsInstance(metric.score, float)
        if isinstance(metric.score, dict):
            return
        score: float = metric.score
        self.assertAlmostEqual(score, 0.0)
