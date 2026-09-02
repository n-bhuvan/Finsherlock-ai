"""RingGuard AI — NetworkX Graph Builder.

Stage 4: NetworkX Graph Engine.
Constructs a deterministic, multi-relational entity graph connecting customers,
accounts, transactions, devices, IP addresses, beneficiaries, and merchants.
Loads data read-only from PostgreSQL or Stage 2 CSV data.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List
import networkx as nx
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


class NetworkGraphBuilder:
    """Deterministic Multi-Relational NetworkX Graph Builder."""

    def __init__(self, session: Optional[Session] = None, data_dir: Optional[str] = None):
        """Initialize builder with optional DB session or CSV directory."""
        self.session = session
        self.data_dir = Path(data_dir) if data_dir else None

    def _load_data_from_db(self) -> Dict[str, pd.DataFrame]:
        """Load entity tables from PostgreSQL into pandas DataFrames."""
        if not self.session:
            raise ValueError("No database session provided for DB load.")

        queries = {
            "customers": "SELECT * FROM customers ORDER BY customer_id ASC;",
            "accounts": "SELECT * FROM accounts ORDER BY account_id ASC;",
            "devices": "SELECT * FROM devices ORDER BY device_id ASC;",
            "ips": "SELECT * FROM ips ORDER BY ip_id ASC;",
            "beneficiaries": "SELECT * FROM beneficiaries ORDER BY beneficiary_id ASC;",
            "merchants": "SELECT * FROM merchants ORDER BY merchant_id ASC;",
            "transactions": "SELECT * FROM transactions ORDER BY transaction_id ASC;",
        }

        dfs = {}
        for table, q in queries.items():
            result = self.session.execute(text(q))
            columns = result.keys()
            rows = result.fetchall()
            dfs[table] = pd.DataFrame(rows, columns=columns)
        return dfs

    def _load_data_from_csv(self) -> Dict[str, pd.DataFrame]:
        """Load entity CSVs from Stage 2 directory into pandas DataFrames."""
        if not self.data_dir or not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

        files = {
            "customers": "customers.csv",
            "accounts": "accounts.csv",
            "devices": "devices.csv",
            "ips": "ips.csv",
            "beneficiaries": "beneficiaries.csv",
            "merchants": "merchants.csv",
            "transactions": "transactions.csv",
        }
        dfs = {}
        for table, fname in files.items():
            fpath = self.data_dir / fname
            if not fpath.exists():
                raise FileNotFoundError(f"Missing CSV: {fpath}")
            dfs[table] = pd.read_csv(fpath, keep_default_na=False)
        return dfs

    def get_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch data from DB if session exists, else from CSV."""
        if self.session:
            return self._load_data_from_db()
        elif self.data_dir:
            return self._load_data_from_csv()
        else:
            raise ValueError("Neither database session nor data_dir was provided.")

    def build_graph(self) -> nx.MultiDiGraph:
        """Construct deterministic MultiDiGraph representing RingGuard entity networks."""
        dfs = self.get_data()
        G = nx.MultiDiGraph()

        # ==========================================
        # 1. ADD NODES
        # ==========================================

        # Customers
        for _, row in dfs["customers"].iterrows():
            cid = str(row["customer_id"])
            created_at = row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"])
            G.add_node(
                cid,
                entity_type="customer",
                name=str(row["customer_name"]),
                email=str(row["customer_email"]),
                phone_hash=str(row["customer_phone_hash"]),
                risk_tier=str(row["risk_tier"]),
                created_at=created_at,
            )

        # Accounts
        for _, row in dfs["accounts"].iterrows():
            aid = str(row["account_id"])
            created_at = row["account_created_at"].isoformat() if hasattr(row["account_created_at"], "isoformat") else str(row["account_created_at"])
            G.add_node(
                aid,
                entity_type="account",
                customer_id=str(row["customer_id"]),
                account_status=str(row["account_status"]),
                account_type=str(row["account_type"]),
                scenario_id=str(row["scenario_id"]),
                scenario_type=str(row["scenario_type"]),
                ground_truth_label=str(row["ground_truth_label"]),
                created_at=created_at,
            )

        # Devices
        for _, row in dfs["devices"].iterrows():
            did = str(row["device_id"])
            created_at = row["device_created_at"].isoformat() if hasattr(row["device_created_at"], "isoformat") else str(row["device_created_at"])
            G.add_node(
                did,
                entity_type="device",
                device_type=str(row["device_type"]),
                device_os=str(row["device_os"]),
                fingerprint_hash=str(row["fingerprint_hash"]),
                created_at=created_at,
            )

        # IPs
        for _, row in dfs["ips"].iterrows():
            ipid = str(row["ip_id"])
            G.add_node(
                ipid,
                entity_type="ip",
                ip_address=str(row["ip_address"]),
                ip_type=str(row["ip_type"]),
                asn_org=str(row["asn_org"]),
                country=str(row["country"]),
            )

        # Beneficiaries
        for _, row in dfs["beneficiaries"].iterrows():
            bid = str(row["beneficiary_id"])
            G.add_node(
                bid,
                entity_type="beneficiary",
                beneficiary_type=str(row["beneficiary_type"]),
                bank_ifsc_prefix=str(row["bank_ifsc_prefix"]),
                account_hash=str(row["account_hash"]),
            )

        # Merchants
        for _, row in dfs["merchants"].iterrows():
            mid = str(row["merchant_id"])
            G.add_node(
                mid,
                entity_type="merchant",
                merchant_category=str(row["merchant_category"]),
                merchant_name=str(row["merchant_name"]),
                merchant_risk_rating=str(row["merchant_risk_rating"]),
            )

        # Transactions
        for _, row in dfs["transactions"].iterrows():
            txid = str(row["transaction_id"])
            timestamp = row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"])
            amt = float(row["amount"]) if isinstance(row["amount"], (Decimal, int, float)) else float(str(row["amount"]))
            G.add_node(
                txid,
                entity_type="transaction",
                account_id=str(row["account_id"]),
                timestamp=timestamp,
                amount=amt,
                transaction_type=str(row["transaction_type"]),
                status=str(row["status"]),
                channel=str(row["channel"]),
                scenario_id=str(row["scenario_id"]),
                scenario_type=str(row["scenario_type"]),
                ground_truth_label=str(row["ground_truth_label"]),
            )

        # ==========================================
        # 2. ADD EDGES (Deterministic & Traceable)
        # ==========================================

        # (customer) -[owns]-> (account)
        for _, row in dfs["accounts"].iterrows():
            cid = str(row["customer_id"])
            aid = str(row["account_id"])
            G.add_edge(
                cid,
                aid,
                key=f"owns_{cid}_{aid}",
                rel_type="owns",
                source_record=aid,
                created_at=row["account_created_at"].isoformat() if hasattr(row["account_created_at"], "isoformat") else str(row["account_created_at"]),
            )

        # Tracking aggregated direct account links
        account_devices: Dict[Tuple[str, str], Dict[str, Any]] = {}
        account_ips: Dict[Tuple[str, str], Dict[str, Any]] = {}
        account_beneficiaries: Dict[Tuple[str, str], Dict[str, Any]] = {}
        account_merchants: Dict[Tuple[str, str], Dict[str, Any]] = {}

        # Transaction Edges
        for _, row in dfs["transactions"].iterrows():
            txid = str(row["transaction_id"])
            aid = str(row["account_id"])
            did = str(row["device_id"])
            ipid = str(row["ip_id"])
            bid = str(row["beneficiary_id"]).strip() if row["beneficiary_id"] else None
            mid = str(row["merchant_id"]).strip() if row["merchant_id"] else None
            timestamp = row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"])
            amt = float(row["amount"]) if isinstance(row["amount"], (Decimal, int, float)) else float(str(row["amount"]))

            # (account) -[participates_in]-> (transaction)
            G.add_edge(
                aid,
                txid,
                key=f"participates_{aid}_{txid}",
                rel_type="participates_in",
                source_record=txid,
                timestamp=timestamp,
                amount=amt,
                status=str(row["status"]),
            )

            # (transaction) -[uses_device]-> (device)
            G.add_edge(
                txid,
                did,
                key=f"tx_uses_device_{txid}_{did}",
                rel_type="uses_device",
                source_record=txid,
                timestamp=timestamp,
            )

            # (transaction) -[uses_ip]-> (ip)
            G.add_edge(
                txid,
                ipid,
                key=f"tx_uses_ip_{txid}_{ipid}",
                rel_type="uses_ip",
                source_record=txid,
                timestamp=timestamp,
            )

            # (transaction) -[involves_beneficiary]-> (beneficiary)
            if bid and bid in G:
                G.add_edge(
                    txid,
                    bid,
                    key=f"tx_involves_ben_{txid}_{bid}",
                    rel_type="involves_beneficiary",
                    source_record=txid,
                    timestamp=timestamp,
                    amount=amt,
                )

            # (transaction) -[involves_merchant]-> (merchant)
            if mid and mid in G:
                G.add_edge(
                    txid,
                    mid,
                    key=f"tx_involves_mer_{txid}_{mid}",
                    rel_type="involves_merchant",
                    source_record=txid,
                    timestamp=timestamp,
                    amount=amt,
                )

            # Aggregate account -> device tracker
            k_dev = (aid, did)
            if k_dev not in account_devices:
                account_devices[k_dev] = {
                    "count": 0,
                    "first_seen": timestamp,
                    "last_seen": timestamp,
                    "tx_ids": [],
                }
            account_devices[k_dev]["count"] += 1
            account_devices[k_dev]["last_seen"] = timestamp
            account_devices[k_dev]["tx_ids"].append(txid)

            # Aggregate account -> IP tracker
            k_ip = (aid, ipid)
            if k_ip not in account_ips:
                account_ips[k_ip] = {
                    "count": 0,
                    "first_seen": timestamp,
                    "last_seen": timestamp,
                    "tx_ids": [],
                }
            account_ips[k_ip]["count"] += 1
            account_ips[k_ip]["last_seen"] = timestamp
            account_ips[k_ip]["tx_ids"].append(txid)

            # Aggregate account -> beneficiary tracker
            if bid and bid in G:
                k_ben = (aid, bid)
                if k_ben not in account_beneficiaries:
                    account_beneficiaries[k_ben] = {
                        "count": 0,
                        "total_amount": 0.0,
                        "first_seen": timestamp,
                        "last_seen": timestamp,
                        "tx_ids": [],
                    }
                account_beneficiaries[k_ben]["count"] += 1
                account_beneficiaries[k_ben]["total_amount"] += amt
                account_beneficiaries[k_ben]["last_seen"] = timestamp
                account_beneficiaries[k_ben]["tx_ids"].append(txid)

            # Aggregate account -> merchant tracker
            if mid and mid in G:
                k_mer = (aid, mid)
                if k_mer not in account_merchants:
                    account_merchants[k_mer] = {
                        "count": 0,
                        "total_amount": 0.0,
                        "first_seen": timestamp,
                        "last_seen": timestamp,
                        "tx_ids": [],
                    }
                account_merchants[k_mer]["count"] += 1
                account_merchants[k_mer]["total_amount"] += amt
                account_merchants[k_mer]["last_seen"] = timestamp
                account_merchants[k_mer]["tx_ids"].append(txid)

        # (account) -[uses_device]-> (device)
        for (aid, did), data in sorted(account_devices.items()):
            G.add_edge(
                aid,
                did,
                key=f"acc_uses_dev_{aid}_{did}",
                rel_type="uses_device",
                source_record=aid,
                transaction_count=data["count"],
                first_seen=data["first_seen"],
                last_seen=data["last_seen"],
                transaction_ids=data["tx_ids"],
            )

        # (account) -[uses_ip]-> (ip)
        for (aid, ipid), data in sorted(account_ips.items()):
            G.add_edge(
                aid,
                ipid,
                key=f"acc_uses_ip_{aid}_{ipid}",
                rel_type="uses_ip",
                source_record=aid,
                transaction_count=data["count"],
                first_seen=data["first_seen"],
                last_seen=data["last_seen"],
                transaction_ids=data["tx_ids"],
            )

        # (account) -[sends_to]-> (beneficiary)
        for (aid, bid), data in sorted(account_beneficiaries.items()):
            G.add_edge(
                aid,
                bid,
                key=f"acc_sends_to_{aid}_{bid}",
                rel_type="sends_to",
                source_record=aid,
                transaction_count=data["count"],
                total_amount=round(data["total_amount"], 2),
                first_seen=data["first_seen"],
                last_seen=data["last_seen"],
                transaction_ids=data["tx_ids"],
            )

        # (account) -[transacts_with]-> (merchant)
        for (aid, mid), data in sorted(account_merchants.items()):
            G.add_edge(
                aid,
                mid,
                key=f"acc_transacts_{aid}_{mid}",
                rel_type="transacts_with",
                source_record=aid,
                transaction_count=data["count"],
                total_amount=round(data["total_amount"], 2),
                first_seen=data["first_seen"],
                last_seen=data["last_seen"],
                transaction_ids=data["tx_ids"],
            )

        return G
