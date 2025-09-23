from metric import BaseMetric
import Path
from typing import override
import requests

API_KEY = "sk-c089cffb672740b4b99d38dad7c97677"
LLM_API_URL = "https://genai.rcac.purdue.edu/api/chat/completions"

class PerformanceClaimsMetric(BaseMetric):
    metric_name: str = "performance_claims"
    model_dir: Path
    readme_file: Path
    
    def __init__(self):
        super().__init__()

    @override
    def setup_resources(self):
        if self.local_directory is None:
            raise ValueError("Local directory not specified")
        self.model_dir = Path(self.local_directory)
        self.readme_file = self.model_dir / "README.md"
        
    @override    
    def calculate_score(self) -> float:
        if not self.readme_file.exists():
            return 0.0
        
        readme_content = self.readme_file.read_text(encoding='utf-8').lower()
        
        prompt = """Use the following README content to score the model's performance claims on a scale of 0 to 1. Look for 
        benchmark keywords, numerical results, academic references, and performance comparisons. The benchmark score has a weight 
        of 0.4, numerical results have a weight of 0.3, academic references have a weight of 0.2, and performance comparisions have a 
        weight of 0.1. Output the calculated score as a floating point and nothing else. README content: """ + readme_content
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3.1:latest",
            "prompt": prompt
        }
        
        final_score = requests.post(LLM_API_URL, headers=headers, json=data)
        final_score = float(final_score.json()['choices'][0]['message']['content'].strip())
        return final_score
    