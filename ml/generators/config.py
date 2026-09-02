"""RingGuard AI — Synthetic Data Generator Configuration.

Stage 2: Synthetic Data Engine.
Provides configuration dataclasses and validation thresholds for deterministic,
reproducible synthetic payment-risk dataset generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any


@dataclass
class GeneratorConfig:
    """Configuration options for RingGuard AI synthetic dataset generation."""

    # Dataset Metadata
    dataset_name: str = "ringguard_mvp_v1"
    dataset_version: str = "1.0.0"
    generator_version: str = "0.2.0"
    random_seed: int = 20260903
    synthetic: bool = True

    # Entity Target Counts (Configurable MVP defaults)
    num_customers: int = 500
    num_accounts: int = 500
    target_transactions: int = 2000
    num_devices: int = 100
    num_ips: int = 150
    num_beneficiaries: int = 100
    num_merchants: int = 50

    # Temporal Window (ISO-formatted date range)
    start_date: datetime = field(default_factory=lambda: datetime(2026, 1, 1, 0, 0, 0))
    end_date: datetime = field(default_factory=lambda: datetime(2026, 3, 1, 23, 59, 59))

    # Scenario Allocations (Number of account clusters assigned per scenario)
    # Each cluster contains a cohesive group of accounts behaving according to the scenario
    scenario_clusters: Dict[str, int] = field(
        default_factory=lambda: {
            "SHARED_DEVICE_RING": 3,              # 3 clusters (~5 accounts each)
            "COMMON_BENEFICIARY_RING": 3,        # 3 clusters (~5 accounts each)
            "RAPID_FUND_DISTRIBUTION_RING": 3,   # 3 clusters (~4 accounts each)
            "HISTORICAL_CONNECTION_RING": 3,     # 3 clusters (~4 accounts each)
            "COMBINED_RING": 3,                  # 3 clusters (~6 accounts each)
            "LEGITIMATE_LOOKALIKE": 5,           # 5 clusters (~4 accounts each, hard negatives)
        }
    )

    # Output Directory
    output_dir: str = "ml/data/generated"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "dataset_version": self.dataset_version,
            "generator_version": self.generator_version,
            "random_seed": self.random_seed,
            "synthetic": self.synthetic,
            "num_customers": self.num_customers,
            "num_accounts": self.num_accounts,
            "target_transactions": self.target_transactions,
            "num_devices": self.num_devices,
            "num_ips": self.num_ips,
            "num_beneficiaries": self.num_beneficiaries,
            "num_merchants": self.num_merchants,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "scenario_clusters": self.scenario_clusters,
            "output_dir": self.output_dir,
        }
