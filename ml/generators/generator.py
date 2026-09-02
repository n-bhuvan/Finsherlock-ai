"""RingGuard AI — Primary Synthetic Dataset Orchestrator.

Stage 2: Synthetic Data Engine.
Orchestrates entity synthesis, controlled scenario application, validation,
and CSV / JSON serialization under ml/data/generated/.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Tuple
import pandas as pd

from ml.generators.config import GeneratorConfig
from ml.generators.entities import EntityGenerator
from ml.generators.scenarios import ScenarioEngine
from ml.generators.validator import DataValidator, ValidationException


class RingGuardDataGenerator:
    """End-to-end synthetic dataset generator and exporter."""

    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.metadata: Dict[str, Any] = {}
        self.quality_report: Dict[str, Any] = {}
        self.validator: DataValidator | None = None

    def generate(self) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
        """Generate all relational tables and metadata in memory."""
        # 1. Initialize entity generator
        ent_gen = EntityGenerator(
            seed=self.config.random_seed,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
        )

        customers_raw = ent_gen.generate_customers(self.config.num_customers)
        accounts_raw = ent_gen.generate_accounts(self.config.num_accounts, customers_raw)
        devices_raw = ent_gen.generate_devices(self.config.num_devices)
        ips_raw = ent_gen.generate_ips(self.config.num_ips)
        beneficiaries_raw = ent_gen.generate_beneficiaries(self.config.num_beneficiaries)
        merchants_raw = ent_gen.generate_merchants(self.config.num_merchants)

        # 2. Initialize scenario engine and generate transactions
        scen_engine = ScenarioEngine(
            accounts=accounts_raw,
            devices=devices_raw,
            ips=ips_raw,
            beneficiaries=beneficiaries_raw,
            merchants=merchants_raw,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            seed=self.config.random_seed,
        )

        accounts_annotated, transactions_raw, scenario_summaries_raw = scen_engine.generate_all_scenarios(
            cluster_config=self.config.scenario_clusters,
            target_transactions=self.config.target_transactions,
        )

        # 3. Convert to DataFrames
        self.dataframes = {
            "customers": pd.DataFrame(customers_raw),
            "accounts": pd.DataFrame(accounts_annotated),
            "devices": pd.DataFrame(devices_raw),
            "ips": pd.DataFrame(ips_raw),
            "beneficiaries": pd.DataFrame(beneficiaries_raw),
            "merchants": pd.DataFrame(merchants_raw),
            "transactions": pd.DataFrame(transactions_raw),
            "scenario_summary": pd.DataFrame(scenario_summaries_raw),
        }

        # 4. Construct dataset metadata
        gen_timestamp = datetime.now().isoformat()
        scenario_counts = self.dataframes["transactions"]["scenario_type"].value_counts().to_dict()
        label_counts = self.dataframes["transactions"]["ground_truth_label"].value_counts().to_dict()

        self.metadata = {
            "dataset_name": self.config.dataset_name,
            "dataset_version": self.config.dataset_version,
            "generator_version": self.config.generator_version,
            "generated_at": gen_timestamp,
            "random_seed": self.config.random_seed,
            "synthetic": True,
            "disclaimer": (
                "This dataset is entirely synthetic and does not represent real customer, "
                "transaction, or merchant data from Razorpay or any financial institution."
            ),
            "entity_counts": {
                "customers": len(self.dataframes["customers"]),
                "accounts": len(self.dataframes["accounts"]),
                "transactions": len(self.dataframes["transactions"]),
                "devices": len(self.dataframes["devices"]),
                "ips": len(self.dataframes["ips"]),
                "beneficiaries": len(self.dataframes["beneficiaries"]),
                "merchants": len(self.dataframes["merchants"]),
            },
            "scenario_distribution": scenario_counts,
            "label_distribution": label_counts,
            "config": self.config.to_dict(),
        }

        # 5. Run validation
        validation_dfs = {k: v for k, v in self.dataframes.items() if k != "scenario_summary"}
        self.validator = DataValidator(dataframes=validation_dfs, metadata=self.metadata)
        self.quality_report = self.validator.validate_all()
        self.metadata["validation"] = {
            "status": "PASS",
            "errors": 0,
            "validated_at": datetime.now().isoformat(),
        }

        return self.dataframes, self.metadata

    def save(self, output_dir: str | None = None) -> str:
        """Serialize DataFrames to CSV and metadata to JSON."""
        target_dir = output_dir or self.config.output_dir
        os.makedirs(target_dir, exist_ok=True)

        # Write CSVs
        for name, df in self.dataframes.items():
            file_path = os.path.join(target_dir, f"{name}.csv")
            df.to_csv(file_path, index=False)

        # Write metadata JSON
        meta_path = os.path.join(target_dir, "dataset_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)

        # Write human-readable quality report
        if self.validator:
            report_text = self.validator.format_human_report()
            report_path = os.path.join(target_dir, "data_quality_report.txt")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_text)

        return target_dir

    def print_summary(self, target_dir: str) -> None:
        """Print the exact structured console summary as specified in the Stage 2 requirements."""
        tx_df = self.dataframes["transactions"]
        scenario_counts = tx_df["scenario_type"].value_counts().to_dict()

        scenarios_ordered = [
            "LEGITIMATE",
            "SHARED_DEVICE_RING",
            "COMMON_BENEFICIARY_RING",
            "RAPID_FUND_DISTRIBUTION_RING",
            "HISTORICAL_CONNECTION_RING",
            "COMBINED_RING",
            "LEGITIMATE_LOOKALIKE",
        ]

        print("\nRINGGUARD AI -- SYNTHETIC DATA GENERATOR")
        print("\nDataset:")
        print(self.config.dataset_name)
        print("\nSynthetic:")
        print("true")
        print("\nSeed:")
        print(self.config.random_seed)
        print("\nCustomers:")
        print(f"{len(self.dataframes['customers']):,}")
        print("\nAccounts:")
        print(f"{len(self.dataframes['accounts']):,}")
        print("\nTransactions:")
        print(f"{len(self.dataframes['transactions']):,}")
        print("\nDevices:")
        print(f"{len(self.dataframes['devices']):,}")
        print("\nIPs:")
        print(f"{len(self.dataframes['ips']):,}")
        print("\nBeneficiaries:")
        print(f"{len(self.dataframes['beneficiaries']):,}")
        print("\nMerchants:")
        print(f"{len(self.dataframes['merchants']):,}")
        print("\nScenario distribution:")
        for sc in scenarios_ordered:
            cnt = scenario_counts.get(sc, 0)
            print(f"{sc}: {cnt:,}")
        print("\nValidation:")
        print("PASS")
        print("\nOutput:")
        print(target_dir.replace("\\", "/") + "/")
