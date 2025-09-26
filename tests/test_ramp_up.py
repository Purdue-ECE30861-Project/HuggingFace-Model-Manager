import unittest
from metrics.ramp_up_time import *


class TestRampUpTime(unittest.TestCase):
    def test_no_url(self):
        metric: RampUpMetric = RampUpMetric(0.25, "cpu") # score is 0.5 at 15 seconds
        metric.model_name = "google-bert/bert-base-uncased"

        score: float = metric.calculate_score()
        print(score)
        self.assertGreater(score, 0.0)

    def test_url(self):
        metric: RampUpMetric = RampUpMetric(0.25, "cpu")
        metric.set_url("https://huggingface.co/google-bert/bert-base-uncased")
        metric.setup_resources()

        self.assertEqual(metric.model_name, "google-bert/bert-base-uncased")
        metric.set_url("nonsense")

        self.assertEqual(metric.run().score, 0.0)

    def test_with_url(self):
        metric: RampUpMetric = RampUpMetric(0.25, "cpu")  # score is 0.5 at 15 seconds
        metric.set_url("https://huggingface.co/google-bert/bert-base-uncased")

        score: float = metric.run().score
        print(score)
        self.assertGreater(score, 0.0)