"""Backend Graph Service for RingGuard AI.

Stage 4: NetworkX Graph Engine.
Provides a cached, read-only interface for backend operations to interact
with the entity graph constructed from PostgreSQL.
"""

from typing import Dict, List, Optional, Any
import networkx as nx
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from ml.graph.builder import NetworkGraphBuilder
from ml.graph.traversal import (
    get_account_neighbors,
    find_shared_devices,
    find_shared_ips,
    find_common_beneficiaries,
    find_connected_accounts,
    find_multi_hop_connections,
    trace_transaction_relationships,
)
from ml.graph.features import GraphFeatureExtractor


class GraphService:
    """Singleton-style service managing the in-memory NetworkX entity graph."""

    _instance: Optional["GraphService"] = None
    _graph: Optional[nx.MultiDiGraph] = None
    _feature_extractor: Optional[GraphFeatureExtractor] = None

    @classmethod
    def get_instance(cls, force_reload: bool = False) -> "GraphService":
        """Retrieve or initialize the graph service instance."""
        if cls._instance is None:
            cls._instance = cls()
        if cls._graph is None or force_reload:
            cls._instance.reload()
        return cls._instance

    def reload(self) -> None:
        """Reload and rebuild graph from PostgreSQL."""
        session: Session = SessionLocal()
        try:
            builder = NetworkGraphBuilder(session=session)
            self._graph = builder.build_graph()
            self._feature_extractor = GraphFeatureExtractor(self._graph)
        finally:
            session.close()

    @property
    def graph(self) -> nx.MultiDiGraph:
        """Get the loaded NetworkX graph."""
        if self._graph is None:
            self.reload()
        return self._graph

    @property
    def feature_extractor(self) -> GraphFeatureExtractor:
        """Get the feature extractor."""
        if self._feature_extractor is None:
            self.reload()
        return self._feature_extractor

    def get_node_counts(self) -> Dict[str, int]:
        """Return count of nodes grouped by entity type."""
        counts: Dict[str, int] = {}
        for _, attrs in self.graph.nodes(data=True):
            etype = attrs.get("entity_type", "unknown")
            counts[etype] = counts.get(etype, 0) + 1
        return counts

    def get_edge_counts(self) -> Dict[str, int]:
        """Return count of edges grouped by relation type."""
        counts: Dict[str, int] = {}
        for _, _, _, data in self.graph.edges(keys=True, data=True):
            rel = data.get("rel_type", "unknown")
            counts[rel] = counts.get(rel, 0) + 1
        return counts

    def get_account_neighbors(self, account_id: str, relation_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return get_account_neighbors(self.graph, account_id, relation_types)

    def find_shared_devices(self, min_accounts: int = 2) -> List[Dict[str, Any]]:
        return find_shared_devices(self.graph, min_accounts)

    def find_shared_ips(self, min_accounts: int = 2) -> List[Dict[str, Any]]:
        return find_shared_ips(self.graph, min_accounts)

    def find_common_beneficiaries(self, min_accounts: int = 2) -> List[Dict[str, Any]]:
        return find_common_beneficiaries(self.graph, min_accounts)

    def find_connected_accounts(self, account_id: str, via_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return find_connected_accounts(self.graph, account_id, via_types)

    def find_multi_hop_connections(
        self, source_account_id: str, target_account_id: Optional[str] = None, max_hops: int = 3
    ) -> List[List[str]]:
        return find_multi_hop_connections(self.graph, source_account_id, target_account_id, max_hops)

    def explain_multi_hop_path(self, path: List[str]) -> List[Dict[str, Any]]:
        return explain_multi_hop_path(self.graph, path)

    def trace_transaction_relationships(self, entity_id: str) -> Dict[str, Any]:
        return trace_transaction_relationships(self.graph, entity_id)

    def extract_predictive_features(self):
        return self.feature_extractor.extract_predictive_features()

    def extract_account_metadata(self):
        return self.feature_extractor.extract_account_metadata()

    def extract_features_and_metadata(self):
        return self.feature_extractor.extract_features_and_metadata()
