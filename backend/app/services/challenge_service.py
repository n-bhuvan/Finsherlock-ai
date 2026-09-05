"""RingGuard AI — Challenge Evaluation Service.

Stage 13: Advanced Evaluation + Hard Negatives.
Loads, parses, and provides access to the persisted hard-negative challenge
evaluation artifacts from ml/data/evaluation/challenge_comparison.json.
Returns 'Unavailable' if artifacts are uninitialized (never fake zeros).
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ChallengeEvaluationService:
    """Service to load and serve persisted challenge benchmark results."""

    def __init__(self, eval_file_path: Optional[Path] = None):
        if eval_file_path:
            self.eval_file_path = Path(eval_file_path)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]  # backend/app/services -> backend -> repo_root
            self.eval_file_path = repo_root / "ml" / "data" / "evaluation" / "challenge_comparison.json"

    def get_challenge_evaluation(self) -> Dict[str, Any]:
        """Load and return persisted challenge evaluation data or status='Unavailable'."""
        if not self.eval_file_path.exists():
            return {
                "status": "Unavailable",
                "message": "Challenge evaluation artifact not found. Please run scripts/evaluate_challenge.py first.",
                "dataset_summary": None,
                "overall_metrics_t_0_70": None,
                "overall_metrics_t_0_50": None,
                "category_slices": None,
                "threshold_sweep": None,
                "disclaimer": "Unavailable",
            }

        try:
            with open(self.eval_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["status"] = "Available"
            return data
        except Exception as e:
            return {
                "status": "Unavailable",
                "message": f"Error loading challenge evaluation artifact: {str(e)}",
                "dataset_summary": None,
                "overall_metrics_t_0_70": None,
                "overall_metrics_t_0_50": None,
                "category_slices": None,
                "threshold_sweep": None,
                "disclaimer": "Unavailable",
            }
