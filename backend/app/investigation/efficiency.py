"""RingGuard AI — Sliced Investigation Efficiency Service.

Stage 15: Investigation Efficiency + Business Impact.
Loads, parses, and provides access to persisted Stage 15 evaluation metrics:
- ml/data/evaluation/investigation_efficiency.json

Reports sliced uncertainty reduction, step compression, simulated tool cost,
and stopping reason distributions across:
1. Overall
2. Ring Fraud
3. Hard Negatives
4. Cold Start
5. Mature
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from app.investigation.schemas import (
    InvestigationEfficiencyResponse,
    InvestigationEfficiencySlice,
)


class InvestigationEfficiencyService:
    """Service to load and serve persisted Stage 15 efficiency results."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]
            self.data_dir = repo_root / "ml" / "data" / "evaluation"

        self.efficiency_file = self.data_dir / "investigation_efficiency.json"

    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """Load and return investigation efficiency metrics or status='Unavailable'."""
        if not self.efficiency_file.exists():
            return {
                "status": "Unavailable",
                "message": "Investigation efficiency artifact not found. Please run scripts/run_stage15_evaluation.py first.",
                "metadata": {},
                "slices": {},
                "workflow_compression_summary": {},
                "disclaimer": "Investigation efficiency metrics are derived from deterministic playback across verified evaluation slices.",
            }

        try:
            with open(self.efficiency_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["status"] = "Available"
            return data
        except Exception as e:
            return {
                "status": "Unavailable",
                "message": f"Error loading investigation efficiency artifact: {str(e)}",
                "metadata": {},
                "slices": {},
                "workflow_compression_summary": {},
                "disclaimer": "Investigation efficiency metrics are derived from deterministic playback across verified evaluation slices.",
            }
