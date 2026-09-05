"""RingGuard AI — Hard-Negative Challenge Dataset Generator.

Stage 13: Advanced Evaluation + Hard Negatives.
Generates an independent, controlled challenge benchmark (800 transactions, 200 accounts)
specifically designed to test whether Model B's graph features improve robustness or
over-flag benign entities that share infrastructure with coordinated-looking patterns.

Hard-Negative Categories:
A. Shared-device legitimate users (family/roommates sharing household desktop/tablet)
B. Shared-IP legitimate users (co-workers/students on shared broadband/campus Wi-Fi)
C. Legitimate common-beneficiary relationships (tenants paying common landlord/society)
D. Legitimate high-volume merchants & flash sales (spikes in merchant purchases)
E. Coordinated timing lookalikes (payday/bill deadline rush hour clusters)
F. Dense legitimate communities (colleagues splitting bills via P2P transfers)
G. Compound lookalikes (multiple shared attributes: shared IP + common merchant/beneficiary)
H. Subtle ring fraud controls (coordinated syndicates to measure fraud recall)
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

from ml.generators.entities import EntityGenerator
from ml.generators.validator import DataValidator


class HardNegativeChallengeGenerator:
    """Orchestrates generation of the 800-record Hard-Negative Challenge Dataset."""

    def __init__(self, seed: int = 20260905):
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        self.start_date = datetime(2026, 3, 5, 0, 0, 0)
        self.end_date = datetime(2026, 3, 25, 23, 59, 59)

        # Entity counts for challenge dataset
        self.num_customers = 200
        self.num_accounts = 200
        self.num_devices = 60
        self.num_ips = 70
        self.num_beneficiaries = 50
        self.num_merchants = 30

        self.transactions: List[Dict[str, Any]] = []
        self.challenge_metadata: List[Dict[str, Any]] = []
        self.tx_counter = 1

    def _random_date(self, start: datetime, end: datetime) -> datetime:
        """Generate a random datetime between start and end."""
        delta = end - start
        total_seconds = int(delta.total_seconds())
        if total_seconds <= 0:
            return start
        return start + timedelta(seconds=self.rng.randint(0, total_seconds))

    def _create_tx(
        self,
        account_id: str,
        device_id: str,
        ip_id: str,
        timestamp: datetime,
        amount: float,
        tx_type: str,
        channel: str,
        scenario_id: str,
        scenario_type: str,
        ground_truth_label: str,
        challenge_category: str,
        category_name: str,
        notes: str,
        beneficiary_id: str = "",
        merchant_id: str = "",
        status: str = "SUCCESS",
    ) -> Dict[str, Any]:
        """Record a challenge transaction with explicit ground truth and metadata."""
        tx_id = f"TXN_CHAL_{self.tx_counter:06d}"
        self.tx_counter += 1

        safe_amount = round(max(10.0, float(amount)), 2)

        tx = {
            "transaction_id": tx_id,
            "account_id": account_id,
            "beneficiary_id": beneficiary_id,
            "merchant_id": merchant_id,
            "device_id": device_id,
            "ip_id": ip_id,
            "timestamp": timestamp.isoformat(),
            "amount": safe_amount,
            "transaction_type": tx_type,
            "status": status,
            "channel": channel,
            "scenario_id": scenario_id,
            "scenario_type": scenario_type,
            "ground_truth_label": ground_truth_label,
        }
        self.transactions.append(tx)

        meta = {
            "transaction_id": tx_id,
            "account_id": account_id,
            "challenge_category": challenge_category,
            "category_name": category_name,
            "ground_truth_label": ground_truth_label,
            "target_binary": 1 if ground_truth_label == "ring" else 0,
            "amount": safe_amount,
            "timestamp": timestamp.isoformat(),
            "scenario_id": scenario_id,
            "notes": notes,
        }
        self.challenge_metadata.append(meta)
        return tx

    def generate(self) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
        """Generate all challenge tables and metadata."""
        # 1. Base Entities
        ent_gen = EntityGenerator(
            seed=self.seed,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        customers = ent_gen.generate_customers(self.num_customers)
        accounts = ent_gen.generate_accounts(self.num_accounts, customers)
        devices = ent_gen.generate_devices(self.num_devices)
        ips = ent_gen.generate_ips(self.num_ips)
        beneficiaries = ent_gen.generate_beneficiaries(self.num_beneficiaries)
        merchants = ent_gen.generate_merchants(self.num_merchants)

        # Separate residential and VPN/datacenter IPs
        res_ips = [ip for ip in ips if ip["ip_type"] in ("RESIDENTIAL", "CELLULAR")]
        vpn_ips = [ip for ip in ips if ip["ip_type"] in ("DATACENTER", "VPN_PROXY")]

        available_accs = list(accounts)
        self.rng.shuffle(available_accs)
        acc_idx = 0

        def allocate_accs(n: int) -> List[Dict[str, Any]]:
            nonlocal acc_idx
            selected = available_accs[acc_idx : acc_idx + n]
            acc_idx += n
            return selected

        # ======================================================================
        # CATEGORY A: Shared-Device Legitimate Users (Family / Roommates)
        # 5 clusters, ~4 accounts each = 20 accounts, ~80 txs
        # Overlap: High device sharing degree, same device_id, bursty daily usage
        # Difference: Diverse benign merchants/utilities, diverse recipient names
        # ======================================================================
        for c in range(1, 6):
            scen_id = f"CHAL_A_FAMILY_{c:03d}"
            cluster_accs = allocate_accs(4)
            shared_device = self.rng.choice(devices)
            shared_ip = self.rng.choice(res_ips)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "LEGITIMATE_LOOKALIKE"
                acc["ground_truth_label"] = "legitimate"

            base_time = self._random_date(
                self.start_date + timedelta(days=2),
                self.end_date - timedelta(days=5),
            )
            # 4 transactions per account over a 2-day period from same tablet/desktop
            for i, acc in enumerate(cluster_accs):
                for k in range(4):
                    tx_time = base_time + timedelta(hours=i * 3 + k * 8 + self.rng.randint(5, 45))
                    # Household bills, school fees, electronics, tuition: ₹1,500 - ₹49,000
                    amt = float(self.rng.choice([1500, 3500, 8500, 18000, 28000, 49000]))
                    is_p2m = self.rng.random() < 0.65
                    mer = self.rng.choice(merchants)["merchant_id"] if is_p2m else ""
                    ben = self.rng.choice(beneficiaries)["beneficiary_id"] if not is_p2m else ""

                    self._create_tx(
                        account_id=acc["account_id"],
                        device_id=shared_device["device_id"],
                        ip_id=shared_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="PAYMENT_P2M" if is_p2m else "TRANSFER_P2P",
                        channel=self.rng.choice(["UPI", "CARD", "NETBANKING"]),
                        scenario_id=scen_id,
                        scenario_type="LEGITIMATE_LOOKALIKE",
                        ground_truth_label="legitimate",
                        challenge_category="A_SHARED_DEVICE",
                        category_name="Shared-Device Legitimate Users",
                        notes="Family members sharing home desktop/tablet for independent household bills",
                        beneficiary_id=ben,
                        merchant_id=mer,
                    )

        # ======================================================================
        # CATEGORY B: Shared-IP Legitimate Users (Co-working / Corporate Office)
        # 5 clusters, ~5 accounts each = 25 accounts, ~85 txs
        # Overlap: Exact same residential/broadband IP, high concurrency
        # Difference: Independent personal mobile devices, distinct merchants
        # ======================================================================
        for c in range(1, 6):
            scen_id = f"CHAL_B_OFFICE_IP_{c:03d}"
            cluster_accs = allocate_accs(5)
            office_ip = self.rng.choice(res_ips)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "LEGITIMATE_LOOKALIKE"
                acc["ground_truth_label"] = "legitimate"

            base_time = self._random_date(
                self.start_date + timedelta(days=3),
                self.end_date - timedelta(days=3),
            )
            for i, acc in enumerate(cluster_accs):
                user_dev = self.rng.choice(devices)
                for k in range(self.rng.randint(3, 4)):
                    tx_time = base_time + timedelta(hours=k * 4 + i, minutes=self.rng.randint(1, 55))
                    # Office expenses, software licenses, professional courses, equipment: ₹450 - ₹48,000
                    amt = float(self.rng.choice([450, 1850, 4500, 12000, 24000, 48000]))
                    is_p2m = self.rng.random() < 0.70
                    mer = self.rng.choice(merchants)["merchant_id"] if is_p2m else ""
                    ben = self.rng.choice(beneficiaries)["beneficiary_id"] if not is_p2m else ""

                    self._create_tx(
                        account_id=acc["account_id"],
                        device_id=user_dev["device_id"],
                        ip_id=office_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="PAYMENT_P2M" if is_p2m else "TRANSFER_P2P",
                        channel=self.rng.choice(["UPI", "UPI", "CARD"]),
                        scenario_id=scen_id,
                        scenario_type="LEGITIMATE_LOOKALIKE",
                        ground_truth_label="legitimate",
                        challenge_category="B_SHARED_IP",
                        category_name="Shared-IP Legitimate Users",
                        notes="Co-workers on office Wi-Fi transacting from distinct mobile devices",
                        beneficiary_id=ben,
                        merchant_id=mer,
                    )

        # ======================================================================
        # CATEGORY C: Legitimate Common Beneficiaries (Landlord / Building Society)
        # 5 clusters, ~5 accounts each = 25 accounts, ~85 txs
        # Overlap: Structured funds channeled into identical beneficiary_id
        # Difference: Monthly rent cycle (1-2 txs per user), distinct devices/IPs
        # ======================================================================
        for c in range(1, 6):
            scen_id = f"CHAL_C_LANDLORD_{c:03d}"
            cluster_accs = allocate_accs(5)
            landlord_ben = self.rng.choice(beneficiaries)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "LEGITIMATE_LOOKALIKE"
                acc["ground_truth_label"] = "legitimate"

            rent_cycle_start = self._random_date(
                self.start_date + timedelta(days=5),
                self.end_date - timedelta(days=5),
            )
            for i, acc in enumerate(cluster_accs):
                user_dev = self.rng.choice(devices)
                user_ip = self.rng.choice(res_ips)
                # 3-4 structured transfers (e.g. rent + maintenance + parking fee)
                for k in range(self.rng.randint(3, 4)):
                    tx_time = rent_cycle_start + timedelta(hours=i * 6 + k * 12, minutes=self.rng.randint(10, 50))
                    # Rent, advance deposits, society maintenance, vendor invoices: ₹15,000 - ₹75,000
                    amt = float(self.rng.choice([15000, 22000, 28000, 38000, 48500, 55000, 75000]))

                    self._create_tx(
                        account_id=acc["account_id"],
                        device_id=user_dev["device_id"],
                        ip_id=user_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="TRANSFER_P2P",
                        channel=self.rng.choice(["IMPS", "NEFT", "UPI"]),
                        scenario_id=scen_id,
                        scenario_type="LEGITIMATE_LOOKALIKE",
                        ground_truth_label="legitimate",
                        challenge_category="C_COMMON_BENEFICIARY",
                        category_name="Legitimate Common Beneficiaries",
                        notes="Apartment residents paying monthly rent/society dues to common landlord",
                        beneficiary_id=landlord_ben["beneficiary_id"],
                    )

        # ======================================================================
        # CATEGORY D: Legitimate High-Volume Merchants & Flash Sales
        # 5 clusters, ~5 accounts each = 25 accounts, ~85 txs
        # Overlap: Rapid surge of payments to single merchant_id within short window
        # Difference: Authentic e-commerce checkout, diverse customer profiles
        # ======================================================================
        for c in range(1, 6):
            scen_id = f"CHAL_D_FLASH_SALE_{c:03d}"
            cluster_accs = allocate_accs(5)
            flash_merchant = self.rng.choice(merchants)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "LEGITIMATE_LOOKALIKE"
                acc["ground_truth_label"] = "legitimate"

            sale_time = self._random_date(
                self.start_date + timedelta(days=7),
                self.end_date - timedelta(days=2),
            )
            # High velocity surge within 3-hour flash sale
            for i, acc in enumerate(cluster_accs):
                user_dev = self.rng.choice(devices)
                user_ip = self.rng.choice(res_ips)
                for k in range(self.rng.randint(3, 4)):
                    tx_time = sale_time + timedelta(minutes=(i * 12) + (k * 20) + self.rng.randint(1, 10))
                    # Flash sale electronics, appliances, consumer luxury: ₹2,999 - ₹69,999
                    amt = float(self.rng.choice([2999, 4999, 9999, 19999, 29999, 49999, 69999]))

                    self._create_tx(
                        account_id=acc["account_id"],
                        device_id=user_dev["device_id"],
                        ip_id=user_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="PAYMENT_P2M",
                        channel=self.rng.choice(["UPI", "CARD"]),
                        scenario_id=scen_id,
                        scenario_type="LEGITIMATE_LOOKALIKE",
                        ground_truth_label="legitimate",
                        challenge_category="D_HIGH_VOLUME_MERCHANT",
                        category_name="High-Volume Merchant Flash Sales",
                        notes="Consumer purchase surge during e-commerce discount campaign",
                        merchant_id=flash_merchant["merchant_id"],
                    )

        # ======================================================================
        # CATEGORY E: Coordinated Timing Lookalikes (Payday / Rush Hour)
        # 5 clusters, ~5 accounts each = 25 accounts, ~85 txs
        # Overlap: Rapid bursts across multiple accounts in sub-hour window
        # Difference: Independent endpoints, diverse billers and merchants
        # ======================================================================
        for c in range(1, 6):
            scen_id = f"CHAL_E_RUSH_HOUR_{c:03d}"
            cluster_accs = allocate_accs(5)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "LEGITIMATE_LOOKALIKE"
                acc["ground_truth_label"] = "legitimate"

            rush_start = self._random_date(
                self.start_date + timedelta(days=4),
                self.end_date - timedelta(days=4),
            )
            for i, acc in enumerate(cluster_accs):
                user_dev = self.rng.choice(devices)
                user_ip = self.rng.choice(res_ips)
                for k in range(self.rng.randint(3, 4)):
                    # Sub-hour clustering
                    tx_time = rush_start + timedelta(minutes=(i * 5) + (k * 7) + self.rng.randint(1, 5))
                    # Payday bills, property taxes, insurance premiums, advances: ₹1,200 - ₹52,000
                    amt = float(self.rng.choice([1200, 3200, 7500, 16000, 28000, 52000]))
                    is_p2m = self.rng.random() < 0.60
                    mer = self.rng.choice(merchants)["merchant_id"] if is_p2m else ""
                    ben = self.rng.choice(beneficiaries)["beneficiary_id"] if not is_p2m else ""

                    self._create_tx(
                        account_id=acc["account_id"],
                        device_id=user_dev["device_id"],
                        ip_id=user_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="PAYMENT_P2M" if is_p2m else "TRANSFER_P2P",
                        channel=self.rng.choice(["UPI", "IMPS"]),
                        scenario_id=scen_id,
                        scenario_type="LEGITIMATE_LOOKALIKE",
                        ground_truth_label="legitimate",
                        challenge_category="E_COORDINATED_TIMING",
                        category_name="Coordinated Timing Rush Hour",
                        notes="Simultaneous payday utility bills and personal transfers across independent users",
                        beneficiary_id=ben,
                        merchant_id=mer,
                    )

        # ======================================================================
        # CATEGORY F: Dense Legitimate Communities (P2P Bill Splitters)
        # 5 clusters, ~5 accounts each = 25 accounts, ~90 txs
        # Overlap: High graph degree, reciprocal transactions, dense community
        # Difference: Small consumer split amounts, reciprocal balances
        # ======================================================================
        for c in range(1, 6):
            scen_id = f"CHAL_F_COMMUNITY_{c:03d}"
            cluster_accs = allocate_accs(5)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "LEGITIMATE_LOOKALIKE"
                acc["ground_truth_label"] = "legitimate"

            base_time = self._random_date(
                self.start_date + timedelta(days=6),
                self.end_date - timedelta(days=4),
            )
            for i, acc in enumerate(cluster_accs):
                user_dev = self.rng.choice(devices)
                user_ip = self.rng.choice(res_ips)
                # Transact with beneficiaries representing other members or group outings
                for k in range(self.rng.randint(3, 4)):
                    target_ben = self.rng.choice(beneficiaries)
                    tx_time = base_time + timedelta(hours=i * 5 + k * 8, minutes=self.rng.randint(5, 50))
                    # Dining, group travel bookings, shared event expenses: ₹850 - ₹48,000
                    amt = float(self.rng.choice([850, 1850, 3500, 7500, 15000, 32000, 48000]))

                    self._create_tx(
                        account_id=acc["account_id"],
                        device_id=user_dev["device_id"],
                        ip_id=user_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="TRANSFER_P2P",
                        channel="UPI",
                        scenario_id=scen_id,
                        scenario_type="LEGITIMATE_LOOKALIKE",
                        ground_truth_label="legitimate",
                        challenge_category="F_DENSE_COMMUNITY",
                        category_name="Dense Legitimate Community",
                        notes="Friends/colleagues repeatedly splitting dining and travel expenses",
                        beneficiary_id=target_ben["beneficiary_id"],
                    )

        # ======================================================================
        # CATEGORY G: Compound Lookalikes (Multiple Shared Infrastructure Signals)
        # 5 clusters, ~5 accounts each = 25 accounts, ~90 txs
        # Overlap: Simultaneous shared device + shared IP + common merchant/beneficiary!
        # Difference: Legitimate family/business partnership, zero mule cashout
        # ======================================================================
        for c in range(1, 6):
            scen_id = f"CHAL_G_COMPOUND_{c:03d}"
            cluster_accs = allocate_accs(5)
            shared_dev = self.rng.choice(devices)
            shared_ip = self.rng.choice(res_ips)
            shared_ben = self.rng.choice(beneficiaries)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "LEGITIMATE_LOOKALIKE"
                acc["ground_truth_label"] = "legitimate"

            base_time = self._random_date(
                self.start_date + timedelta(days=5),
                self.end_date - timedelta(days=3),
            )
            for i, acc in enumerate(cluster_accs):
                for k in range(self.rng.randint(3, 4)):
                    tx_time = base_time + timedelta(hours=i * 4 + k * 6, minutes=self.rng.randint(5, 40))
                    # Small business supplies, IT hardware, wholesale vendor invoices: ₹4,500 - ₹68,000
                    amt = float(self.rng.choice([4500, 12000, 21000, 35000, 49500, 68000]))

                    self._create_tx(
                        account_id=acc["account_id"],
                        device_id=shared_dev["device_id"],
                        ip_id=shared_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="TRANSFER_P2P",
                        channel=self.rng.choice(["UPI", "IMPS"]),
                        scenario_id=scen_id,
                        scenario_type="LEGITIMATE_LOOKALIKE",
                        ground_truth_label="legitimate",
                        challenge_category="G_COMPOUND_INFRA",
                        category_name="Compound Multi-Signal Lookalikes",
                        notes="Family-run small business sharing office hardware and vendor account legitimately",
                        beneficiary_id=shared_ben["beneficiary_id"],
                    )

        # ======================================================================
        # CATEGORY H: Subtle / Evasive Ring Fraud Controls (Ground Truth: RING)
        # Remaining accounts (~30-40 accounts), ~200 txs
        # Coordinated abuse syndicates designed to measure true fraud recall
        # ======================================================================
        remaining_accs = available_accs[acc_idx:]
        ring_clusters = 6
        accs_per_ring = max(4, len(remaining_accs) // ring_clusters)

        for c in range(1, ring_clusters + 1):
            scen_id = f"CHAL_H_RING_{c:03d}"
            r_accs = remaining_accs[(c - 1) * accs_per_ring : c * accs_per_ring]
            if not r_accs:
                break

            mule_dev = self.rng.choice(devices)
            mule_ip = self.rng.choice(vpn_ips) if vpn_ips else self.rng.choice(ips)
            mule_ben = self.rng.choice(beneficiaries)

            for acc in r_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "COMBINED_RING"
                acc["ground_truth_label"] = "ring"

            base_burst = self._random_date(
                self.start_date + timedelta(days=10),
                self.end_date - timedelta(days=2),
            )
            # Multi-tier coordinated operations: testing pings, mid-value layering, and cash-outs
            for i, acc in enumerate(r_accs):
                for k in range(self.rng.randint(4, 6)):
                    # Mix of synchronized bursts (seconds apart) and staged multi-hour transfers
                    tx_time = base_burst + timedelta(
                        hours=(k // 2) * 3,
                        minutes=(i * 12) + (k % 2) * 4,
                        seconds=self.rng.randint(2, 45),
                    )
                    # Spans testing pings (₹1,500-₹8,500), layering (₹14,500-₹32,000), cashouts (₹48,500-₹75,000)
                    amt = float(self.rng.choice([1500, 3500, 8500, 14500, 22000, 32000, 48500, 49900, 75000]))

                    # 85% P2P mule sink transfers, 15% P2M merchant/voucher cash-outs
                    is_p2m = self.rng.random() < 0.15
                    m_id = self.rng.choice(merchants)["merchant_id"] if is_p2m else ""
                    b_id = mule_ben["beneficiary_id"] if not is_p2m else ""

                    self._create_tx(
                        account_id=acc["account_id"],
                        device_id=mule_dev["device_id"],
                        ip_id=mule_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="PAYMENT_P2M" if is_p2m else "TRANSFER_P2P",
                        channel=self.rng.choice(["IMPS", "UPI", "NEFT"]),
                        scenario_id=scen_id,
                        scenario_type="COMBINED_RING",
                        ground_truth_label="ring",
                        challenge_category="H_SUBTLE_RING_FRAUD",
                        category_name="Subtle Evasive Ring Fraud",
                        notes="Coordinated mule syndicate channeling structured funds through shared proxy and mule sink",
                        beneficiary_id=b_id,
                        merchant_id=m_id,
                    )

        # Sort transactions chronologically
        self.transactions.sort(key=lambda t: t["timestamp"])
        self.challenge_metadata.sort(key=lambda m: m["timestamp"])

        dfs = {
            "customers": pd.DataFrame(customers),
            "accounts": pd.DataFrame(accounts),
            "devices": pd.DataFrame(devices),
            "ips": pd.DataFrame(ips),
            "beneficiaries": pd.DataFrame(beneficiaries),
            "merchants": pd.DataFrame(merchants),
            "transactions": pd.DataFrame(self.transactions),
            "challenge_metadata": pd.DataFrame(self.challenge_metadata),
        }

        metadata = {
            "dataset_name": "ringguard_challenge_v1",
            "dataset_version": "1.0.0",
            "generator_version": "0.3.0",
            "random_seed": self.seed,
            "synthetic": True,
            "seed": self.seed,
            "generated_at": datetime.now().isoformat(),
            "total_transactions": len(self.transactions),
            "total_accounts": len(accounts),
            "legitimate_hard_negatives": sum(1 for t in self.transactions if t["ground_truth_label"] == "legitimate"),
            "ring_fraud_controls": sum(1 for t in self.transactions if t["ground_truth_label"] == "ring"),
            "category_distribution": pd.DataFrame(self.challenge_metadata)["challenge_category"].value_counts().to_dict(),
        }

        return dfs, metadata

    def export_csv(self, output_dir: str = "ml/data/challenge") -> Path:
        """Export challenge tables and metadata to designated directory."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        dfs, meta = self.generate()

        # Run DataValidator against the core 7 tables
        core_dfs = {k: dfs[k] for k in ["customers", "accounts", "devices", "ips", "beneficiaries", "merchants", "transactions"]}
        validator = DataValidator(core_dfs, meta)
        validator.validate_all()

        for name, df in dfs.items():
            csv_file = out_path / f"{name}.csv"
            df.to_csv(csv_file, index=False)

        # Save metadata json
        import json
        with open(out_path / "dataset_metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return out_path
