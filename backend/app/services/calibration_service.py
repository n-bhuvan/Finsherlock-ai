"""RingGuard AI — Calibration, Threshold & Cold-Start Evaluation Service.

Stage 14: Cold Start + Calibration + Thresholding.
Loads, parses, and provides access to persisted Stage 14 evaluation artifacts:
- ml/data/evaluation/calibration_results.json
- ml/data/evaluation/threshold_optimization.json
- ml/data/evaluation/cold_start_evaluation.json
Returns 'Unavailable' if artifacts are uninitialized (never fabricated metrics).
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class CalibrationEvaluationService:
    """Service to load and serve persisted Stage 14 evaluation results."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]  # backend/app/services -> backend -> repo_root
            self.data_dir = repo_root / "ml" / "data" / "evaluation"

        self.calibration_file = self.data_dir / "calibration_results.json"
        self.threshold_file = self.data_dir / "threshold_optimization.json"
        self.cold_start_file = self.data_dir / "cold_start_evaluation.json"

    def get_calibration_results(self) -> Dict[str, Any]:
        """Load and return calibration results or status='Unavailable'."""
        if not self.calibration_file.exists():
            return {
                "status": "Unavailable",
                "message": "Calibration artifact not found. Please run scripts/run_stage14_evaluation.py first.",
                "data": None,
            }
        try:
            with open(self.calibration_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["status"] = "Available"
            return data
        except Exception as e:
            return {
                "status": "Unavailable",
                "message": f"Error loading calibration artifact: {str(e)}",
                "data": None,
            }

    def get_threshold_policies(self) -> Dict[str, Any]:
        """Load and return threshold optimization results or status='Unavailable'."""
        if not self.threshold_file.exists():
            return {
                "status": "Unavailable",
                "message": "Threshold optimization artifact not found. Please run scripts/run_stage14_evaluation.py first.",
                "data": None,
            }
        try:
            with open(self.threshold_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["status"] = "Available"
            return data
        except Exception as e:
            return {
                "status": "Unavailable",
                "message": f"Error loading threshold optimization artifact: {str(e)}",
                "data": None,
            }

    def get_cold_start_evaluation(self) -> Dict[str, Any]:
        """Load and return cold start evaluation results or status='Unavailable'."""
        if not self.cold_start_file.exists():
            return {
                "status": "Unavailable",
                "message": "Cold start evaluation artifact not found. Please run scripts/run_stage14_evaluation.py first.",
                "data": None,
            }
        try:
            with open(self.cold_start_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["status"] = "Available"
            return data
        except Exception as e:
            return {
                "status": "Unavailable",
                "message": f"Error loading cold start evaluation artifact: {str(e)}",
                "data": None,
            }
