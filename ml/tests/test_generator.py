"""RingGuard AI — Synthetic Data Generator Test Suite.

Stage 2: Synthetic Data Engine.
Validates generation success, schema validity, referential integrity,
scenario provenance fidelity, positive amounts, valid timestamps,
strict reproducibility, and validator error handling.
"""

import json
import os
import pytest
import pandas as pd

from ml.generators.config import GeneratorConfig
from ml.generators.generator import RingGuardDataGenerator
from ml.generators.validator import DataValidator, ValidationException


@pytest.fixture(scope="module")
def generated_dataset(tmp_path_factory):
    """Generate a test synthetic dataset once for the module in a temporary directory."""
    temp_dir = str(tmp_path_factory.mktemp("ringguard_synth_test"))
    config = GeneratorConfig(
        random_seed=20260903,
        output_dir=temp_dir,
        num_customers=100,
        num_accounts=100,
        target_transactions=400,
        num_devices=30,
        num_ips=40,
        num_beneficiaries=30,
        num_merchants=20,
    )
    generator = RingGuardDataGenerator(config)
    dfs, metadata = generator.generate()
    saved_dir = generator.save(temp_dir)
    return {
        "generator": generator,
        "config": config,
        "dfs": dfs,
        "metadata": metadata,
        "output_dir": saved_dir,
    }


def test_generation_succeeds_and_files_exist(generated_dataset):
    """Verify that all required CSV and JSON artifacts are created on disk."""
    out_dir = generated_dataset["output_dir"]
    expected_files = [
        "customers.csv",
        "accounts.csv",
        "transactions.csv",
        "devices.csv",
        "ips.csv",
        "beneficiaries.csv",
        "merchants.csv",
        "scenario_summary.csv",
        "dataset_metadata.json",
        "data_quality_report.txt",
    ]
    for filename in expected_files:
        path = os.path.join(out_dir, filename)
        assert os.path.exists(path), f"Expected file '{filename}' was not created"
        assert os.path.getsize(path) > 0, f"File '{filename}' is empty"


def test_entity_row_counts(generated_dataset):
    """Verify entity counts match configured parameters."""
    dfs = generated_dataset["dfs"]
    assert len(dfs["customers"]) == 100
    assert len(dfs["accounts"]) == 100
    assert len(dfs["devices"]) == 30
    assert len(dfs["ips"]) == 40
    assert len(dfs["beneficiaries"]) == 30
    assert len(dfs["merchants"]) == 20
    assert len(dfs["transactions"]) >= 400


def test_id_uniqueness(generated_dataset):
    """Verify that primary keys across all entities are 100% unique."""
    dfs = generated_dataset["dfs"]
    id_map = {
        "customers": "customer_id",
        "accounts": "account_id",
        "devices": "device_id",
        "ips": "ip_id",
        "beneficiaries": "beneficiary_id",
        "merchants": "merchant_id",
        "transactions": "transaction_id",
    }
    for table_name, pk in id_map.items():
        series = dfs[table_name][pk]
        assert series.nunique() == len(series), f"Duplicate primary keys detected in '{table_name}.{pk}'"


def test_referential_integrity(generated_dataset):
    """Verify foreign key integrity: no orphan account, device, IP, beneficiary, or merchant references."""
    dfs = generated_dataset["dfs"]
    tx_df = dfs["transactions"]

    # 1. account_id exists
    acc_ids = set(dfs["accounts"]["account_id"])
    assert tx_df["account_id"].isin(acc_ids).all(), "Orphan account_id found in transactions"

    # 2. device_id exists
    dev_ids = set(dfs["devices"]["device_id"])
    assert tx_df["device_id"].isin(dev_ids).all(), "Orphan device_id found in transactions"

    # 3. ip_id exists
    ip_ids = set(dfs["ips"]["ip_id"])
    assert tx_df["ip_id"].isin(ip_ids).all(), "Orphan ip_id found in transactions"

    # 4. beneficiary_id exists when present
    ben_ids = set(dfs["beneficiaries"]["beneficiary_id"])
    tx_bens = tx_df["beneficiary_id"].dropna()
    tx_bens = tx_bens[tx_bens.astype(str).str.strip() != ""]
    assert tx_bens.isin(ben_ids).all(), "Invalid beneficiary_id found in transactions"

    # 5. merchant_id exists when present
    mer_ids = set(dfs["merchants"]["merchant_id"])
    tx_mers = tx_df["merchant_id"].dropna()
    tx_mers = tx_mers[tx_mers.astype(str).str.strip() != ""]
    assert tx_mers.isin(mer_ids).all(), "Invalid merchant_id found in transactions"


def test_amounts_positive(generated_dataset):
    """Verify all transaction amounts are strictly greater than zero."""
    tx_df = generated_dataset["dfs"]["transactions"]
    assert (tx_df["amount"] > 0).all(), "Found non-positive transaction amounts"


def test_timestamps_valid_and_chronological(generated_dataset):
    """Verify timestamps are valid ISO 8601 and occur after account creation."""
    dfs = generated_dataset["dfs"]
    tx_df = dfs["transactions"]
    acc_df = dfs["accounts"]

    tx_times = pd.to_datetime(tx_df["timestamp"], format="ISO8601")
    acc_times = pd.to_datetime(acc_df["account_created_at"], format="ISO8601")
    acc_map = dict(zip(acc_df["account_id"], acc_times))

    tx_acc_created = tx_df["account_id"].map(acc_map)
    assert (tx_times >= tx_acc_created).all(), "Transaction timestamp occurred prior to account creation"


def test_scenario_provenance_and_labels(generated_dataset):
    """Verify that all transactions carry valid scenario types and ground truth labels."""
    tx_df = generated_dataset["dfs"]["transactions"]

    valid_labels = {"legitimate", "suspicious", "ring"}
    assert set(tx_df["ground_truth_label"].unique()).issubset(valid_labels)

    valid_scenarios = {
        "LEGITIMATE",
        "SHARED_DEVICE_RING",
        "COMMON_BENEFICIARY_RING",
        "RAPID_FUND_DISTRIBUTION_RING",
        "HISTORICAL_CONNECTION_RING",
        "COMBINED_RING",
        "LEGITIMATE_LOOKALIKE",
    }
    assert set(tx_df["scenario_type"].unique()).issubset(valid_scenarios)

    # Verify that lookalike scenario is labeled legitimate (hard negative)
    lookalikes = tx_df[tx_df["scenario_type"] == "LEGITIMATE_LOOKALIKE"]
    assert len(lookalikes) > 0, "No legitimate lookalike transactions generated"
    assert (lookalikes["ground_truth_label"] == "legitimate").all(), "Lookalikes must be labeled 'legitimate'"


def test_metadata_synthetic_flag(generated_dataset):
    """Verify dataset metadata declares synthetic=true and contains provenance."""
    meta = generated_dataset["metadata"]
    assert meta["synthetic"] is True
    assert meta["random_seed"] == 20260903
    assert "disclaimer" in meta
    assert "synthetic" in meta["disclaimer"].lower()
    assert meta["validation"]["status"] == "PASS"


def test_deterministic_reproducibility(tmp_path):
    """Verify running the generator twice with the same seed produces identical DataFrames."""
    config1 = GeneratorConfig(
        random_seed=42,
        output_dir=str(tmp_path / "run1"),
        num_customers=50,
        num_accounts=50,
        target_transactions=150,
        num_devices=20,
        num_ips=20,
        num_beneficiaries=15,
        num_merchants=10,
    )
    config2 = GeneratorConfig(
        random_seed=42,
        output_dir=str(tmp_path / "run2"),
        num_customers=50,
        num_accounts=50,
        target_transactions=150,
        num_devices=20,
        num_ips=20,
        num_beneficiaries=15,
        num_merchants=10,
    )

    gen1 = RingGuardDataGenerator(config1)
    dfs1, _ = gen1.generate()

    gen2 = RingGuardDataGenerator(config2)
    dfs2, _ = gen2.generate()

    for table in ["customers", "accounts", "devices", "ips", "beneficiaries", "merchants", "transactions"]:
        pd.testing.assert_frame_equal(dfs1[table], dfs2[table])


def test_validator_detects_corrupted_foreign_key(generated_dataset):
    """Verify that DataValidator catches corrupted foreign keys and raises ValidationException."""
    dfs = {k: v.copy() for k, v in generated_dataset["dfs"].items() if k != "scenario_summary"}
    # Corrupt transaction account_id
    dfs["transactions"].loc[0, "account_id"] = "ACC_NONEXISTENT_999999"

    validator = DataValidator(dataframes=dfs, metadata=generated_dataset["metadata"])
    with pytest.raises(ValidationException) as exc_info:
        validator.validate_all()
    assert "orphan 'account_id' references" in str(exc_info.value)
