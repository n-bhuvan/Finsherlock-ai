"""RingGuard AI — Controlled Scenario Generation Engine.

Stage 2: Synthetic Data Engine.
Implements the 7 required controlled operational scenarios with explicit
scenario provenance, multi-signal coordination, and hard-negative lookalikes.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np


class ScenarioEngine:
    """Orchestrates scenario assignments and transaction flow generation."""

    def __init__(
        self,
        accounts: List[Dict[str, Any]],
        devices: List[Dict[str, Any]],
        ips: List[Dict[str, Any]],
        beneficiaries: List[Dict[str, Any]],
        merchants: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
        seed: int,
    ):
        self.accounts = accounts
        self.devices = devices
        self.ips = ips
        self.beneficiaries = beneficiaries
        self.merchants = merchants
        self.start_date = start_date
        self.end_date = end_date
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        # Lookup maps for fast entity access
        self.acc_by_id = {a["account_id"]: a for a in self.accounts}
        self.dev_by_id = {d["device_id"]: d for d in self.devices}
        self.ip_by_id = {ip["ip_id"]: ip for ip in self.ips}

        # IP categorization for realistic assignments
        self.res_ips = [ip for ip in self.ips if ip["ip_type"] in ("RESIDENTIAL", "CELLULAR")]
        self.vpn_ips = [ip for ip in self.ips if ip["ip_type"] in ("DATACENTER", "VPN_PROXY")]

        # Track scenario metadata and transactions
        self.transactions: List[Dict[str, Any]] = []
        self.scenario_summaries: List[Dict[str, Any]] = []
        self.tx_counter = 1

    def _create_transaction(
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
        beneficiary_id: str = "",
        merchant_id: str = "",
        status: str = "SUCCESS",
    ) -> Dict[str, Any]:
        """Construct a validated transaction record with explicit scenario provenance."""
        # Ensure timestamp is strictly after account creation
        acc = self.acc_by_id[account_id]
        acc_created = datetime.fromisoformat(acc["account_created_at"])
        if timestamp <= acc_created:
            timestamp = acc_created + timedelta(hours=self.rng.randint(2, 48))

        # Enforce positive amount rounded to 2 decimal places
        safe_amount = round(max(10.0, float(amount)), 2)

        tx_id = f"TXN_{self.tx_counter:08d}"
        self.tx_counter += 1

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
        return tx

    def _random_date(self, start: datetime, end: datetime) -> datetime:
        """Generate a random datetime between start and end."""
        delta = end - start
        total_seconds = int(delta.total_seconds())
        if total_seconds <= 0:
            return start
        return start + timedelta(seconds=self.rng.randint(0, total_seconds))

    def generate_all_scenarios(
        self, cluster_config: Dict[str, int], target_transactions: int
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Execute scenario assignments and transaction synthesis."""
        available_accounts = list(self.accounts)
        self.rng.shuffle(available_accounts)
        account_pointer = 0

        def allocate_accounts(count: int) -> List[Dict[str, Any]]:
            nonlocal account_pointer
            allocated = available_accounts[account_pointer : account_pointer + count]
            account_pointer += count
            return allocated

        # ----------------------------------------------------------------------
        # Scenario 2: SHARED_DEVICE_RING
        # Multiple accounts share a single device and display synchronized bursts.
        # ----------------------------------------------------------------------
        num_sd_clusters = cluster_config.get("SHARED_DEVICE_RING", 3)
        for c in range(1, num_sd_clusters + 1):
            scen_id = f"SCEN_SHARED_DEVICE_{c:03d}"
            cluster_accs = allocate_accounts(self.rng.randint(4, 6))
            shared_dev = self.rng.choice(self.devices)
            shared_ip = self.rng.choice(self.res_ips)
            ben = self.rng.choice(self.beneficiaries)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "SHARED_DEVICE_RING"
                acc["ground_truth_label"] = "ring"

            cluster_txs = 0
            cluster_vol = 0.0
            # Coordinated bursts: All accounts execute rapid transfers from the shared device within a 2-hour burst
            burst_start = self._random_date(
                self.start_date + timedelta(days=10),
                self.end_date - timedelta(days=5),
            )
            for i, acc in enumerate(cluster_accs):
                # 3-5 transactions per account in burst
                for k in range(self.rng.randint(3, 5)):
                    tx_time = burst_start + timedelta(minutes=(i * 15) + (k * 4))
                    amt = float(self.rng.choice([9500, 9800, 9900, 14500, 19800]))
                    self._create_transaction(
                        account_id=acc["account_id"],
                        device_id=shared_dev["device_id"],
                        ip_id=shared_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="TRANSFER_P2P",
                        channel="UPI",
                        scenario_id=scen_id,
                        scenario_type="SHARED_DEVICE_RING",
                        ground_truth_label="ring",
                        beneficiary_id=ben["beneficiary_id"],
                    )
                    cluster_txs += 1
                    cluster_vol += amt

            self.scenario_summaries.append({
                "scenario_id": scen_id,
                "scenario_type": "SHARED_DEVICE_RING",
                "ground_truth_label": "ring",
                "description": "Coordinated accounts transacting from the same physical device in rapid succession",
                "num_accounts": len(cluster_accs),
                "num_transactions": cluster_txs,
                "total_volume": round(cluster_vol, 2),
                "shared_device_id": shared_dev["device_id"],
                "shared_ip_id": shared_ip["ip_id"],
                "common_beneficiary_id": ben["beneficiary_id"],
            })

        # ----------------------------------------------------------------------
        # Scenario 3: COMMON_BENEFICIARY_RING
        # Unconnected accounts funnel funds into a single mule aggregator endpoint.
        # ----------------------------------------------------------------------
        num_cb_clusters = cluster_config.get("COMMON_BENEFICIARY_RING", 3)
        for c in range(1, num_cb_clusters + 1):
            scen_id = f"SCEN_COMMON_BEN_{c:03d}"
            cluster_accs = allocate_accounts(self.rng.randint(4, 6))
            common_ben = self.rng.choice(self.beneficiaries)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "COMMON_BENEFICIARY_RING"
                acc["ground_truth_label"] = "ring"

            cluster_txs = 0
            cluster_vol = 0.0
            for acc in cluster_accs:
                # Each account uses its own device/IP, but all direct structured transfers to common beneficiary
                acc_dev = self.rng.choice(self.devices)
                acc_ip = self.rng.choice(self.res_ips)
                base_time = self._random_date(
                    self.start_date + timedelta(days=5),
                    self.end_date - timedelta(days=5),
                )
                for k in range(self.rng.randint(2, 4)):
                    tx_time = base_time + timedelta(hours=k * 8 + self.rng.randint(1, 30))
                    amt = float(self.rng.choice([49000, 48500, 49500, 24500, 24800]))
                    self._create_transaction(
                        account_id=acc["account_id"],
                        device_id=acc_dev["device_id"],
                        ip_id=acc_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="TRANSFER_P2P",
                        channel="IMPS",
                        scenario_id=scen_id,
                        scenario_type="COMMON_BENEFICIARY_RING",
                        ground_truth_label="ring",
                        beneficiary_id=common_ben["beneficiary_id"],
                    )
                    cluster_txs += 1
                    cluster_vol += amt

            self.scenario_summaries.append({
                "scenario_id": scen_id,
                "scenario_type": "COMMON_BENEFICIARY_RING",
                "ground_truth_label": "ring",
                "description": "Multi-account funnel directing repeated structured payments to a common mule destination",
                "num_accounts": len(cluster_accs),
                "num_transactions": cluster_txs,
                "total_volume": round(cluster_vol, 2),
                "shared_device_id": "NONE",
                "shared_ip_id": "NONE",
                "common_beneficiary_id": common_ben["beneficiary_id"],
            })

        # ----------------------------------------------------------------------
        # Scenario 4: RAPID_FUND_DISTRIBUTION_RING
        # High-velocity fan-out dispersal within short intervals (structuring/dispersion).
        # ----------------------------------------------------------------------
        num_rf_clusters = cluster_config.get("RAPID_FUND_DISTRIBUTION_RING", 3)
        for c in range(1, num_rf_clusters + 1):
            scen_id = f"SCEN_RAPID_DISTRIB_{c:03d}"
            cluster_accs = allocate_accounts(self.rng.randint(3, 5))
            distrib_device = self.rng.choice(self.devices)
            distrib_ip = self.rng.choice(self.vpn_ips) if self.vpn_ips else self.rng.choice(self.ips)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "RAPID_FUND_DISTRIBUTION_RING"
                acc["ground_truth_label"] = "ring"

            cluster_txs = 0
            cluster_vol = 0.0
            dispersion_time = self._random_date(
                self.start_date + timedelta(days=8),
                self.end_date - timedelta(days=3),
            )
            # Rapid cascade: transfers across multiple targets within minutes
            target_bens = self.rng.sample(self.beneficiaries, min(4, len(self.beneficiaries)))
            for i, acc in enumerate(cluster_accs):
                for j, ben in enumerate(target_bens):
                    tx_time = dispersion_time + timedelta(minutes=(i * 10) + (j * 2) + self.rng.randint(0, 1))
                    amt = float(self.rng.choice([15000, 20000, 25000, 30000]))
                    self._create_transaction(
                        account_id=acc["account_id"],
                        device_id=distrib_device["device_id"],
                        ip_id=distrib_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="TRANSFER_P2P",
                        channel="IMPS",
                        scenario_id=scen_id,
                        scenario_type="RAPID_FUND_DISTRIBUTION_RING",
                        ground_truth_label="ring",
                        beneficiary_id=ben["beneficiary_id"],
                    )
                    cluster_txs += 1
                    cluster_vol += amt

            self.scenario_summaries.append({
                "scenario_id": scen_id,
                "scenario_type": "RAPID_FUND_DISTRIBUTION_RING",
                "ground_truth_label": "ring",
                "description": "High-velocity rapid fund dispersal across multiple accounts/beneficiaries in sub-hour window",
                "num_accounts": len(cluster_accs),
                "num_transactions": cluster_txs,
                "total_volume": round(cluster_vol, 2),
                "shared_device_id": distrib_device["device_id"],
                "shared_ip_id": distrib_ip["ip_id"],
                "common_beneficiary_id": "MULTI_TARGET",
            })

        # ----------------------------------------------------------------------
        # Scenario 5: HISTORICAL_CONNECTION_RING
        # Historical dormant linkages (shared device/IP weeks prior) that re-activate concurrently.
        # ----------------------------------------------------------------------
        num_hc_clusters = cluster_config.get("HISTORICAL_CONNECTION_RING", 3)
        for c in range(1, num_hc_clusters + 1):
            scen_id = f"SCEN_HIST_CONN_{c:03d}"
            cluster_accs = allocate_accounts(self.rng.randint(3, 5))
            hist_device = self.rng.choice(self.devices)
            hist_ip = self.rng.choice(self.res_ips)
            recent_device = self.rng.choice(self.devices)
            ben = self.rng.choice(self.beneficiaries)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "HISTORICAL_CONNECTION_RING"
                acc["ground_truth_label"] = "ring"

            cluster_txs = 0
            cluster_vol = 0.0

            # 1. Historical footprint: Accounts transacted together 45 days in the past on hist_device
            hist_time = self.start_date + timedelta(days=self.rng.randint(2, 10))
            for acc in cluster_accs:
                self._create_transaction(
                    account_id=acc["account_id"],
                    device_id=hist_device["device_id"],
                    ip_id=hist_ip["ip_id"],
                    timestamp=hist_time + timedelta(hours=self.rng.randint(1, 12)),
                    amount=500.0,
                    tx_type="PAYMENT_P2M",
                    channel="UPI",
                    scenario_id=scen_id,
                    scenario_type="HISTORICAL_CONNECTION_RING",
                    ground_truth_label="ring",
                    merchant_id=self.rng.choice(self.merchants)["merchant_id"],
                )
                cluster_txs += 1
                cluster_vol += 500.0

            # 2. Modern re-activation: 40 days later, concurrent high-value coordinated movement
            modern_time = self.end_date - timedelta(days=self.rng.randint(3, 10))
            for acc in cluster_accs:
                amt = float(self.rng.choice([35000, 42000, 48000]))
                self._create_transaction(
                    account_id=acc["account_id"],
                    device_id=recent_device["device_id"],
                    ip_id=hist_ip["ip_id"],
                    timestamp=modern_time + timedelta(minutes=self.rng.randint(5, 45)),
                    amount=amt,
                    tx_type="TRANSFER_P2P",
                    channel="IMPS",
                    scenario_id=scen_id,
                    scenario_type="HISTORICAL_CONNECTION_RING",
                    ground_truth_label="ring",
                    beneficiary_id=ben["beneficiary_id"],
                )
                cluster_txs += 1
                cluster_vol += amt

            self.scenario_summaries.append({
                "scenario_id": scen_id,
                "scenario_type": "HISTORICAL_CONNECTION_RING",
                "ground_truth_label": "ring",
                "description": "Historical device/IP linkage established in early window reactivated for concurrent fund movement",
                "num_accounts": len(cluster_accs),
                "num_transactions": cluster_txs,
                "total_volume": round(cluster_vol, 2),
                "shared_device_id": f"{hist_device['device_id']},{recent_device['device_id']}",
                "shared_ip_id": hist_ip["ip_id"],
                "common_beneficiary_id": ben["beneficiary_id"],
            })

        # ----------------------------------------------------------------------
        # Scenario 6: COMBINED_RING
        # Compounding signals: shared device + datacenter/VPN IP + common beneficiary + micro-burst timing.
        # ----------------------------------------------------------------------
        num_comb_clusters = cluster_config.get("COMBINED_RING", 3)
        for c in range(1, num_comb_clusters + 1):
            scen_id = f"SCEN_COMBINED_RING_{c:03d}"
            cluster_accs = allocate_accounts(self.rng.randint(5, 7))
            syndicate_dev = self.rng.choice(self.devices)
            syndicate_ip = self.rng.choice(self.vpn_ips) if self.vpn_ips else self.rng.choice(self.ips)
            syndicate_ben = self.rng.choice(self.beneficiaries)

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "COMBINED_RING"
                acc["ground_truth_label"] = "ring"

            cluster_txs = 0
            cluster_vol = 0.0
            base_burst_time = self._random_date(
                self.start_date + timedelta(days=15),
                self.end_date - timedelta(days=2),
            )
            # Micro-burst timing: transactions within seconds/minutes
            for i, acc in enumerate(cluster_accs):
                for k in range(self.rng.randint(2, 4)):
                    tx_time = base_burst_time + timedelta(seconds=(i * 120) + (k * 25) + self.rng.randint(1, 15))
                    amt = float(self.rng.choice([49500, 49999, 49000, 99500]))
                    self._create_transaction(
                        account_id=acc["account_id"],
                        device_id=syndicate_dev["device_id"],
                        ip_id=syndicate_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type="TRANSFER_P2P",
                        channel="IMPS",
                        scenario_id=scen_id,
                        scenario_type="COMBINED_RING",
                        ground_truth_label="ring",
                        beneficiary_id=syndicate_ben["beneficiary_id"],
                    )
                    cluster_txs += 1
                    cluster_vol += amt

            self.scenario_summaries.append({
                "scenario_id": scen_id,
                "scenario_type": "COMBINED_RING",
                "ground_truth_label": "ring",
                "description": "Multi-signal abuse ring: shared hardware, VPN/hosting IP, common mule sink, sub-minute bursts",
                "num_accounts": len(cluster_accs),
                "num_transactions": cluster_txs,
                "total_volume": round(cluster_vol, 2),
                "shared_device_id": syndicate_dev["device_id"],
                "shared_ip_id": syndicate_ip["ip_id"],
                "common_beneficiary_id": syndicate_ben["beneficiary_id"],
            })

        # ----------------------------------------------------------------------
        # Scenario 7: LEGITIMATE_LOOKALIKE (Hard Negatives)
        # Genuinely shared attributes (family devices, office IPs, common utility/landlord)
        # with ground_truth_label = "legitimate" and realistic benign transaction flows.
        # ----------------------------------------------------------------------
        num_lookalike_clusters = cluster_config.get("LEGITIMATE_LOOKALIKE", 5)
        for c in range(1, num_lookalike_clusters + 1):
            scen_id = f"SCEN_LOOKALIKE_{c:03d}"
            cluster_accs = allocate_accounts(self.rng.randint(3, 5))

            # Cluster subtype: 
            # 1 = Shared family device (e.g. household tablet or home PC)
            # 2 = Shared corporate/office IP (e.g. co-working space or office fiber)
            # 3 = Common supplier/landlord beneficiary (e.g. apartment society maintenance)
            lookalike_type = c % 3

            if lookalike_type == 0:
                # Shared Family Device
                shared_dev = self.rng.choice(self.devices)
                shared_ip = self.rng.choice(self.res_ips)
                desc = "Legitimate family members sharing a household desktop or tablet for independent personal bills"
                dev_label = shared_dev["device_id"]
                ip_label = shared_ip["ip_id"]
                ben_label = "DIVERSE"
            elif lookalike_type == 1:
                # Shared Office IP
                shared_dev = None
                shared_ip = self.rng.choice(self.res_ips)
                desc = "Legitimate co-workers transacting on separate mobile devices from the same office broadband IP"
                dev_label = "INDEPENDENT"
                ip_label = shared_ip["ip_id"]
                ben_label = "DIVERSE"
            else:
                # Common Supplier / Landlord / Society Beneficiary
                shared_dev = None
                shared_ip = None
                common_supplier_ben = self.rng.choice(self.beneficiaries)
                desc = "Independent tenants/residents paying a common legitimate landlord or utility society account"
                dev_label = "INDEPENDENT"
                ip_label = "INDEPENDENT"
                ben_label = common_supplier_ben["beneficiary_id"]

            for acc in cluster_accs:
                acc["scenario_id"] = scen_id
                acc["scenario_type"] = "LEGITIMATE_LOOKALIKE"
                acc["ground_truth_label"] = "legitimate"

            cluster_txs = 0
            cluster_vol = 0.0

            # Generate benign, spaced-out transactions reflecting normal consumer spending
            for acc in cluster_accs:
                acc_dev = shared_dev if shared_dev else self.rng.choice(self.devices)
                acc_ip = shared_ip if shared_ip else self.rng.choice(self.res_ips)
                # Transactions scattered realistically across the entire temporal window (days/weeks apart)
                for k in range(self.rng.randint(3, 6)):
                    tx_time = self._random_date(self.start_date, self.end_date)
                    # Normal consumer payment amounts
                    amt = float(self.rng.choice([150, 450, 899, 1250, 2400, 3500, 5000]))

                    if lookalike_type == 2:
                        target_ben = common_supplier_ben["beneficiary_id"]
                        target_mer = ""
                        tx_t = "TRANSFER_P2P"
                    else:
                        target_ben = ""
                        target_mer = self.rng.choice(self.merchants)["merchant_id"]
                        tx_t = "PAYMENT_P2M"

                    self._create_transaction(
                        account_id=acc["account_id"],
                        device_id=acc_dev["device_id"],
                        ip_id=acc_ip["ip_id"],
                        timestamp=tx_time,
                        amount=amt,
                        tx_type=tx_t,
                        channel=self.rng.choice(["UPI", "CARD", "NETBANKING"]),
                        scenario_id=scen_id,
                        scenario_type="LEGITIMATE_LOOKALIKE",
                        ground_truth_label="legitimate",
                        beneficiary_id=target_ben,
                        merchant_id=target_mer,
                    )
                    cluster_txs += 1
                    cluster_vol += amt

            self.scenario_summaries.append({
                "scenario_id": scen_id,
                "scenario_type": "LEGITIMATE_LOOKALIKE",
                "ground_truth_label": "legitimate",
                "description": desc,
                "num_accounts": len(cluster_accs),
                "num_transactions": cluster_txs,
                "total_volume": round(cluster_vol, 2),
                "shared_device_id": dev_label,
                "shared_ip_id": ip_label,
                "common_beneficiary_id": ben_label,
            })

        # ----------------------------------------------------------------------
        # Scenario 1: LEGITIMATE (Baseline Population)
        # All remaining unassigned accounts receive normal, non-coordinated consumer patterns
        # ----------------------------------------------------------------------
        baseline_accs = available_accounts[account_pointer:]
        for acc in baseline_accs:
            acc["scenario_id"] = "SCEN_LEGIT_BASELINE"
            acc["scenario_type"] = "LEGITIMATE"
            acc["ground_truth_label"] = "legitimate"

        # Calculate remaining transactions needed to hit target_transactions
        generated_so_far = len(self.transactions)
        remaining_txs = max(target_transactions - generated_so_far, len(baseline_accs) * 2)

        # Map each baseline account to a consistent primary device and IP
        acc_primary_dev = {a["account_id"]: self.rng.choice(self.devices) for a in baseline_accs}
        acc_primary_ip = {a["account_id"]: self.rng.choice(self.res_ips) for a in baseline_accs}

        legit_vol = 0.0
        legit_count = 0
        for _ in range(remaining_txs):
            acc = self.rng.choice(baseline_accs)
            # 85% use primary device, 15% use secondary device
            dev = acc_primary_dev[acc["account_id"]] if self.rng.random() < 0.85 else self.rng.choice(self.devices)
            ip = acc_primary_ip[acc["account_id"]] if self.rng.random() < 0.85 else self.rng.choice(self.res_ips)

            tx_time = self._random_date(self.start_date, self.end_date)
            # Realistic power-law-like distribution for benign consumer spending
            amt = float(round(float(self.np_rng.exponential(scale=1200)) + 50.0, 2))
            amt = min(amt, 45000.0)

            # 70% merchant payment, 30% P2P transfer
            is_p2m = self.rng.random() < 0.70
            target_mer = self.rng.choice(self.merchants)["merchant_id"] if is_p2m else ""
            target_ben = self.rng.choice(self.beneficiaries)["beneficiary_id"] if not is_p2m else ""
            tx_type = "PAYMENT_P2M" if is_p2m else "TRANSFER_P2P"

            self._create_transaction(
                account_id=acc["account_id"],
                device_id=dev["device_id"],
                ip_id=ip["ip_id"],
                timestamp=tx_time,
                amount=amt,
                tx_type=tx_type,
                channel=self.rng.choice(["UPI", "UPI", "CARD", "NETBANKING"]),
                scenario_id="SCEN_LEGIT_BASELINE",
                scenario_type="LEGITIMATE",
                ground_truth_label="legitimate",
                beneficiary_id=target_ben,
                merchant_id=target_mer,
            )
            legit_count += 1
            legit_vol += amt

        self.scenario_summaries.append({
            "scenario_id": "SCEN_LEGIT_BASELINE",
            "scenario_type": "LEGITIMATE",
            "ground_truth_label": "legitimate",
            "description": "Baseline uncoordinated individual consumer transactions across diverse merchants and personal recipients",
            "num_accounts": len(baseline_accs),
            "num_transactions": legit_count,
            "total_volume": round(legit_vol, 2),
            "shared_device_id": "NONE",
            "shared_ip_id": "NONE",
            "common_beneficiary_id": "NONE",
        })

        # Sort transactions chronologically by timestamp
        self.transactions.sort(key=lambda t: t["timestamp"])

        return self.accounts, self.transactions, self.scenario_summaries
