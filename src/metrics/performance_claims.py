from metric import BaseMetric  # pyright: ignore[reportMissingTypeStubs]
from pathlib import Path
import re
import json
from typing import override
import time


class PerformanceClaimsMetric(BaseMetric):
    metric_name: str = "performance_claims"
    
    def __init__(self):
        super().__init__()
        self.model_name: str = ""
        self.readme_content: str = ""

    @override
    def setup_resources(self):
        #read from readme
        
    @override    
    def calculate_score(self) -> float:
        score = 0.0
        readme_lower = self.readme_content.lower()
        
        benchmark_start = time.time()
        benchmark_keywords = [
                'benchmark', 'evaluation', 'performance', 'accuracy', 'f1', 
                'bleu', 'rouge', 'perplexity', 'score', 'metric', 'eval',
                'test', 'validation', 'leaderboard', 'sota', 'baseline',
                'glue', 'squad', 'superglue', 'hellaswag'
            ]
        benchmark_score = 0.0
        for keyword in benchmark_keywords:
                if keyword in readme_lower:
                    benchmark_score += 0.025  # Each keyword adds points
        benchmark_score = min(0.4, benchmark_score)
        benchmark_end = time.time()
        benchmark_time = benchmark_end - benchmark_start
        
        numeric_start = time.time()
        number_patterns = [
                r'\b\d{1,2}\.\d{1,3}%',      # 85.7%
                r'\b0\.\d{2,3}\b',           # 0.85 (F1 scores, etc.)
                r'\b[5-9]\d\.\d%',           # 85.5% (accuracy)
                r'\b\d{1,2}\.\d{1,2}\s*(?:bleu|rouge|f1)', # 42.1 BLEU
        ]
        numeric_results = []
        for pattern in number_patterns:
            matches = re.findall(pattern, self.readme_content, re.IGNORECASE)
            numeric_results.extend(matches)
        
        numeric_score = 0.0
        if len(numeric_results) >= 5:
            numeric_score = 0.3
        elif len(numeric_results) >= 3:
            numeric_score = 0.2
        elif len(numeric_results) >= 1:
            numeric_score = 0.1
        numeric_end = time.time()
        numeric_time = numeric_end - numeric_start
        
        academic_start = time.time()
        academic_patterns = [
            r'arxiv\.org/\w+/\d+\.\d+',     # ArXiv links
            r'doi\.org/\w+',                 # DOI links  
            r'proceedings\s+of\s+\w+',      # Conference proceedings
            r'published\s+in\s+\w+',        # Published in X
            r'cite\s+as:|citation:', # Citation sections
        ]
        
        academic_keywords = [
            'paper', 'arxiv', 'doi:', 'citation', 'published', 
            'conference', 'journal', 'acl', 'emnlp', 'icml',
            'neurips', 'iclr', 'naacl', 'aaai'
        ]
        
        academic_score = 0.0
        for pattern in academic_patterns:
            if re.search(pattern, self.readme_content, re.IGNORECASE):
                academic_score = 0.2
                break
        
        if academic_score == 0.0:
            for keyword in academic_keywords:
                if keyword in readme_lower:
                    academic_score = 0.1
                    break
        
        academic_end = time.time()
        academic_time = academic_end - academic_start
    
        dataset_start = time.time()
        dataset_keywords = [
            'dataset', 'corpus', 'test set', 'validation set', 
            'evaluated on', 'tested on', 'benchmarked on',
            'common crawl', 'wikipedia', 'bookcorpus', 'pile'
        ]
        dataset_score = 0.0
        for keyword in dataset_keywords:
            if keyword in readme_lower:
                dataset_score = 0.1
                break
        dataset_end = time.time()
        dataset_time = dataset_end - dataset_start
        
        total_score = benchmark_score + numeric_score + academic_score + dataset_score
        total_analysis_time = benchmark_time + numeric_time + academic_time + dataset_time
        
        final_score = min(1.0, max(0.0, total_score))
        
        return final_score