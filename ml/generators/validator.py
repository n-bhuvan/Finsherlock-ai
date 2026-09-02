"""RingGuard AI — Synthetic Dataset Integrity & Quality Validator.

Stage 2: Synthetic Data Engine.
Implements the 13 required validation rules, referential integrity assertions,
and human-inspectable data quality summary reporting.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd


class ValidationException(Exception):
    """Raised when critical validation checks fail on synthetic datasets."""
    pass


class DataValidator:
    """Validates relational integrity, scenario provenance, and quality metrics."""

    REQUIRED_COLUMNS = {
        "customers": [
            "customer_id",
            "customer_name",
            "customer_email",
            "customer_phone_hash",
            "risk_tier",
            "created_at",
        ],
        "accounts": [
            "account_id",
            "customer_id",
            "account_created_at",
            "account_status",
            "account_type",
            "scenario_id",
            "scenario_type",
            "ground_truth_label",
        ],
        "devices": [
            "device_id",
            "device_type",
            "device_created_at",
            "device_os",
            "fingerprint_hash",
        ],
        "ips": [
            "ip_id",
            "ip_address",
            "ip_type",
            "asn_org",
            "country",
        ],
        "beneficiaries": [
            "beneficiary_id",
            "beneficiary_type",
            "bank_ifsc_prefix",
            "account_hash",
        ],
        "merchants": [
            "merchant_id",
            "merchant_category",
            "merchant_name",
            "merchant_risk_rating",
        ],
        "transactions": [
            "transaction_id",
            "account_id",
            "beneficiary_id",
            "merchant_id",
            "device_id",
            "ip_id",
            "timestamp",
            "amount",
            "transaction_type",
            "status",
            "channel",
            "scenario_id",
            "scenario_type",
            "ground_truth_label",
        ],
    }

    VALID_LABELS = {"legitimate", "suspicious", "ring"}
    VALID_SCENARIO_TYPES = {
        "LEGITIMATE",
        "SHARED_DEVICE_RING",
        "COMMON_BENEFICIARY_RING",
        "RAPID_FUND_DISTRIBUTION_RING",
        "HISTORICAL_CONNECTION_RING",
        "COMBINED_RING",
        "LEGITIMATE_LOOKALIKE",
    }

    def __init__(self, dataframes: Dict[str, pd.DataFrame], metadata: Optional[Dict[str, Any]] = None):
        self.dfs = dataframes
        self.metadata = metadata or {}
        self.errors: List[str] = []
        self.quality_report: Dict[str, Any] = {}

    def validate_all(self) -> Dict[str, Any]:
        """Run all 13 required validation checks. Raises ValidationException on critical failure."""
        self.errors = []

        # 1. Non-empty check
        self._check_non_empty()

        # 2. Required columns check
        self._check_required_columns()

        # 3. ID uniqueness check
        duplicate_counts = self._check_id_uniqueness()

        # 4. Referential integrity checks
        invalid_refs = self._check_referential_integrity()

        # 5. Positive amounts check
        amount_stats = self._check_transaction_amounts()

        # 6. Timestamp validity check
        timestamp_stats = self._check_timestamps()

        # 7. Scenario labels and provenance fidelity check
        scenario_dist, label_dist = self._check_scenarios_and_labels()

        # 8. Synthetic metadata check
        synthetic_confirmed = self._check_metadata()

        # 9. Missing values check
        missing_counts = self._check_missing_values()

        # Construct comprehensive quality metrics report
        self.quality_report = {
            "validation_passed": len(self.errors) == 0,
            "synthetic_confirmed": synthetic_confirmed,
            "row_counts": {name: len(df) for name, df in self.dfs.items()},
            "duplicate_id_counts": duplicate_counts,
            "invalid_reference_counts": invalid_refs,
            "missing_value_counts": missing_counts,
            "scenario_distribution": scenario_dist,
            "label_distribution": label_dist,
            "timestamp_range": timestamp_stats,
            "amount_range": amount_stats,
            "error_count": len(self.errors),
            "errors": self.errors,
        }

        if self.errors:
            error_details = "\n - ".join(self.errors[:10])
            if len(self.errors) > 10:
                error_details += f"\n ... and {len(self.errors) - 10} more errors."
            raise ValidationException(f"Synthetic dataset validation failed with {len(self.errors)} error(s):\n - {error_details}")

        return self.quality_report

    def _check_non_empty(self) -> None:
        """Verify no required table is empty."""
        for table_name in self.REQUIRED_COLUMNS.keys():
            if table_name not in self.dfs:
                self.errors.append(f"Missing required table: '{table_name}'")
            elif len(self.dfs[table_name]) == 0:
                self.errors.append(f"Table '{table_name}' is empty (0 rows)")

    def _check_required_columns(self) -> None:
        """Verify required columns exist in each dataset."""
        for table_name, expected_cols in self.REQUIRED_COLUMNS.items():
            if table_name in self.dfs:
                df = self.dfs[table_name]
                missing = [c for c in expected_cols if c not in df.columns]
                if missing:
                    self.errors.append(f"Table '{table_name}' is missing columns: {missing}")

    def _check_id_uniqueness(self) -> Dict[str, int]:
        """Enforce primary key uniqueness."""
        id_map = {
            "customers": "customer_id",
            "accounts": "account_id",
            "devices": "device_id",
            "ips": "ip_id",
            "beneficiaries": "beneficiary_id",
            "merchants": "merchant_id",
            "transactions": "transaction_id",
        }
        dup_counts = {}
        for table_name, pk in id_map.items():
            if table_name in self.dfs and pk in self.dfs[table_name].columns:
                dups = int(self.dfs[table_name][pk].duplicated().sum())
                dup_counts[table_name] = dups
                if dups > 0:
                    self.errors.append(f"Table '{table_name}' has {dups} duplicate '{pk}' values")
            else:
                dup_counts[table_name] = 0
        return dup_counts

    def _check_referential_integrity(self) -> Dict[str, int]:
        """Enforce valid foreign key references without orphans."""
        tx_df = self.dfs.get("transactions")
        invalid_counts = {
            "account_id": 0,
            "device_id": 0,
            "ip_id": 0,
            "beneficiary_id": 0,
            "merchant_id": 0,
        }
        if tx_df is None or len(tx_df) == 0:
            return invalid_counts

        # 1. Accounts ref
        acc_ids = set(self.dfs["accounts"]["account_id"])
        bad_accs = (~tx_df["account_id"].isin(acc_ids)).sum()
        invalid_counts["account_id"] = int(bad_accs)
        if bad_accs > 0:
            self.errors.append(f"Transactions contain {bad_accs} orphan 'account_id' references")

        # 2. Devices ref
        dev_ids = set(self.dfs["devices"]["device_id"])
        bad_devs = (~tx_df["device_id"].isin(dev_ids)).sum()
        invalid_counts["device_id"] = int(bad_devs)
        if bad_devs > 0:
            self.errors.append(f"Transactions contain {bad_devs} orphan 'device_id' references")

        # 3. IPs ref
        ip_ids = set(self.dfs["ips"]["ip_id"])
        bad_ips = (~tx_df["ip_id"].isin(ip_ids)).sum()
        invalid_counts["ip_id"] = int(bad_ips)
        if bad_ips > 0:
            self.errors.append(f"Transactions contain {bad_ips} orphan 'ip_id' references")

        # 4. Beneficiaries ref (optional per tx, but if present must exist)
        ben_ids = set(self.dfs["beneficiaries"]["beneficiary_id"])
        # Non-empty and non-null beneficiary_ids
        tx_bens = tx_df["beneficiary_id"].dropna()
        tx_bens = tx_bens[tx_bens.astype(str).str.strip() != ""]
        bad_bens = (~tx_bens.isin(ben_ids)).sum()
        invalid_counts["beneficiary_id"] = int(bad_bens)
        if bad_bens > 0:
            self.errors.append(f"Transactions contain {bad_bens} invalid 'beneficiary_id' references")

        # 5. Merchants ref (optional per tx, but if present must exist)
        mer_ids = set(self.dfs["merchants"]["merchant_id"])
        tx_mers = tx_df["merchant_id"].dropna()
        tx_mers = tx_mers[tx_mers.astype(str).str.strip() != ""]
        bad_mers = (~tx_mers.isin(mer_ids)).sum()
        invalid_counts["merchant_id"] = int(bad_mers)
        if bad_mers > 0:
            self.errors.append(f"Transactions contain {bad_mers} invalid 'merchant_id' references")

        return invalid_counts

    def _check_transaction_amounts(self) -> Dict[str, float]:
        """Verify transaction amounts are strictly positive."""
        tx_df = self.dfs.get("transactions")
        if tx_df is None or len(tx_df) == 0:
            return {"min": 0.0, "max": 0.0, "mean": 0.0}

        non_positive = (tx_df["amount"] <= 0).sum()
        if non_positive > 0:
            self.errors.append(f"Transactions contain {non_positive} non-positive amounts (must be > 0)")

        return {
            "min": float(tx_df["amount"].min()),
            "max": float(tx_df["amount"].max()),
            "mean": float(round(tx_df["amount"].mean(), 2)),
            "median": float(round(tx_df["amount"].median(), 2)),
        }

    def _check_timestamps(self) -> Dict[str, str]:
        """Verify timestamp formats and chronological sanity."""
        tx_df = self.dfs.get("transactions")
        acc_df = self.dfs.get("accounts")
        if tx_df is None or len(tx_df) == 0:
            return {"start": "N/A", "end": "N/A"}

        try:
            parsed_tx_times = pd.to_datetime(tx_df["timestamp"], format="ISO8601")
        except Exception as e:
            self.errors.append(f"Failed to parse transaction timestamps: {str(e)}")
            return {"start": "ERROR", "end": "ERROR"}

        # Verify transaction timestamp >= account creation timestamp
        if acc_df is not None and "account_created_at" in acc_df.columns:
            acc_created_map = dict(zip(acc_df["account_id"], pd.to_datetime(acc_df["account_created_at"], format="ISO8601")))
            tx_acc_created = tx_df["account_id"].map(acc_created_map)
            violations = (parsed_tx_times < tx_acc_created).sum()
            if violations > 0:
                self.errors.append(f"Found {violations} transactions occurring BEFORE parent account creation timestamp")

        return {
            "earliest_transaction": parsed_tx_times.min().isoformat(),
            "latest_transaction": parsed_tx_times.max().isoformat(),
        }

    def _check_scenarios_and_labels(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Verify validity of scenario types and ground truth labels."""
        tx_df = self.dfs.get("transactions")
        acc_df = self.dfs.get("accounts")
        if tx_df is None or acc_df is None:
            return {}, {}

        # Labels check
        tx_labels = set(tx_df["ground_truth_label"].unique())
        invalid_tx_labels = tx_labels - self.VALID_LABELS
        if invalid_tx_labels:
            self.errors.append(f"Invalid transaction ground_truth_labels: {invalid_tx_labels}")

        acc_labels = set(acc_df["ground_truth_label"].unique())
        invalid_acc_labels = acc_labels - self.VALID_LABELS
        if invalid_acc_labels:
            self.errors.append(f"Invalid account ground_truth_labels: {invalid_acc_labels}")

        # Scenarios check
        tx_scenarios = set(tx_df["scenario_type"].unique())
        invalid_tx_scenarios = tx_scenarios - self.VALID_SCENARIO_TYPES
        if invalid_tx_scenarios:
            self.errors.append(f"Invalid transaction scenario_types: {invalid_tx_scenarios}")

        acc_scenarios = set(acc_df["scenario_type"].unique())
        invalid_acc_scenarios = acc_scenarios - self.VALID_SCENARIO_TYPES
        if invalid_acc_scenarios:
            self.errors.append(f"Invalid account scenario_types: {invalid_acc_scenarios}")

        scenario_dist = tx_df["scenario_type"].value_counts().to_dict()
        label_dist = tx_df["ground_truth_label"].value_counts().to_dict()

        return scenario_dist, label_dist

    def _check_metadata(self) -> bool:
        """Verify synthetic provenance metadata."""
        if not self.metadata:
            self.errors.append("Dataset metadata is empty or missing")
            return False

        if not self.metadata.get("synthetic", False):
            self.errors.append("Dataset metadata must explicitly declare 'synthetic: true'")
            return False

        required_meta_keys = ["dataset_name", "dataset_version", "random_seed", "generator_version"]
        for k in required_meta_keys:
            if k not in self.metadata:
                self.errors.append(f"Metadata is missing required attribute: '{k}'")

        return True

    def _check_missing_values(self) -> Dict[str, int]:
        """Count unexpected missing values across core fields."""
        missing = {}
        for table_name, df in self.dfs.items():
            # In transactions, beneficiary_id or merchant_id can be empty by design depending on tx_type
            if table_name == "transactions":
                core_cols = ["transaction_id", "account_id", "device_id", "ip_id", "timestamp", "amount", "ground_truth_label"]
                null_count = int(df[core_cols].isnull().sum().sum())
            else:
                null_count = int(df.isnull().sum().sum())
            missing[table_name] = null_count
            if null_count > 0:
                self.errors.append(f"Table '{table_name}' contains {null_count} unexpected null values in mandatory fields")
        return missing

    def format_human_report(self) -> str:
        """Generate formatted human-inspectable quality report."""
        r = self.quality_report
        status = "PASS" if r.get("validation_passed") else "FAIL"

        lines = [
            "================================================================================",
            "RINGGUARD AI — SYNTHETIC DATA QUALITY & INTEGRITY REPORT",
            "================================================================================",
            f"Overall Status:            {status}",
            f"Synthetic Confirmation:    {r.get('synthetic_confirmed')} (Strictly Synthetic)",
            "",
            "1. ROW COUNTS & ENTITY SIZES:",
        ]
        for tbl, count in r.get("row_counts", {}).items():
            lines.append(f"   - {tbl:15s}: {count:,} rows")

        lines.extend([
            "",
            "2. REFERENTIAL INTEGRITY & DUPLICATE CHECKS:",
        ])
        for tbl, dups in r.get("duplicate_id_counts", {}).items():
            lines.append(f"   - {tbl:15s}: {dups} duplicate primary keys")
        for ref, invalid in r.get("invalid_reference_counts", {}).items():
            lines.append(f"   - Foreign key '{ref}': {invalid} orphan references")

        lines.extend([
            "",
            "3. MISSING MANDATORY VALUES:",
        ])
        for tbl, nulls in r.get("missing_value_counts", {}).items():
            lines.append(f"   - {tbl:15s}: {nulls} nulls")

        lines.extend([
            "",
            "4. SCENARIO DISTRIBUTION (Transactions):",
        ])
        for scen, cnt in r.get("scenario_distribution", {}).items():
            lines.append(f"   - {scen:30s}: {cnt:,} txs")

        lines.extend([
            "",
            "5. GROUND TRUTH LABEL DISTRIBUTION (Transactions):",
        ])
        for lbl, cnt in r.get("label_distribution", {}).items():
            lines.append(f"   - {lbl:15s}: {cnt:,} txs")

        ts_stats = r.get("timestamp_range", {})
        lines.extend([
            "",
            "6. TEMPORAL & FINANCIAL RANGES:",
            f"   - Timestamp Window : {ts_stats.get('earliest_transaction')} to {ts_stats.get('latest_transaction')}",
        ])
        amt_stats = r.get("amount_range", {})
        lines.extend([
            f"   - Min Amount       : INR {amt_stats.get('min', 0):,.2f}",
            f"   - Max Amount       : INR {amt_stats.get('max', 0):,.2f}",
            f"   - Mean Amount      : INR {amt_stats.get('mean', 0):,.2f}",
            f"   - Median Amount    : INR {amt_stats.get('median', 0):,.2f}",
            "================================================================================",
        ])
        return "\n".join(lines)
