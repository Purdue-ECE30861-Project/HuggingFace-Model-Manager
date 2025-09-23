from metric import BaseMetric
import re
from typing import override
from pathlib import Path


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

        readme_content = self.readme_file.read_text(encoding="utf-8").lower()

        # Benchmark keywords
        benchmark_keywords = [
            "benchmark",
            "evaluation",
            "performance",
            "accuracy",
            "f1",
            "bleu",
            "rouge",
            "perplexity",
            "score",
            "metric",
            "eval",
            "test",
            "validation",
            "leaderboard",
            "sota",
            "baseline",
        ]
        benchmark_score = 0.0
        for keyword in benchmark_keywords:
            if keyword in readme_content:
                benchmark_score += 0.03
        benchmark_score = min(0.4, benchmark_score)

        # Numerical results
        numbers = re.findall(r"\b\d+\.?\d*%?\b", self.readme_content)
        numeric_results = []
        for num in numbers:
            try:
                clean_num = num.replace("%", "")
                val = float(clean_num)
                # Filter for likely performance scores
                if (
                    ("%" in num and 0 <= val <= 100)
                    or ("." in num and 0 <= val <= 1)
                    or (not "%" in num and not "." in num and 50 <= val <= 100)
                ):
                    numeric_results.append(num)
            except ValueError:
                continue

        numeric_score = 0.0
        if len(numeric_results) >= 5:
            numeric_score = 0.3
        elif len(numeric_results) >= 3:
            numeric_score = 0.2
        elif len(numeric_results) >= 1:
            numeric_score = 0.1

        # Academic references
        paper_indicators = [
            "paper",
            "arxiv",
            "doi:",
            "citation",
            "published",
            "conference",
            "journal",
            "acl",
            "emnlp",
            "icml",
        ]
        academic_score = 0.0
        for indicator in paper_indicators:
            if indicator in readme_content:
                academic_score = 0.2
                break

        # Dataset evaluation
        dataset_keywords = [
            "dataset",
            "corpus",
            "test set",
            "validation set",
            "eval",
            "glue",
            "squad",
            "coco",
        ]
        dataset_score = 0.0
        for keyword in dataset_keywords:
            if keyword in readme_content:
                dataset_score = 0.1
                break

        # Calculate total score and time
        total_score = benchmark_score + numeric_score + academic_score + dataset_score

        # Normalize score
        final_score = min(1.0, max(0.0, total_score))

        return final_score
