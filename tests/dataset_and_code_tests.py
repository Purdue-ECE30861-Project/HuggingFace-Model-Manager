import unittest
from src.metrics.dataset_and_code import *


class TestDatasetAndCodeScoreMetric(unittest.TestCase):
    metric: DatasetAndCodeScoreMetric

    def setUp(self):
        self.metric = DatasetAndCodeScoreMetric()
        self.metric.dataset_url = "https://huggingface.co/datasets/test-dataset"
        self.metric.code_url = "https://github.com/test/repo"

    def test_score_calculation_no_resources(self):
        """
        Test score calculation when no URLs or documentation available
        """
        self.metric.dataset_url = None
        self.metric.code_url = None

        self.metric.readme_file = type(
            "MockPath", (), {"read_text": lambda: ""}  # Empty README
        )()

        score = self.metric.calculate_score()
        self.assertEqual(score, 0.0)

    def test_score_calculation_full_documentation(self):
        """
        Test score calculation with README documentation
        """
        self.metric.dataset_url = None
        self.metric.code_url = None

        # Mock README content
        readme = """
        # Model Documentation
        
        This model uses a comprehensive dataset with detailed data description.
        
        ## Usage
        Here's how to use this model effectively.
        
        ## Example
        Sample usage and code examples.
        
        ## Requirements
        Installation and dependency requirements.
        
        ## Limitations
        Known limitations and constraints.
        """.lower()

        self.metric.readme_file = type("MockPath", (), {"read_text": lambda: readme})()

        score = self.metric.calculate_score()

        # Should get full documentation score
        expected_score = 0.2
        self.assertAlmostEqual(score, expected_score, places=1)

    def test_score_calculation_working_urls(self):
        """
        Test score calculation when URLs are accessible
        """
        self.metric.dataset_url = "https://working-dataset.com"
        self.metric.code_url = "https://working-code.com"

        # Mock empty README
        self.metric.readme_file = type("MockPath", (), {"read_text": lambda: ""})()

        score = self.metric.calculate_score()

        # Should get full score for working URLs
        expected_score = 0.6
        self.assertAlmostEqual(score, expected_score, places=1)

    def test_documentation_scoring_logic(self):
        """Test the specific documentation scoring algorithm"""
        self.metric.dataset_url = None
        self.metric.code_url = None

        # Test cases with different documentation levels
        test_cases = [
            ("", 0.0),
            ("dataset", 0.04),
            ("dataset usage", 0.08),
            ("dataset data description usage how to use", 0.08),
            ("dataset usage example requirements limitations", 0.2),
        ]

        for readme_content, expected_doc_score in test_cases:
            self.metric.readme_file = type(
                "MockPath", (), {"read_text": lambda content=readme_content: content}
            )()

            score = self.metric.calculate_score()
            self.assertAlmostEqual(score, expected_doc_score, places=1)
