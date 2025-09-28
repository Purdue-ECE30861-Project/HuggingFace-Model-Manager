import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from huggingface_hub import snapshot_download
import git
from src.metric import ModelURLs


class DownloadManager:
    def __init__(self, models_dir: str = "models", codebases_dir: str = "codebases", datasets_dir: str = "datasets"):
        """
        Args:
            models_dir: Directory to store downloaded models
            codebases_dir: Directory to store downloaded codebases
            datasets_dir: Directory to store downloaded datasetsS
        """
        self.models_dir = Path(models_dir)
        self.codebases_dir = Path(codebases_dir)
        self.datasets_dir = Path(datasets_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.codebases_dir.mkdir(exist_ok=True)
        self.datasets_dir.mkdir(exist_ok=True)

    def _extract_repo_id(self, model_url: str) -> str:
        """
        Args:
            model_url: HuggingFace model URL
            
        Returns:
            Repository ID (e.g., "username/model-name")
        """
        # Remove common URL patterns
        repo_id = model_url.replace("https://huggingface.co/", "")
        repo_id = repo_id.replace("/tree/main", "")
        repo_id = repo_id.rstrip("/")
        return repo_id
    
    def _extract_dataset_repo_id(self, dataset_url: str) ->str:
        """
        Args:
            dataset_url: HuggingFace dataset URL
            
        Returns:
            Dataset repository ID (e.g., "username/dataset-name")
        """
        # Remove common URL patterns for datasets
        repo_id = dataset_url.replace("https://huggingface.co/datasets/", "")
        repo_id = repo_id.replace("/tree/main", "")
        repo_id = repo_id.rstrip("/")
        return repo_id

    def _extract_repo_name(self, code_url: str) -> str:
        """
        Args:
            code_url: Git repository URL
            
        Returns:
            Repository name
        """
        repo_name = code_url.rstrip('/').split('/')[-1]
        repo_name = repo_name.replace('.git', '')
        return repo_name

    def download_model(self, model_url: str) -> Path:
        """
        Args:
            model_url: HuggingFace model URL
            
        Returns:
            Path to the downloaded model directory
        """
        repo_id = self._extract_repo_id(model_url)
        local_path = self.models_dir / repo_id.replace("/", "_")
        
        if local_path.exists():
            logging.info(f"Model already exists at {local_path}")
            return local_path
        
        logging.info(f"Downloading model from {model_url}...")
        try:
            snapshot_download(
                repo_id=repo_id,
                local_dir=str(local_path),
                revision="main"
            )
            logging.info(f"Model downloaded to {local_path}")
            return local_path
        except Exception as e:
            logging.error(f"Failed to download model from {model_url}: {e}")
            raise

    def download_dataset(self, dataset_url: str) -> Path:
        """
        Args:
            dataset_url: HuggingFace dataset URL
            
        Returns:
            Path to the downloaded dataset directory
        """
        repo_id = self._extract_dataset_repo_id(dataset_url)
        local_path = self.datasets_dir / repo_id.replace("/", "_")
        
        if local_path.exists():
            logging.info(f"Dataset already exists at {local_path}")
            return local_path
        
        logging.info(f"Downloading dataset from {dataset_url}...")
        try:
            snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",  # Important: specify repo_type for datasets
                local_dir=str(local_path),
                revision="main"
            )
            logging.info(f"Dataset downloaded to {local_path}")
            return local_path
        except Exception as e:
            logging.error(f"Failed to download dataset from {dataset_url}: {e}")
            raise

    def download_codebase(self, code_url: str) -> Path:
        """
        Args:
            code_url: Git repository URL
            
        Returns:
            Path to the downloaded codebase directory
        """
        repo_name = self._extract_repo_name(code_url)
        local_path = self.codebases_dir / repo_name
        
        if local_path.exists():
            logging.info(f"Codebase already exists at {local_path}, pulling latest changes...")
            try:
                repo = git.Repo(local_path)
                repo.remotes.origin.pull()
                logging.info(f"Codebase updated at {local_path}")
            except Exception as e:
                logging.warning(f"Could not pull latest changes: {e}")
            return local_path
        
        logging.info(f"Cloning codebase from {code_url}...")
        try:
            git.Repo.clone_from(code_url, local_path)
            logging.info(f"Codebase cloned to {local_path}")
            return local_path
        except Exception as e:
            logging.error(f"Failed to clone codebase from {code_url}: {e}")
            raise

    def check_local_model(self, model_url: str) -> Optional[Path]:
        """
        Args:
            model_url: HuggingFace model URL
            
        Returns:
            Path to model if exists, None otherwise
        """
        repo_id = self._extract_repo_id(model_url)
        local_path = self.models_dir / repo_id.replace("/", "_")
        
        if local_path.exists():
            return local_path
        return None

    def check_local_codebase(self, code_url: str) -> Optional[Path]:
        """
        Args:
            code_url: Git repository URL
            
        Returns:
            Path to codebase if exists, None otherwise
        """
        repo_name = self._extract_repo_name(code_url)
        local_path = self.codebases_dir / repo_name
        
        if local_path.exists():
            return local_path
        return None

    def download_model_resources(
        self, 
        model_urls: ModelURLs,
        download_model: bool = True,
        download_codebase: bool = True,
        download_dataset: bool = True
    ) -> Tuple[Optional[Path], Optional[Path], Optional[Path]]:
        """
        Args:
            model_urls: ModelURLs object containing URLs
            download_model: Whether to download the model
            download_codebase: Whether to download the codebase
            download_dataset: Whether to download the dataset
            
        Returns:
            Tuple of (model_path, codebase_path, dataset_path)
        """
        model_path = None
        codebase_path = None
        dataset_path = None
        
        # Download model if requested and URL exists
        if download_model and model_urls.model:
            # Check if already downloaded
            model_path = self.check_local_model(model_urls.model)
            if not model_path:
                model_path = self.download_model(model_urls.model)
            
        # Download codebase if requested and URL exists
        if download_codebase and model_urls.codebase:
            # Check if already downloaded
            codebase_path = self.check_local_codebase(model_urls.codebase)
            if not codebase_path:
                codebase_path = self.download_codebase(model_urls.codebase)

        # Download dataset if requested and URL exists
        if download_dataset and model_urls.dataset:
            # Check if already downloaded
            dataset_path = self.check_local_model(model_urls.dataset)
            if not dataset_path:
                dataset_path = self.download_dataset(model_urls.dataset)
        
        return model_path, codebase_path, dataset_path
