import unittest
import tempfile
import shutil
from pathlib import Path

from huggingface_hub import snapshot_download
from src.metrics.code_quality import CodeQualityMetric


class TestCodeQualityMetricWithHuggingFaceModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a shared temporary workspace for this test class
        cls._class_tmp = tempfile.TemporaryDirectory()
        cls.workspace = Path(cls._class_tmp.name)

        # Create a codebase dir where we’ll place the downloaded model (acts as "repo")
        cls.codebase_dir = cls.workspace / "codebase"
        cls.codebase_dir.mkdir(parents=True, exist_ok=True)

        # Download a very small Hugging Face model into the codebase directory
        # Using a tiny config-only repo to minimize size and time
        # You can swap this with any small public model if desired.
        cls.model_local_dir = cls.codebase_dir / "sshleifer_tiny-distilroberta-base"
        if not cls.model_local_dir.exists():
            snapshot_download(
                repo_id="sshleifer/tiny-distilroberta-base",
                local_dir=str(cls.model_local_dir),
                revision="main",
            )

        # Add minimal ancillary files that typical code quality checks might expect
        (cls.codebase_dir / "README.md").write_text("# Tiny Model Repo\n\nAuto-downloaded for testing.\n")
        (cls.codebase_dir / "pyproject.toml").write_text("[tool]\nname='tiny'\n")

    @classmethod
    def tearDownClass(cls):
        cls._class_tmp.cleanup()

    def setUp(self):
        # Fresh metric instance per test; preserve existing test style
        self.metric = CodeQualityMetric()

    def tearDown(self):
        pass

    def test_metric_runs_on_downloaded_model_directory(self):
        # Point metric at our prepared directory with a downloaded HF model
        self.metric.set_local_directory(str(self.codebase_dir))
        result = self.metric.run()
        self.assertIsInstance(result.score, float)
        self.assertGreaterEqual(result.score, 0.0)
        self.assertLessEqual(result.score, 1.0)

    def test_metric_handles_no_valid_file(self):
        # Create an empty temp directory with no valid files
        empty_tmp = tempfile.TemporaryDirectory()
        try:
            empty_path = Path(empty_tmp.name)
            self.metric.set_local_directory(str(empty_path))
            result = self.metric.run()
            self.assertIsInstance(result.score, float)
            # Expect a low score when no valid files are present
            self.assertLessEqual(result.score, 0.5)
        finally:
            empty_tmp.cleanup()


if __name__ == "__main__":
    unittest.main()