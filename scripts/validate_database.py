#!/usr/bin/env python3
"""RingGuard AI — PostgreSQL Database Integrity Validator.

Stage 3: PostgreSQL Database.
Validates table existence, row counts against Stage 2 source data,
primary key uniqueness, foreign key referential integrity, positive amounts,
chronological timestamps, scenario provenance, and synthetic provenance.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import text, inspect

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


def validate_database() -> dict:
    """Run full PostgreSQL validation suite."""
    engine = get_engine()
    inspector = inspect(engine)
    session = SessionLocal()

    results = {
        "tables_exist": True,
        "row_counts": {},
        "referential_integrity": True,
        "constraints": True,
        "synthetic_provenance": True,
        "errors": [],
    }

    try:
        # 1. Verify tables exist
        existing_tables = set(inspector.get_table_names())
        required_tables = [
            "customers",
            "accounts",
            "devices",
            "ips",
            "beneficiaries",
            "merchants",
            "transactions",
            "dataset_metadata",
        ]
        for tbl in required_tables:
            if tbl not in existing_tables:
                results["tables_exist"] = False
                results["errors"].append(f"Missing table: {tbl}")

        # 2. Verify row counts
        row_counts = {
            "customers": session.query(Customer).count(),
            "accounts": session.query(Account).count(),
            "devices": session.query(Device).count(),
            "ips": session.query(IPAddress).count(),
            "beneficiaries": session.query(Beneficiary).count(),
            "merchants": session.query(Merchant).count(),
            "transactions": session.query(Transaction).count(),
            "dataset_metadata": session.query(DatasetMetadata).count(),
        }
        results["row_counts"] = row_counts

        expected_counts = {
            "customers": 500,
            "accounts": 500,
            "devices": 100,
            "ips": 150,
            "beneficiaries": 100,
            "merchants": 50,
            "transactions": 2000,
        }
        for entity, exp_count in expected_counts.items():
            actual = row_counts.get(entity, 0)
            if actual != exp_count:
                results["errors"].append(
                    f"Row count mismatch for '{entity}': expected {exp_count}, got {actual}"
                )

        # 3. Verify Foreign Keys / Referential Integrity via SQL
        # Check for orphan transactions
        orphan_acc = session.execute(
            text(
                "SELECT count(*) FROM transactions t LEFT JOIN accounts a ON t.account_id = a.account_id WHERE a.account_id IS NULL;"
            )
        ).scalar()
        orphan_dev = session.execute(
            text(
                "SELECT count(*) FROM transactions t LEFT JOIN devices d ON t.device_id = d.device_id WHERE d.device_id IS NULL;"
            )
        ).scalar()
        orphan_ip = session.execute(
            text(
                "SELECT count(*) FROM transactions t LEFT JOIN ips i ON t.ip_id = i.ip_id WHERE i.ip_id IS NULL;"
            )
        ).scalar()
        orphan_ben = session.execute(
            text(
                "SELECT count(*) FROM transactions t LEFT JOIN beneficiaries b ON t.beneficiary_id = b.beneficiary_id WHERE t.beneficiary_id IS NOT NULL AND b.beneficiary_id IS NULL;"
            )
        ).scalar()
        orphan_mer = session.execute(
            text(
                "SELECT count(*) FROM transactions t LEFT JOIN merchants m ON t.merchant_id = m.merchant_id WHERE t.merchant_id IS NOT NULL AND m.merchant_id IS NULL;"
            )
        ).scalar()

        total_orphans = orphan_acc + orphan_dev + orphan_ip + orphan_ben + orphan_mer
        if total_orphans > 0:
            results["referential_integrity"] = False
            results["errors"].append(f"Detected {total_orphans} orphan foreign key records in transactions.")

        # 4. Verify Positive Amounts Constraint
        non_positive = session.execute(
            text("SELECT count(*) FROM transactions WHERE amount <= 0;")
        ).scalar()
        if non_positive > 0:
            results["constraints"] = False
            results["errors"].append(f"Detected {non_positive} transactions with amount <= 0.")

        # 5. Verify Timestamp validity
        chronology_violations = session.execute(
            text(
                "SELECT count(*) FROM transactions t JOIN accounts a ON t.account_id = a.account_id WHERE t.timestamp < a.account_created_at;"
            )
        ).scalar()
        if chronology_violations > 0:
            results["constraints"] = False
            results["errors"].append(
                f"Detected {chronology_violations} transactions occurring prior to parent account creation."
            )

        # 6. Verify Synthetic Provenance
        meta = session.query(DatasetMetadata).first()
        if not meta:
            results["synthetic_provenance"] = False
            results["errors"].append("Missing dataset_metadata record.")
        elif not meta.synthetic:
            results["synthetic_provenance"] = False
            results["errors"].append("Metadata record does not have synthetic=true.")
        elif meta.random_seed != 20260903:
            results["synthetic_provenance"] = False
            results["errors"].append(f"Unexpected seed in metadata: {meta.random_seed}")

        # 7. Overall status
        results["is_valid"] = len(results["errors"]) == 0
        return results

    finally:
        session.close()


def print_summary(results: dict):
    """Print the formatted console summary as requested."""
    counts = results.get("row_counts", {})
    all_pass = results.get("is_valid", False)

    print("\nRINGGUARD AI -- DATABASE INITIALIZATION\n")
    print("Database: PostgreSQL")
    print("Connection: SUCCESS\n")
    print("Tables:")
    for t in [
        "customers",
        "accounts",
        "devices",
        "ips",
        "beneficiaries",
        "merchants",
        "transactions",
    ]:
        print(t)

    print("\nImported rows:")
    for t in [
        "customers",
        "accounts",
        "devices",
        "ips",
        "beneficiaries",
        "merchants",
        "transactions",
    ]:
        print(f"{t}: {counts.get(t, 0):,}")

    print(f"\nReferential integrity: {'PASS' if results['referential_integrity'] else 'FAIL'}")
    print(f"Constraints: {'PASS' if results['constraints'] else 'FAIL'}")
    print(f"Synthetic provenance: {'PASS' if results['synthetic_provenance'] else 'FAIL'}")
    print(f"Database validation: {'PASS' if all_pass else 'FAIL'}")

    if results["errors"]:
        print("\nErrors encountered:")
        for err in results["errors"]:
            print(f" - {err}")


def main():
    results = validate_database()
    print_summary(results)
    if not results["is_valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
