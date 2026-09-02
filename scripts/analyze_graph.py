#!/usr/bin/env python3
"""RingGuard AI — Graph Engine Analysis & Verification CLI.

Stage 4: NetworkX Graph Engine.
Constructs the entity graph, validates reproducibility, displays node/edge metrics,
and demonstrates shared-attribute intelligence queries.
"""

import sys
from pathlib import Path

# Ensure repository root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from ml.graph.builder import NetworkGraphBuilder
from ml.graph.traversal import (
    find_shared_devices,
    find_shared_ips,
    find_common_beneficiaries,
    find_connected_accounts,
    find_multi_hop_connections,
    explain_multi_hop_path,
    trace_transaction_relationships,
)
from ml.graph.features import GraphFeatureExtractor


def main():
    print("=" * 70)
    print("RINGGUARD AI -- GRAPH ENGINE ANALYSIS (STAGE 4)")
    print("=" * 70)

    # 1. Build Graph from PostgreSQL
    session = SessionLocal()
    try:
        builder = NetworkGraphBuilder(session=session)
        print("\n[INFO] Loading Stage 3 PostgreSQL data and building NetworkX graph...")
        G1 = builder.build_graph()

        # Check reproducibility
        print("[INFO] Building second instance to verify deterministic reproducibility...")
        G2 = builder.build_graph()

        nodes_match = set(G1.nodes()) == set(G2.nodes())
        edges_match = set(G1.edges(keys=True)) == set(G2.edges(keys=True))
        reproducible = nodes_match and edges_match
        print(f"[REPRODUCIBILITY] Nodes match: {nodes_match}, Edges match: {edges_match} -> {'PASS' if reproducible else 'FAIL'}")

    finally:
        session.close()

    # 2. Node Counts by Entity Type
    node_counts = {}
    for _, d in G1.nodes(data=True):
        t = d.get("entity_type", "unknown")
        node_counts[t] = node_counts.get(t, 0) + 1

    print("\n" + "-" * 40)
    print("GRAPH NODE COUNTS BY ENTITY TYPE:")
    print("-" * 40)
    total_nodes = len(G1.nodes())
    for etype in ["customer", "account", "transaction", "device", "ip", "beneficiary", "merchant"]:
        print(f"  - {etype:15s}: {node_counts.get(etype, 0):,}")
    print(f"  Total Nodes      : {total_nodes:,}")

    # 3. Edge Counts by Relationship Type
    edge_counts = {}
    for _, _, _, d in G1.edges(keys=True, data=True):
        rel = d.get("rel_type", "unknown")
        edge_counts[rel] = edge_counts.get(rel, 0) + 1

    print("\n" + "-" * 40)
    print("GRAPH EDGE COUNTS BY RELATION TYPE:")
    print("-" * 40)
    total_edges = len(G1.edges())
    for rtype in sorted(edge_counts.keys()):
        print(f"  - {rtype:22s}: {edge_counts[rtype]:,}")
    print(f"  Total Edges           : {total_edges:,}")

    # 4. Example Shared-Device Relationship
    shared_devs = find_shared_devices(G1, min_accounts=2)
    print("\n" + "-" * 40)
    print(f"DISCOVERED SHARED DEVICES ({len(shared_devs)} devices shared across >=2 accounts):")
    print("-" * 40)
    if shared_devs:
        ex_dev = shared_devs[0]
        print(f"  Example Device ID : {ex_dev['device_id']}")
        print(f"  Type / OS         : {ex_dev['device_type']} ({ex_dev['device_os']})")
        print(f"  Connected Accounts: {ex_dev['account_count']} accounts -> {ex_dev['accounts'][:5]}...")

    # 5. Example Shared-IP Relationship
    shared_ips = find_shared_ips(G1, min_accounts=2)
    print("\n" + "-" * 40)
    print(f"DISCOVERED SHARED IPS ({len(shared_ips)} IPs shared across >=2 accounts):")
    print("-" * 40)
    if shared_ips:
        ex_ip = shared_ips[0]
        print(f"  Example IP ID     : {ex_ip['ip_id']} ({ex_ip['ip_address']})")
        print(f"  Type / ASN        : {ex_ip['ip_type']} ({ex_ip['asn_org']})")
        print(f"  Connected Accounts: {ex_ip['account_count']} accounts -> {ex_ip['accounts'][:5]}...")

    # 6. Example Common-Beneficiary Relationship
    common_bens = find_common_beneficiaries(G1, min_accounts=2)
    print("\n" + "-" * 40)
    print(f"DISCOVERED COMMON BENEFICIARIES ({len(common_bens)} beneficiaries received funds from >=2 accounts):")
    print("-" * 40)
    if common_bens:
        ex_ben = common_bens[0]
        print(f"  Example Ben ID    : {ex_ben['beneficiary_id']}")
        print(f"  Type / Bank IFSC  : {ex_ben['beneficiary_type']} ({ex_ben['bank_ifsc_prefix']})")
        print(f"  Connected Accounts: {ex_ben['account_count']} accounts -> {ex_ben['accounts'][:5]}...")
        print(f"  Total Received    : INR {ex_ben['total_amount']:,.2f}")

    # 7. Example Multi-Hop Relationship
    print("\n" + "-" * 40)
    print("EXAMPLE MULTI-HOP RELATIONSHIP PATHWAY:")
    print("-" * 40)
    if shared_devs and len(shared_devs[0]["accounts"]) >= 2:
        src_acc = shared_devs[0]["accounts"][0]
        tgt_acc = shared_devs[0]["accounts"][1]
        paths = find_multi_hop_connections(G1, src_acc, tgt_acc, max_hops=3)
        if paths:
            print(f"  Discovery path between {src_acc} and {tgt_acc}:")
            for p in paths[:1]:
                print(f"    Path: {' -> '.join(p)}")
                explained = explain_multi_hop_path(G1, p)
                print("    Underlying directed edges & provenance:")
                for step in explained:
                    print(f"      - {step['from_node']} -> {step['to_node']} (edge: {step['directed_edge']}, dir: {step['direction']}, rel: {step['rel_type']})")

    # 8. Feature Extraction Sample (Target Leakage Isolated)
    extractor = GraphFeatureExtractor(G1)
    df_pred, df_meta = extractor.extract_features_and_metadata()
    print("\n" + "-" * 40)
    print("GRAPH FEATURE EXTRACTION FOR ML (LEAKAGE ISOLATED):")
    print("-" * 40)
    print(f"  Predictive Features Shape : {df_pred.shape} (strictly no labels/scenarios)")
    print(f"  Predictive Feature Columns: {list(df_pred.columns[1:])}")
    print(f"  Metadata / Labels Shape   : {df_meta.shape}")
    print(f"  Metadata Columns          : {list(df_meta.columns)}")
    print(f"  Accounts with shared devices: {df_pred['has_shared_device'].sum()} / 500")
    print(f"  Accounts with shared IPs    : {df_pred['has_shared_ip'].sum()} / 500")
    print(f"  Accounts with shared ben    : {df_pred['has_common_beneficiary'].sum()} / 500")

    print("\n" + "=" * 70)
    print("GRAPH ENGINE VERIFICATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
