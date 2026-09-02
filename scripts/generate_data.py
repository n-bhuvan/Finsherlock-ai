#!/usr/bin/env python3
"""RingGuard AI — Synthetic Dataset CLI Generator.

Stage 2: Synthetic Data Engine.
Provides a clean CLI to generate reproducible synthetic payment-risk datasets
with explicit scenario provenance and full relational integrity.

Usage:
    python scripts/generate_data.py
    python scripts/generate_data.py --seed 20260903 --output-dir ml/data/generated
    python scripts/generate_data.py --help
"""

import argparse
import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.generators.config import GeneratorConfig
from ml.generators.generator import RingGuardDataGenerator
from ml.generators.validator import ValidationException


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="RingGuard AI — Synthetic Payment Risk Dataset Generator (Stage 2)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260903,
        help="Random seed for reproducible deterministic dataset generation",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="ml/data/generated",
        help="Directory where generated CSV files and metadata will be saved",
    )
    parser.add_argument(
        "--num-customers",
        type=int,
        default=500,
        help="Target number of synthetic customers",
    )
    parser.add_argument(
        "--num-accounts",
        type=int,
        default=500,
        help="Target number of synthetic accounts",
    )
    parser.add_argument(
        "--target-transactions",
        type=int,
        default=2000,
        help="Target number of synthetic transactions",
    )
    parser.add_argument(
        "--num-devices",
        type=int,
        default=100,
        help="Target number of synthetic devices",
    )
    parser.add_argument(
        "--num-ips",
        type=int,
        default=150,
        help="Target number of synthetic IP addresses",
    )
    parser.add_argument(
        "--num-beneficiaries",
        type=int,
        default=100,
        help="Target number of synthetic beneficiaries",
    )
    parser.add_argument(
        "--num-merchants",
        type=int,
        default=50,
        help="Target number of synthetic merchants",
    )
    return parser.parse_args()


def main() -> None:
    """Main execution flow."""
    args = parse_args()

    config = GeneratorConfig(
        random_seed=args.seed,
        output_dir=args.output_dir,
        num_customers=args.num_customers,
        num_accounts=args.num_accounts,
        target_transactions=args.target_transactions,
        num_devices=args.num_devices,
        num_ips=args.num_ips,
        num_beneficiaries=args.num_beneficiaries,
        num_merchants=args.num_merchants,
    )

    generator = RingGuardDataGenerator(config)

    try:
        generator.generate()
        target_dir = generator.save()
        generator.print_summary(target_dir)
    except ValidationException as val_err:
        print(f"\n[ERROR] Validation Failure:\n{val_err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"\n[ERROR] Generation Failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
