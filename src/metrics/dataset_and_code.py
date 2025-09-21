from metric import BaseMetric
from typing import override
import Path
import requests

class DatasetAndCodeScoreMetric(BaseMetric):
    metric_name: str = "dataset_and_code_score"
    model_dir: Path
    readme_file: Path
    
    def __init__(self, dataset_url: str, code_url: str):
        super().__init__()
        self.dataset_url = dataset_url
        self.code_url = code_url
    
    @override
    def setup_resources(self):
        if self.local_directory is None:
            raise ValueError("Local directory not specified")
        self.model_dir = Path(self.local_directory)
        self.readme_file = self.model_dir / "README.md"
    
    @override
    def calculate_score(self) -> float:
        score = 0.0
        
        #Check dataset availability
        try:  
            if self.dataset_url:
                response = requests.head(self.dataset_url)
                if response.status_code == 200:
                    score += 0.3
        except requests.RequestException:
            pass
        
        #Check code availability     
        try:   
            if self.code_url:
                response = requests.head(self.code_url)
                if response.status_code == 200:
                    score += 0.3    
        except requests.RequestException:
            pass 
        
        #Check online documentation
        try:
            if self.dataset_url:
                response = requests.get(self.dataset_url)
                if "dataset description" in response.text.lower():
                    score += 0.2
        except requests.RequestException:
            pass
        
        #Check README for dataset and code info
        readme_content = self.readme_file.read_text().lower()
        documentation_markers = {
            "dataset": ["dataset", "data description", "training data"],
            "usage": ["usage", "how to use", "getting started"],
            "examples": ["example", "sample usage"],
            "requirements": ["requirements", "dependencies", "installation"],
            "limitations": ["limitations", "constraints", "known issues"]
        }
        
        doc_score = 0.0
        for section in documentation_markers.values():
            for marker in section:
                if marker in readme_content:
                    doc_score += 0.2 / len(documentation_markers)
                    
        return min(1, score + doc_score)         
                