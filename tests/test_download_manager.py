import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import tempfile
import shutil
import sys

from src.download_manager import DownloadManager
from src.metric import ModelURLs


class TestDownloadManager(unittest.TestCase):
    """Test DownloadManager in isolation using mocks"""

    def setUp(self):
        """Set up test fixtures before each test"""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.models_dir = Path(self.test_dir) / "models"
        self.codebases_dir = Path(self.test_dir) / "codebases"
        
        self.dm = DownloadManager(
            models_dir=str(self.models_dir),
            codebases_dir=str(self.codebases_dir)
        )

    def tearDown(self):
        """Clean up after each test"""
        shutil.rmtree(self.test_dir)

    def test_init_creates_directories(self):
        """Test that __init__ creates model and codebase directories"""
        self.assertTrue(self.models_dir.exists())
        self.assertTrue(self.codebases_dir.exists())

    def test_extract_repo_id_standard_url(self):
        """Test extracting repo ID from standard HuggingFace URL"""
        url = "https://huggingface.co/bert-base-uncased"
        result = self.dm._extract_repo_id(url)
        self.assertEqual(result, "bert-base-uncased")

    def test_extract_repo_id_with_tree_main(self):
        """Test extracting repo ID from URL with /tree/main"""
        url = "https://huggingface.co/username/model-name/tree/main"
        result = self.dm._extract_repo_id(url)
        self.assertEqual(result, "username/model-name")

    def test_extract_repo_id_with_trailing_slash(self):
        """Test extracting repo ID with trailing slash"""
        url = "https://huggingface.co/username/model/"
        result = self.dm._extract_repo_id(url)
        self.assertEqual(result, "username/model")

    def test_extract_repo_name_standard_github_url(self):
        """Test extracting repo name from GitHub URL"""
        url = "https://github.com/username/repo-name"
        result = self.dm._extract_repo_name(url)
        self.assertEqual(result, "repo-name")

    def test_extract_repo_name_with_git_extension(self):
        """Test extracting repo name with .git extension"""
        url = "https://github.com/username/repo-name.git"
        result = self.dm._extract_repo_name(url)
        self.assertEqual(result, "repo-name")

    def test_extract_repo_name_with_trailing_slash(self):
        """Test extracting repo name with trailing slash"""
        url = "https://github.com/username/repo-name/"
        result = self.dm._extract_repo_name(url)
        self.assertEqual(result, "repo-name")

    @patch('download_manager.snapshot_download')
    def test_download_model_success(self, mock_snapshot):
        """Test successful model download"""
        model_url = "https://huggingface.co/bert-base-uncased"
        
        result = self.dm.download_model(model_url)
        
        # Check snapshot_download was called correctly
        mock_snapshot.assert_called_once_with(
            repo_id="bert-base-uncased",
            local_dir=str(self.models_dir / "bert-base-uncased"),
            revision="main"
        )
        
        # Check return value
        self.assertEqual(result, self.models_dir / "bert-base-uncased")

    @patch('download_manager.snapshot_download')
    def test_download_model_already_exists(self, mock_snapshot):
        """Test that existing model is not re-downloaded"""
        model_url = "https://huggingface.co/bert-base-uncased"
        local_path = self.models_dir / "bert-base-uncased"
        local_path.mkdir(parents=True)
        
        result = self.dm.download_model(model_url)
        
        # Should NOT call snapshot_download
        mock_snapshot.assert_not_called()
        
        # Should return existing path
        self.assertEqual(result, local_path)

    @patch('download_manager.snapshot_download')
    def test_download_model_failure(self, mock_snapshot):
        """Test model download failure handling"""
        model_url = "https://huggingface.co/nonexistent/model"
        mock_snapshot.side_effect = Exception("Download failed")
        
        with self.assertRaises(Exception) as context:
            self.dm.download_model(model_url)
        
        self.assertIn("Download failed", str(context.exception))

    @patch('download_manager.git.Repo')
    def test_download_codebase_success(self, mock_repo_class):
        """Test successful codebase clone"""
        code_url = "https://github.com/username/repo"
        
        result = self.dm.download_codebase(code_url)
        
        # Check clone_from was called correctly
        mock_repo_class.clone_from.assert_called_once_with(
            code_url,
            self.codebases_dir / "repo"
        )
        
        # Check return value
        self.assertEqual(result, self.codebases_dir / "repo")

    @patch('download_manager.git.Repo')
    def test_download_codebase_already_exists(self, mock_repo_class):
        """Test that existing codebase is updated (pulled)"""
        code_url = "https://github.com/username/repo"
        local_path = self.codebases_dir / "repo"
        local_path.mkdir(parents=True)
        
        # Mock the repo instance
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        
        result = self.dm.download_codebase(code_url)
        
        # Should call Repo() to open existing repo
        mock_repo_class.assert_called_once_with(local_path)
        
        # Should pull latest changes
        mock_repo_instance.remotes.origin.pull.assert_called_once()
        
        # Should NOT call clone_from
        mock_repo_class.clone_from.assert_not_called()
        
        self.assertEqual(result, local_path)

    @patch('download_manager.git.Repo')
    def test_download_codebase_pull_failure(self, mock_repo_class):
        """Test that pull failure is handled gracefully"""
        code_url = "https://github.com/username/repo"
        local_path = self.codebases_dir / "repo"
        local_path.mkdir(parents=True)
        
        mock_repo_instance = MagicMock()
        mock_repo_instance.remotes.origin.pull.side_effect = Exception("Pull failed")
        mock_repo_class.return_value = mock_repo_instance
        
        # Should not raise, just log warning
        result = self.dm.download_codebase(code_url)
        
        self.assertEqual(result, local_path)

    @patch('download_manager.git.Repo')
    def test_download_codebase_clone_failure(self, mock_repo_class):
        """Test codebase clone failure handling"""
        code_url = "https://github.com/username/repo"
        mock_repo_class.clone_from.side_effect = Exception("Clone failed")
        
        with self.assertRaises(Exception) as context:
            self.dm.download_codebase(code_url)
        
        self.assertIn("Clone failed", str(context.exception))

    def test_check_local_model_exists(self):
        """Test checking for existing local model"""
        model_url = "https://huggingface.co/bert-base-uncased"
        local_path = self.models_dir / "bert-base-uncased"
        local_path.mkdir(parents=True)
        
        result = self.dm.check_local_model(model_url)
        
        self.assertEqual(result, local_path)

    def test_check_local_model_not_exists(self):
        """Test checking for non-existent local model"""
        model_url = "https://huggingface.co/bert-base-uncased"
        
        result = self.dm.check_local_model(model_url)
        
        self.assertIsNone(result)

    def test_check_local_codebase_exists(self):
        """Test checking for existing local codebase"""
        code_url = "https://github.com/username/repo"
        local_path = self.codebases_dir / "repo"
        local_path.mkdir(parents=True)
        
        result = self.dm.check_local_codebase(code_url)
        
        self.assertEqual(result, local_path)

    def test_check_local_codebase_not_exists(self):
        """Test checking for non-existent local codebase"""
        code_url = "https://github.com/username/repo"
        
        result = self.dm.check_local_codebase(code_url)
        
        self.assertIsNone(result)

    @patch('download_manager.snapshot_download')
    @patch('download_manager.git.Repo')
    def test_download_model_resources_both(self, mock_git, mock_snapshot):
        """Test downloading both model and codebase"""
        model_urls = ModelURLs(
            model="https://huggingface.co/bert-base-uncased",
            codebase="https://github.com/username/repo",
            dataset=None
        )
        
        model_path, codebase_path = self.dm.download_model_resources(model_urls)
        
        # Check both were attempted
        mock_snapshot.assert_called_once()
        mock_git.clone_from.assert_called_once()
        
        # Check return values
        self.assertEqual(model_path, self.models_dir / "bert-base-uncased")
        self.assertEqual(codebase_path, self.codebases_dir / "repo")

    @patch('download_manager.snapshot_download')
    def test_download_model_resources_model_only(self, mock_snapshot):
        """Test downloading only model (no codebase URL)"""
        model_urls = ModelURLs(
            model="https://huggingface.co/bert-base-uncased",
            codebase=None,
            dataset=None
        )
        
        model_path, codebase_path = self.dm.download_model_resources(model_urls)
        
        # Check model was downloaded
        mock_snapshot.assert_called_once()
        
        # Check return values
        self.assertEqual(model_path, self.models_dir / "bert-base-uncased")
        self.assertIsNone(codebase_path)

    @patch('download_manager.git.Repo')
    def test_download_model_resources_codebase_only(self, mock_git):
        """Test downloading only codebase (no model download)"""
        model_urls = ModelURLs(
            model="https://huggingface.co/bert-base-uncased",
            codebase="https://github.com/username/repo",
            dataset=None
        )
        
        model_path, codebase_path = self.dm.download_model_resources(
            model_urls,
            download_model=False,
            download_codebase=True
        )
        
        # Check codebase was downloaded
        mock_git.clone_from.assert_called_once()
        
        # Check return values
        self.assertIsNone(model_path)
        self.assertEqual(codebase_path, self.codebases_dir / "repo")

    @patch('download_manager.snapshot_download')
    @patch('download_manager.git.Repo')
    def test_download_model_resources_cached(self, mock_git, mock_snapshot):
        """Test that cached resources are not re-downloaded"""
        # Create existing directories
        model_path = self.models_dir / "bert-base-uncased"
        codebase_path = self.codebases_dir / "repo"
        model_path.mkdir(parents=True)
        codebase_path.mkdir(parents=True)
        
        model_urls = ModelURLs(
            model="https://huggingface.co/bert-base-uncased",
            codebase="https://github.com/username/repo",
            dataset=None
        )
        
        result_model, result_codebase = self.dm.download_model_resources(model_urls)
        
        # Should NOT call download functions (files exist)
        mock_snapshot.assert_not_called()
        mock_git.clone_from.assert_not_called()
        
        # Should call git.Repo to update existing codebase
        mock_git.assert_called_once_with(codebase_path)
        
        # Check return values
        self.assertEqual(result_model, model_path)
        self.assertEqual(result_codebase, codebase_path)

    def test_download_model_resources_no_urls(self):
        """Test with no URLs provided"""
        model_urls = ModelURLs(
            model=None,
            codebase=None,
            dataset=None
        )
        
        model_path, codebase_path = self.dm.download_model_resources(model_urls)
        
        self.assertIsNone(model_path)
        self.assertIsNone(codebase_path)


if __name__ == "__main__":
    unittest.main()