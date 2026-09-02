"""RingGuard AI — NetworkX Graph Engine Test Suite.

Stage 4: NetworkX Graph Engine.
Validates graph construction from PostgreSQL, node/edge counts, referential integrity,
shared infrastructure discovery, multi-hop traversals, transaction tracing,
topological feature extraction, and deterministic reproducibility.
"""

import pytest
import networkx as nx
from app.db.session import SessionLocal
from ml.graph.builder import NetworkGraphBuilder
from ml.graph.traversal import (
    get_account_neighbors,
    find_shared_devices,
    find_shared_ips,
    find_common_beneficiaries,
    find_connected_accounts,
    find_multi_hop_connections,
    explain_multi_hop_path,
    trace_transaction_relationships,
)
from ml.graph.features import GraphFeatureExtractor


@pytest.fixture(scope="module")
def graph_instance():
    """Build and provide a module-level graph instance from PostgreSQL."""
    session = SessionLocal()
    try:
        builder = NetworkGraphBuilder(session=session)
        G = builder.build_graph()
        return G
    finally:
        session.close()


# 1. Graph Construction from Database
def test_graph_construction(graph_instance):
    assert isinstance(graph_instance, nx.MultiDiGraph)
    assert len(graph_instance.nodes()) == 3400
    assert len(graph_instance.edges()) > 0


# 2. Node Counts by Entity Type
def test_graph_node_counts(graph_instance):
    counts = {}
    for _, d in graph_instance.nodes(data=True):
        t = d.get("entity_type")
        counts[t] = counts.get(t, 0) + 1

    assert counts["customer"] == 500
    assert counts["account"] == 500
    assert counts["transaction"] == 2000
    assert counts["device"] == 100
    assert counts["ip"] == 150
    assert counts["beneficiary"] == 100
    assert counts["merchant"] == 50
    assert sum(counts.values()) == 3400


# 3. Edge Counts and Referential Integrity
def test_graph_edge_integrity(graph_instance):
    rel_counts = {}
    for u, v, k, d in graph_instance.edges(keys=True, data=True):
        # Assert endpoints exist
        assert u in graph_instance
        assert v in graph_instance
        rel = d.get("rel_type")
        assert rel is not None
        rel_counts[rel] = rel_counts.get(rel, 0) + 1

    expected_types = {
        "owns",
        "participates_in",
        "uses_device",
        "uses_ip",
        "involves_beneficiary",
        "involves_merchant",
        "sends_to",
        "transacts_with",
    }
    assert expected_types.issubset(set(rel_counts.keys()))
    assert rel_counts["owns"] == 500
    assert rel_counts["participates_in"] == 2000


# 4. Shared Device Discovery
def test_find_shared_devices(graph_instance):
    shared_devs = find_shared_devices(graph_instance, min_accounts=2)
    assert len(shared_devs) > 0

    top_dev = shared_devs[0]
    assert "device_id" in top_dev
    assert top_dev["account_count"] >= 2
    assert len(top_dev["accounts"]) == top_dev["account_count"]
    assert "fingerprint_hash" in top_dev
    assert "device_os" in top_dev


# 5. Shared IP Discovery
def test_find_shared_ips(graph_instance):
    shared_ips = find_shared_ips(graph_instance, min_accounts=2)
    assert len(shared_ips) > 0

    top_ip = shared_ips[0]
    assert "ip_id" in top_ip
    assert top_ip["account_count"] >= 2
    assert len(top_ip["accounts"]) == top_ip["account_count"]
    assert "ip_address" in top_ip
    assert "asn_org" in top_ip


# 6. Common Beneficiary Discovery
def test_find_common_beneficiaries(graph_instance):
    common_bens = find_common_beneficiaries(graph_instance, min_accounts=2)
    assert len(common_bens) > 0

    top_ben = common_bens[0]
    assert "beneficiary_id" in top_ben
    assert top_ben["account_count"] >= 2
    assert len(top_ben["accounts"]) == top_ben["account_count"]
    assert top_ben["total_amount"] > 0


# 7. Connected Accounts Discovery (2-hop)
def test_find_connected_accounts(graph_instance):
    sample_acc = "ACC_000001"
    connected = find_connected_accounts(graph_instance, sample_acc)
    assert isinstance(connected, list)
    if connected:
        peer = connected[0]
        assert "account_id" in peer
        assert peer["account_id"] != sample_acc
        assert "shared_entities" in peer
        assert len(peer["shared_entities"]) > 0


# 8. Account Neighbor Inspection
def test_get_account_neighbors(graph_instance):
    sample_acc = "ACC_000001"
    neighbors = get_account_neighbors(graph_instance, sample_acc)
    assert len(neighbors) > 0

    entity_types = {n["entity_type"] for n in neighbors}
    assert "customer" in entity_types
    assert "transaction" in entity_types or "device" in entity_types


# 9. Multi-Hop Pathway Traversal
def test_find_multi_hop_connections(graph_instance):
    shared_devs = find_shared_devices(graph_instance, min_accounts=2)
    src_acc = shared_devs[0]["accounts"][0]
    tgt_acc = shared_devs[0]["accounts"][1]

    paths = find_multi_hop_connections(graph_instance, src_acc, tgt_acc, max_hops=3)
    assert len(paths) > 0
    assert paths[0][0] == src_acc
    assert paths[0][-1] == tgt_acc


# 10. Transaction Relationship Tracing
def test_trace_transaction_relationships(graph_instance):
    sample_tx = "TXN_00000001"
    trace = trace_transaction_relationships(graph_instance, sample_tx)
    assert trace["transaction_id"] == sample_tx
    assert trace["account_id"] is not None
    assert trace["amount"] > 0
    assert len(trace["endpoints"]["devices"]) > 0
    assert len(trace["endpoints"]["ips"]) > 0

    # Test account trace
    sample_acc = "ACC_000001"
    acc_trace = trace_transaction_relationships(graph_instance, sample_acc)
    assert acc_trace["account_id"] == sample_acc
    assert "transactions" in acc_trace


# 11. Provenance and Timestamp Integrity
def test_relationship_provenance_and_timestamps(graph_instance):
    for _, _, _, data in graph_instance.edges(keys=True, data=True):
        assert "source_record" in data
        assert "rel_type" in data
        if data["rel_type"] in ["participates_in", "uses_device", "uses_ip"]:
            assert "timestamp" in data or "first_seen" in data


# 12. Graph Feature Extraction
def test_graph_feature_extractor(graph_instance):
    extractor = GraphFeatureExtractor(graph_instance)
    sample_feat = extractor.extract_account_features("ACC_000001")

    expected_keys = {
        "account_id",
        "scenario_type",
        "ground_truth_label",
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
    }
    assert expected_keys == set(sample_feat.keys())
    assert sample_feat["degree"] > 0

    # Extract all accounts (500)
    df_features = extractor.extract_all_account_features()
    assert len(df_features) == 500
    assert not df_features.isnull().any().any()


# 13. Target Leakage Prevention Regression Test
def test_target_leakage_prevention(graph_instance):
    extractor = GraphFeatureExtractor(graph_instance)
    pred_df = extractor.extract_predictive_features()

    # CRITICAL: Verify ground truth label and scenario type are completely excluded
    assert "ground_truth_label" not in pred_df.columns, "Target leakage detected: ground_truth_label in predictive features"
    assert "scenario_type" not in pred_df.columns, "Target leakage detected: scenario_type in predictive features"

    # Verify expected predictive feature columns
    for col in extractor.PREDICTIVE_FEATURE_COLUMNS:
        assert col in pred_df.columns, f"Missing predictive feature column: {col}"
    assert "account_id" in pred_df.columns
    assert len(pred_df) == 500

    # Verify metadata extraction is properly isolated
    meta_df = extractor.extract_account_metadata()
    assert set(meta_df.columns) == {"account_id", "scenario_type", "ground_truth_label"}
    assert len(meta_df) == 500

    # Verify convenience method
    p_df, m_df = extractor.extract_features_and_metadata()
    assert p_df.equals(pred_df)
    assert m_df.equals(meta_df)


# 14. Directed vs Discovery Traversal Integrity Test
def test_directed_vs_discovery_traversal_integrity(graph_instance):
    # 1. Underlying graph must remain strictly directed
    assert graph_instance.is_directed() is True

    shared_devs = find_shared_devices(graph_instance, min_accounts=2)
    dev_id = shared_devs[0]["device_id"]
    acc1 = shared_devs[0]["accounts"][0]
    acc2 = shared_devs[0]["accounts"][1]

    # 2. In the directed graph, account -> device edge exists, but NOT device -> account
    assert graph_instance.has_edge(acc1, dev_id) is True
    assert graph_instance.has_edge(dev_id, acc1) is False
    assert graph_instance.has_edge(acc2, dev_id) is True
    assert graph_instance.has_edge(dev_id, acc2) is False

    # 3. Discovery traversal finds symmetric relationship without creating reverse edges
    paths = find_multi_hop_connections(graph_instance, acc1, acc2, max_hops=3)
    assert len(paths) > 0

    # Underlying graph still has no reverse edge
    assert graph_instance.has_edge(dev_id, acc1) is False

    # 4. explain_multi_hop_path accurately identifies true directed edges and directions
    for path in paths[:3]:
        explained = explain_multi_hop_path(graph_instance, path)
        assert len(explained) == len(path) - 1
        for step in explained:
            u, v = step["from_node"], step["to_node"]
            assert step["direction"] in ["forward", "reverse"]
            assert step["rel_type"] is not None
            # The directed edge must truly exist in graph_instance
            d_src, d_tgt = step["directed_edge"]
            assert graph_instance.has_edge(d_src, d_tgt) is True


# 15. Deterministic Reproducibility
def test_deterministic_reproducibility():
    session = SessionLocal()
    try:
        builder = NetworkGraphBuilder(session=session)
        g_a = builder.build_graph()
        g_b = builder.build_graph()

        assert set(g_a.nodes()) == set(g_b.nodes())
        assert set(g_a.edges(keys=True)) == set(g_b.edges(keys=True))

        # Check random account feature equivalence
        ext_a = GraphFeatureExtractor(g_a)
        ext_b = GraphFeatureExtractor(g_b)
        feat_a = ext_a.extract_predictive_features()
        feat_b = ext_b.extract_predictive_features()
        assert feat_a.equals(feat_b)
    finally:
        session.close()
