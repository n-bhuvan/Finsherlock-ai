#!/usr/bin/env python3
"""RingGuard AI — PostgreSQL Database Seeder.

Stage 3: PostgreSQL Database.
Imports Stage 2 generated CSV datasets from ml/data/generated/ into PostgreSQL
in strict foreign-key dependency order, preserving IDs, exact Decimal currency
precision, timezone-aware timestamps, and synthetic provenance.

Usage:
    python scripts/seed_database.py
    python scripts/seed_database.py --reset
    python scripts/seed_database.py --data-dir ml/data/generated --reset
"""

import argparse
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import pandas as pd
from sqlalchemy import text

# Ensure repository root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import get_engine, SessionLocal
from app.models import (
    Customer,
    Account,
    Device,
    IPAddress,
    Beneficiary,
    Merchant,
    Transaction,
    DatasetMetadata,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="RingGuard AI — Database Seed Pipeline (Stage 3)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="ml/data/generated",
        help="Directory containing Stage 2 generated CSVs and metadata",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Cleanly truncate existing tables before seeding to prevent duplicate records",
    )
    return parser.parse_args()


def seed_database(data_dir: str, reset: bool = False) -> dict:
    """Execute the database seeding pipeline."""
    data_path = Path(data_dir)
    if not data_path.is_absolute():
        data_path = REPO_ROOT / data_path

    # Verify input files exist
    required_files = [
        "customers.csv",
        "accounts.csv",
        "devices.csv",
        "ips.csv",
        "beneficiaries.csv",
        "merchants.csv",
        "transactions.csv",
        "dataset_metadata.json",
    ]
    for rf in required_files:
        p = data_path / rf
        if not p.exists():
            raise FileNotFoundError(f"Required dataset file missing: {p}")

    session = SessionLocal()
    counts = {}

    try:
        # Reset if requested
        if reset:
            print("[INFO] Resetting tables via CASCADE truncation...")
            session.execute(
                text(
                    "TRUNCATE TABLE transactions, accounts, customers, devices, ips, beneficiaries, merchants, dataset_metadata CASCADE;"
                )
            )
            session.commit()

        # Check if tables already have data when not resetting
        existing_count = session.query(Customer).count()
        if existing_count > 0 and not reset:
            raise RuntimeError(
                f"Database already contains {existing_count} customers. "
                "Use --reset to safely truncate and reseed without duplicate ID conflicts."
            )

        # 1. Customers
        print("[1/8] Importing customers.csv...")
        df_cust = pd.read_csv(data_path / "customers.csv")
        customers = [
            Customer(
                customer_id=row["customer_id"],
                customer_name=row["customer_name"],
                customer_email=row["customer_email"],
                customer_phone_hash=row["customer_phone_hash"],
                risk_tier=row["risk_tier"],
                created_at=pd.to_datetime(row["created_at"], format="ISO8601").to_pydatetime(),
            )
            for _, row in df_cust.iterrows()
        ]
        session.bulk_save_objects(customers)
        session.commit()
        counts["customers"] = len(customers)

        # 2. Accounts
        print("[2/8] Importing accounts.csv...")
        df_acc = pd.read_csv(data_path / "accounts.csv")
        accounts = [
            Account(
                account_id=row["account_id"],
                customer_id=row["customer_id"],
                account_created_at=pd.to_datetime(row["account_created_at"], format="ISO8601").to_pydatetime(),
                account_status=row["account_status"],
                account_type=row["account_type"],
                scenario_id=row["scenario_id"],
                scenario_type=row["scenario_type"],
                ground_truth_label=row["ground_truth_label"],
            )
            for _, row in df_acc.iterrows()
        ]
        session.bulk_save_objects(accounts)
        session.commit()
        counts["accounts"] = len(accounts)

        # 3. Devices
        print("[3/8] Importing devices.csv...")
        df_dev = pd.read_csv(data_path / "devices.csv")
        devices = [
            Device(
                device_id=row["device_id"],
                device_type=row["device_type"],
                device_created_at=pd.to_datetime(row["device_created_at"], format="ISO8601").to_pydatetime(),
                device_os=row["device_os"],
                fingerprint_hash=row["fingerprint_hash"],
            )
            for _, row in df_dev.iterrows()
        ]
        session.bulk_save_objects(devices)
        session.commit()
        counts["devices"] = len(devices)

        # 4. IPs
        print("[4/8] Importing ips.csv...")
        df_ip = pd.read_csv(data_path / "ips.csv")
        ips = [
            IPAddress(
                ip_id=row["ip_id"],
                ip_address=row["ip_address"],
                ip_type=row["ip_type"],
                asn_org=row["asn_org"],
                country=row["country"],
            )
            for _, row in df_ip.iterrows()
        ]
        session.bulk_save_objects(ips)
        session.commit()
        counts["ips"] = len(ips)

        # 5. Beneficiaries
        print("[5/8] Importing beneficiaries.csv...")
        df_ben = pd.read_csv(data_path / "beneficiaries.csv")
        beneficiaries = [
            Beneficiary(
                beneficiary_id=row["beneficiary_id"],
                beneficiary_type=row["beneficiary_type"],
                bank_ifsc_prefix=row["bank_ifsc_prefix"],
                account_hash=row["account_hash"],
            )
            for _, row in df_ben.iterrows()
        ]
        session.bulk_save_objects(beneficiaries)
        session.commit()
        counts["beneficiaries"] = len(beneficiaries)

        # 6. Merchants
        print("[6/8] Importing merchants.csv...")
        df_mer = pd.read_csv(data_path / "merchants.csv")
        merchants = [
            Merchant(
                merchant_id=row["merchant_id"],
                merchant_category=row["merchant_category"],
                merchant_name=row["merchant_name"],
                merchant_risk_rating=row["merchant_risk_rating"],
            )
            for _, row in df_mer.iterrows()
        ]
        session.bulk_save_objects(merchants)
        session.commit()
        counts["merchants"] = len(merchants)

        # 7. Transactions
        print("[7/8] Importing transactions.csv...")
        df_tx = pd.read_csv(data_path / "transactions.csv", keep_default_na=False)
        transactions = []
        for _, row in df_tx.iterrows():
            ben_id = row["beneficiary_id"].strip() if row["beneficiary_id"] else None
            mer_id = row["merchant_id"].strip() if row["merchant_id"] else None
            transactions.append(
                Transaction(
                    transaction_id=row["transaction_id"],
                    account_id=row["account_id"],
                    beneficiary_id=ben_id,
                    merchant_id=mer_id,
                    device_id=row["device_id"],
                    ip_id=row["ip_id"],
                    timestamp=pd.to_datetime(row["timestamp"], format="ISO8601").to_pydatetime(),
                    amount=Decimal(str(row["amount"])),
                    transaction_type=row["transaction_type"],
                    status=row["status"],
                    channel=row["channel"],
                    scenario_id=row["scenario_id"],
                    scenario_type=row["scenario_type"],
                    ground_truth_label=row["ground_truth_label"],
                )
            )
        session.bulk_save_objects(transactions)
        session.commit()
        counts["transactions"] = len(transactions)

        # 8. Dataset Metadata
        print("[8/8] Importing dataset_metadata.json...")
        with open(data_path / "dataset_metadata.json", "r", encoding="utf-8") as f:
            meta_dict = json.load(f)

        metadata_record = DatasetMetadata(
            dataset_name=meta_dict["dataset_name"],
            dataset_version=meta_dict["dataset_version"],
            generator_version=meta_dict["generator_version"],
            random_seed=meta_dict["random_seed"],
            synthetic=meta_dict["synthetic"],
            disclaimer=meta_dict["disclaimer"],
            imported_at=datetime.now(),
            entity_counts_json=json.dumps(meta_dict.get("entity_counts", {})),
            config_json=json.dumps(meta_dict.get("config", {})),
        )
        session.add(metadata_record)
        session.commit()
        counts["dataset_metadata"] = 1

        print("\n[SUCCESS] Seeding complete!")
        return counts

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def main():
    args = parse_args()
    try:
        counts = seed_database(data_dir=args.data_dir, reset=args.reset)
        print("\nSeeded entity counts:")
        for entity, cnt in counts.items():
            print(f"  - {entity:18s}: {cnt:,} rows")
    except Exception as err:
        print(f"\n[ERROR] Seeding failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
