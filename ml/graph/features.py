"""RingGuard AI — Graph Feature Engineering Extraction.

Stage 4: NetworkX Graph Engine.
Extracts structural, topological, and community features from the entity graph
for downstream consumption by Stage 5 ML Feature Engineering.

CRITICAL DESIGN RULE (TARGET LEAKAGE PREVENTION):
Predictive features must strictly exclude ground truth labels and scenario types.
Metadata and ground-truth labels are isolated in a separate metadata container.
"""

from typing import Dict, List, Any, Optional, Tuple
import networkx as nx
import pandas as pd

# Explicit separation between metadata/labels and predictive features
METADATA_COLUMNS = [
    "account_id",
    "scenario_type",
    "ground_truth_label",
]

PREDICTIVE_FEATURE_COLUMNS = [
    "degree",
    "in_degree",
    "out_degree",
    "device_count",
    "ip_count",
    "beneficiary_count",
    "merchant_count",
    "connected_accounts_count",
    "shared_device_accounts_count",
    "shared_ip_accounts_count",
    "shared_beneficiary_accounts_count",
    "has_shared_device",
    "has_shared_ip",
    "has_common_beneficiary",
    "max_device_sharing_degree",
    "max_ip_sharing_degree",
    "max_beneficiary_sharing_degree",
    "tx_count",
    "total_tx_amount",
    "avg_tx_amount",
    "component_id",
    "component_size",
]


class GraphFeatureExtractor:
    """Extracts topological graph features for accounts with strict target leakage isolation."""

    METADATA_COLUMNS = METADATA_COLUMNS
    PREDICTIVE_FEATURE_COLUMNS = PREDICTIVE_FEATURE_COLUMNS

    def __init__(self, graph: nx.MultiDiGraph):
        """Initialize with constructed entity graph."""
        self.graph = graph
        # Precompute undirected view and connected components for component size/id
        self._undirected = graph.to_undirected(as_view=True)
        self._components = list(nx.connected_components(self._undirected))
        self._node_to_comp: Dict[str, int] = {}
        self._comp_sizes: Dict[int, int] = {}
        for comp_idx, comp_nodes in enumerate(self._components):
            c_size = len(comp_nodes)
            self._comp_sizes[comp_idx] = c_size
            for n in comp_nodes:
                self._node_to_comp[n] = comp_idx

    def extract_account_features(self, account_id: str, include_metadata: bool = True) -> Dict[str, Any]:
        """Extract topological metrics for a single account.
        
        Args:
            account_id: Account identifier to inspect.
            include_metadata: If False, omits scenario_type and ground_truth_label.
        """
        if account_id not in self.graph:
            raise KeyError(f"Account '{account_id}' not found in graph.")

        attrs = self.graph.nodes[account_id]
        if attrs.get("entity_type") != "account":
            raise ValueError(f"Entity '{account_id}' is not an account.")

        # Degree metrics
        degree = self.graph.degree(account_id)
        in_degree = self.graph.in_degree(account_id)
        out_degree = self.graph.out_degree(account_id)

        # Direct endpoints
        devices_used = set()
        ips_used = set()
        beneficiaries_used = set()
        merchants_used = set()
        transactions = []

        for _, target, _, data in self.graph.out_edges(account_id, keys=True, data=True):
            rel = data.get("rel_type")
            if rel == "uses_device":
                devices_used.add(target)
            elif rel == "uses_ip":
                ips_used.add(target)
            elif rel == "sends_to":
                beneficiaries_used.add(target)
            elif rel == "transacts_with":
                merchants_used.add(target)
            elif rel == "participates_in":
                transactions.append(data)

        # Shared infrastructure analysis
        shared_dev_accounts = set()
        max_dev_sharing = 1
        for d in devices_used:
            dev_accounts = {
                u for u, _, _, ddata in self.graph.in_edges(d, keys=True, data=True)
                if ddata.get("rel_type") == "uses_device" and self.graph.nodes[u].get("entity_type") == "account"
            }
            if len(dev_accounts) > max_dev_sharing:
                max_dev_sharing = len(dev_accounts)
            shared_dev_accounts.update(dev_accounts - {account_id})

        shared_ip_accounts = set()
        max_ip_sharing = 1
        for ip in ips_used:
            ip_accounts = {
                u for u, _, _, idata in self.graph.in_edges(ip, keys=True, data=True)
                if idata.get("rel_type") == "uses_ip" and self.graph.nodes[u].get("entity_type") == "account"
            }
            if len(ip_accounts) > max_ip_sharing:
                max_ip_sharing = len(ip_accounts)
            shared_ip_accounts.update(ip_accounts - {account_id})

        shared_ben_accounts = set()
        max_ben_sharing = 1
        for b in beneficiaries_used:
            ben_accounts = {
                u for u, _, _, bdata in self.graph.in_edges(b, keys=True, data=True)
                if bdata.get("rel_type") == "sends_to" and self.graph.nodes[u].get("entity_type") == "account"
            }
            if len(ben_accounts) > max_ben_sharing:
                max_ben_sharing = len(ben_accounts)
            shared_ben_accounts.update(ben_accounts - {account_id})

        all_connected_accounts = shared_dev_accounts | shared_ip_accounts | shared_ben_accounts

        # Transaction volume
        tx_count = len(transactions)
        total_tx_amount = sum(tx.get("amount", 0.0) for tx in transactions)
        avg_tx_amount = round(total_tx_amount / tx_count, 2) if tx_count > 0 else 0.0

        # Component metrics
        comp_id = self._node_to_comp.get(account_id, -1)
        comp_size = self._comp_sizes.get(comp_id, 1)

        feature_dict = {
            "account_id": account_id,
            "degree": degree,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "device_count": len(devices_used),
            "ip_count": len(ips_used),
            "beneficiary_count": len(beneficiaries_used),
            "merchant_count": len(merchants_used),
            "connected_accounts_count": len(all_connected_accounts),
            "shared_device_accounts_count": len(shared_dev_accounts),
            "shared_ip_accounts_count": len(shared_ip_accounts),
            "shared_beneficiary_accounts_count": len(shared_ben_accounts),
            "has_shared_device": 1 if len(shared_dev_accounts) > 0 else 0,
            "has_shared_ip": 1 if len(shared_ip_accounts) > 0 else 0,
            "has_common_beneficiary": 1 if len(shared_ben_accounts) > 0 else 0,
            "max_device_sharing_degree": max_dev_sharing,
            "max_ip_sharing_degree": max_ip_sharing,
            "max_beneficiary_sharing_degree": max_ben_sharing,
            "tx_count": tx_count,
            "total_tx_amount": round(total_tx_amount, 2),
            "avg_tx_amount": avg_tx_amount,
            "component_id": comp_id,
            "component_size": comp_size,
        }

        if include_metadata:
            feature_dict["scenario_type"] = attrs.get("scenario_type")
            feature_dict["ground_truth_label"] = attrs.get("ground_truth_label")

        return feature_dict

    def extract_predictive_features(self) -> pd.DataFrame:
        """Extract ONLY predictive features for ML models.
        
        Strictly excludes ground_truth_label and scenario_type to prevent target leakage.
        Returns DataFrame with 'account_id' as index and 22 structural feature columns.
        """
        account_ids = sorted([
            n for n, d in self.graph.nodes(data=True) if d.get("entity_type") == "account"
        ])
        rows = [self.extract_account_features(aid, include_metadata=False) for aid in account_ids]
        df = pd.DataFrame(rows)
        # Ensure account_id is leading column or index
        ordered_cols = ["account_id"] + [c for c in PREDICTIVE_FEATURE_COLUMNS if c in df.columns]
        df = df[ordered_cols]
        # Re-verify no target leakage
        assert "ground_truth_label" not in df.columns, "Leakage: ground_truth_label found in predictive features"
        assert "scenario_type" not in df.columns, "Leakage: scenario_type found in predictive features"
        return df

    def extract_account_metadata(self) -> pd.DataFrame:
        """Extract metadata and ground truth labels separately from predictive features."""
        account_ids = sorted([
            n for n, d in self.graph.nodes(data=True) if d.get("entity_type") == "account"
        ])
        rows = []
        for aid in account_ids:
            attrs = self.graph.nodes[aid]
            rows.append({
                "account_id": aid,
                "scenario_type": attrs.get("scenario_type"),
                "ground_truth_label": attrs.get("ground_truth_label"),
            })
        return pd.DataFrame(rows)[METADATA_COLUMNS]

    def extract_features_and_metadata(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Convenience method returning cleanly separated (predictive_features_df, metadata_df)."""
        return self.extract_predictive_features(), self.extract_account_metadata()

    def extract_all_account_features(self) -> pd.DataFrame:
        """Extract all features including metadata.
        
        Note: For ML training, call `extract_predictive_features()` instead to prevent target leakage.
        """
        account_ids = sorted([
            n for n, d in self.graph.nodes(data=True) if d.get("entity_type") == "account"
        ])
        rows = [self.extract_account_features(aid, include_metadata=True) for aid in account_ids]
        return pd.DataFrame(rows)
