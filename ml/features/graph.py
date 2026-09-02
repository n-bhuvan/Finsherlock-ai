"""RingGuard AI — Point-in-Time NetworkX Graph Feature Extractor.

Stage 5: Feature Engineering.
Extracts strictly point-in-time graph features for each incoming transaction.

CRITICAL INVARIANT (POINT-IN-TIME GRAPH SAFETY):
For a transaction at time T, graph topology is evaluated strictly using nodes
and relationships established at or before time T. Transactions occurring at t > T
are NOT present in the graph when features for transaction T are computed.
"""

from typing import Dict, List, Any, Optional, Set
import networkx as nx
import pandas as pd

POINT_IN_TIME_GRAPH_FEATURE_COLUMNS = [
    "g_degree",
    "g_in_degree",
    "g_out_degree",
    "g_device_count",
    "g_ip_count",
    "g_beneficiary_count",
    "g_merchant_count",
    "g_connected_accounts_count",
    "g_shared_device_accounts_count",
    "g_shared_ip_accounts_count",
    "g_shared_beneficiary_accounts_count",
    "g_has_shared_device",
    "g_has_shared_ip",
    "g_has_common_beneficiary",
    "g_max_device_sharing_degree",
    "g_max_ip_sharing_degree",
    "g_max_beneficiary_sharing_degree",
    "g_tx_count",
    "g_total_tx_amount",
    "g_avg_tx_amount",
    "g_component_size",
]


class PointInTimeGraphExtractor:
    """Computes point-in-time graph features transaction-by-transaction."""

    COLUMNS = POINT_IN_TIME_GRAPH_FEATURE_COLUMNS

    def __init__(self, dfs: Dict[str, pd.DataFrame]):
        """Initialize base static graph with customers, accounts, and endpoints."""
        self.dfs = dfs

    def extract_features(self, df_transactions: pd.DataFrame) -> pd.DataFrame:
        """Extract point-in-time graph features for all transactions.
        
        Builds the graph incrementally in chronological order (T_1, T_2, ... T_N).
        At step i, only transactions with timestamp <= T_i are in the graph.
        """
        G = nx.MultiDiGraph()
        U = nx.Graph()

        # 1. Base Static Entities
        for _, r in self.dfs["customers"].iterrows():
            cid = str(r["customer_id"])
            G.add_node(cid, entity_type="customer")
            U.add_node(cid)

        for _, r in self.dfs["accounts"].iterrows():
            aid = str(r["account_id"])
            cid = str(r["customer_id"])
            G.add_node(aid, entity_type="account")
            U.add_node(aid)
            G.add_edge(cid, aid, key=f"owns_{cid}_{aid}", rel_type="owns")
            U.add_edge(cid, aid)

        for _, r in self.dfs["devices"].iterrows():
            did = str(r["device_id"])
            G.add_node(did, entity_type="device")
            U.add_node(did)

        for _, r in self.dfs["ips"].iterrows():
            ipid = str(r["ip_id"])
            G.add_node(ipid, entity_type="ip")
            U.add_node(ipid)

        for _, r in self.dfs["beneficiaries"].iterrows():
            bid = str(r["beneficiary_id"])
            G.add_node(bid, entity_type="beneficiary")
            U.add_node(bid)

        for _, r in self.dfs["merchants"].iterrows():
            mid = str(r["merchant_id"])
            G.add_node(mid, entity_type="merchant")
            U.add_node(mid)

        # 2. Chronological Processing of Transactions
        df_sorted = df_transactions.copy()
        df_sorted["dt_timestamp"] = pd.to_datetime(df_sorted["timestamp"], utc=True)
        df_sorted["num_amount"] = pd.to_numeric(df_sorted["amount"], errors="coerce").fillna(0.0)
        df_sorted = df_sorted.sort_values(by=["dt_timestamp", "transaction_id"]).reset_index(drop=True)

        # Track account interaction history in memory for fast feature computation
        account_devices: Dict[str, Set[str]] = {}
        account_ips: Dict[str, Set[str]] = {}
        account_beneficiaries: Dict[str, Set[str]] = {}
        account_merchants: Dict[str, Set[str]] = {}
        account_tx_amounts: Dict[str, List[float]] = {}

        device_to_accounts: Dict[str, Set[str]] = {}
        ip_to_accounts: Dict[str, Set[str]] = {}
        ben_to_accounts: Dict[str, Set[str]] = {}

        feature_records: List[Dict[str, Any]] = []

        for _, row in df_sorted.iterrows():
            txid = str(row["transaction_id"])
            aid = str(row["account_id"])
            did = str(row["device_id"]) if pd.notna(row["device_id"]) else ""
            ipid = str(row["ip_id"]) if pd.notna(row["ip_id"]) else ""
            bid = str(row["beneficiary_id"]).strip() if pd.notna(row["beneficiary_id"]) and str(row["beneficiary_id"]).strip() else None
            mid = str(row["merchant_id"]).strip() if pd.notna(row["merchant_id"]) and str(row["merchant_id"]).strip() else None
            amt = float(row["num_amount"])

            # Add transaction node and edges to incremental graph
            G.add_node(txid, entity_type="transaction")
            G.add_edge(aid, txid, key=f"participates_{aid}_{txid}", rel_type="participates_in", amount=amt)
            U.add_edge(aid, txid)

            if did and did in G:
                G.add_edge(txid, did, key=f"tx_dev_{txid}_{did}", rel_type="uses_device")
                G.add_edge(aid, did, key=f"acc_dev_{aid}_{did}", rel_type="uses_device")
                U.add_edge(txid, did)
                U.add_edge(aid, did)
                if did not in device_to_accounts:
                    device_to_accounts[did] = set()
                device_to_accounts[did].add(aid)

            if ipid and ipid in G:
                G.add_edge(txid, ipid, key=f"tx_ip_{txid}_{ipid}", rel_type="uses_ip")
                G.add_edge(aid, ipid, key=f"acc_ip_{aid}_{ipid}", rel_type="uses_ip")
                U.add_edge(txid, ipid)
                U.add_edge(aid, ipid)
                if ipid not in ip_to_accounts:
                    ip_to_accounts[ipid] = set()
                ip_to_accounts[ipid].add(aid)

            if bid and bid in G:
                G.add_edge(txid, bid, key=f"tx_ben_{txid}_{bid}", rel_type="involves_beneficiary", amount=amt)
                G.add_edge(aid, bid, key=f"acc_ben_{aid}_{bid}", rel_type="sends_to", amount=amt)
                U.add_edge(txid, bid)
                U.add_edge(aid, bid)
                if bid not in ben_to_accounts:
                    ben_to_accounts[bid] = set()
                ben_to_accounts[bid].add(aid)

            if mid and mid in G:
                G.add_edge(txid, mid, key=f"tx_mer_{txid}_{mid}", rel_type="involves_merchant", amount=amt)
                G.add_edge(aid, mid, key=f"acc_mer_{aid}_{mid}", rel_type="transacts_with", amount=amt)
                U.add_edge(txid, mid)
                U.add_edge(aid, mid)

            # Update account state tracking
            if aid not in account_devices:
                account_devices[aid] = set()
                account_ips[aid] = set()
                account_beneficiaries[aid] = set()
                account_merchants[aid] = set()
                account_tx_amounts[aid] = []

            if did:
                account_devices[aid].add(did)
            if ipid:
                account_ips[aid].add(ipid)
            if bid:
                account_beneficiaries[aid].add(bid)
            if mid:
                account_merchants[aid].add(mid)
            account_tx_amounts[aid].append(amt)

            # --- Compute Point-in-Time Graph Features for `aid` at time T_i ---
            degree = G.degree(aid)
            in_degree = G.in_degree(aid)
            out_degree = G.out_degree(aid)

            dev_cnt = len(account_devices[aid])
            ip_cnt = len(account_ips[aid])
            ben_cnt = len(account_beneficiaries[aid])
            mer_cnt = len(account_merchants[aid])

            # Shared devices
            shared_dev_accs: Set[str] = set()
            max_dev_sharing = 1
            for d in account_devices[aid]:
                d_accs = device_to_accounts.get(d, set())
                if len(d_accs) > max_dev_sharing:
                    max_dev_sharing = len(d_accs)
                shared_dev_accs.update(d_accs - {aid})

            # Shared IPs
            shared_ip_accs: Set[str] = set()
            max_ip_sharing = 1
            for ip in account_ips[aid]:
                ip_accs = ip_to_accounts.get(ip, set())
                if len(ip_accs) > max_ip_sharing:
                    max_ip_sharing = len(ip_accs)
                shared_ip_accs.update(ip_accs - {aid})

            # Shared Beneficiaries
            shared_ben_accs: Set[str] = set()
            max_ben_sharing = 1
            for b in account_beneficiaries[aid]:
                b_accs = ben_to_accounts.get(b, set())
                if len(b_accs) > max_ben_sharing:
                    max_ben_sharing = len(b_accs)
                shared_ben_accs.update(b_accs - {aid})

            connected_accs = shared_dev_accs | shared_ip_accs | shared_ben_accs

            # Point-in-time transaction volume in graph
            tx_count = len(account_tx_amounts[aid])
            total_amount = sum(account_tx_amounts[aid])
            avg_amount = round(total_amount / tx_count, 2) if tx_count > 0 else 0.0

            # Component size in undirected discovery view
            comp_size = len(nx.node_connected_component(U, aid))

            feature_records.append({
                "transaction_id": txid,
                "g_degree": degree,
                "g_in_degree": in_degree,
                "g_out_degree": out_degree,
                "g_device_count": dev_cnt,
                "g_ip_count": ip_cnt,
                "g_beneficiary_count": ben_cnt,
                "g_merchant_count": mer_cnt,
                "g_connected_accounts_count": len(connected_accs),
                "g_shared_device_accounts_count": len(shared_dev_accs),
                "g_shared_ip_accounts_count": len(shared_ip_accs),
                "g_shared_beneficiary_accounts_count": len(shared_ben_accs),
                "g_has_shared_device": 1 if len(shared_dev_accs) > 0 else 0,
                "g_has_shared_ip": 1 if len(shared_ip_accs) > 0 else 0,
                "g_has_common_beneficiary": 1 if len(shared_ben_accs) > 0 else 0,
                "g_max_device_sharing_degree": max_dev_sharing,
                "g_max_ip_sharing_degree": max_ip_sharing,
                "g_max_beneficiary_sharing_degree": max_ben_sharing,
                "g_tx_count": tx_count,
                "g_total_tx_amount": round(total_amount, 2),
                "g_avg_tx_amount": avg_amount,
                "g_component_size": comp_size,
            })

        res_df = pd.DataFrame(feature_records).set_index("transaction_id")
        # Align with original input order
        res_df = res_df.loc[df_transactions["transaction_id"].values]
        return res_df[POINT_IN_TIME_GRAPH_FEATURE_COLUMNS]
