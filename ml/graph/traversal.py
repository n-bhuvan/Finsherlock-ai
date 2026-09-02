"""RingGuard AI — NetworkX Graph Traversal & Query Operations.

Stage 4: NetworkX Graph Engine.
Provides reusable graph intelligence functions for detecting shared infrastructure,
common beneficiaries, connected accounts, multi-hop pathways, and transaction traces.
"""

from typing import Dict, List, Optional, Set, Any
import networkx as nx


def get_account_neighbors(
    graph: nx.MultiDiGraph,
    account_id: str,
    relation_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all neighboring entities directly linked to an account."""
    if account_id not in graph:
        raise KeyError(f"Account ID '{account_id}' not found in graph.")

    neighbors = []

    # Outgoing edges from account (e.g. participates_in, uses_device, uses_ip, sends_to, transacts_with)
    for u, v, k, data in graph.out_edges(account_id, keys=True, data=True):
        rel = data.get("rel_type")
        if relation_types and rel not in relation_types:
            continue
        target_attrs = dict(graph.nodes[v])
        neighbors.append({
            "direction": "out",
            "neighbor_id": v,
            "entity_type": target_attrs.get("entity_type"),
            "relation_type": rel,
            "edge_key": k,
            "edge_data": data,
            "node_attrs": target_attrs,
        })

    # Incoming edges to account (e.g. customer owns account)
    for u, v, k, data in graph.in_edges(account_id, keys=True, data=True):
        rel = data.get("rel_type")
        if relation_types and rel not in relation_types:
            continue
        source_attrs = dict(graph.nodes[u])
        neighbors.append({
            "direction": "in",
            "neighbor_id": u,
            "entity_type": source_attrs.get("entity_type"),
            "relation_type": rel,
            "edge_key": k,
            "edge_data": data,
            "node_attrs": source_attrs,
        })

    return neighbors


def find_shared_devices(
    graph: nx.MultiDiGraph, min_accounts: int = 2
) -> List[Dict[str, Any]]:
    """Discover devices connected to at least `min_accounts` distinct accounts."""
    shared = []

    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("entity_type") != "device":
            continue

        # Find accounts directly linked via uses_device
        connected_accounts = set()
        for u, v, k, data in graph.in_edges(node_id, keys=True, data=True):
            if data.get("rel_type") == "uses_device" and graph.nodes[u].get("entity_type") == "account":
                connected_accounts.add(u)

        if len(connected_accounts) >= min_accounts:
            shared.append({
                "device_id": node_id,
                "device_type": attrs.get("device_type"),
                "device_os": attrs.get("device_os"),
                "fingerprint_hash": attrs.get("fingerprint_hash"),
                "account_count": len(connected_accounts),
                "accounts": sorted(list(connected_accounts)),
            })

    # Sort descending by account count, then device_id
    shared.sort(key=lambda x: (-x["account_count"], x["device_id"]))
    return shared


def find_shared_ips(
    graph: nx.MultiDiGraph, min_accounts: int = 2
) -> List[Dict[str, Any]]:
    """Discover IP addresses connected to at least `min_accounts` distinct accounts."""
    shared = []

    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("entity_type") != "ip":
            continue

        connected_accounts = set()
        for u, v, k, data in graph.in_edges(node_id, keys=True, data=True):
            if data.get("rel_type") == "uses_ip" and graph.nodes[u].get("entity_type") == "account":
                connected_accounts.add(u)

        if len(connected_accounts) >= min_accounts:
            shared.append({
                "ip_id": node_id,
                "ip_address": attrs.get("ip_address"),
                "ip_type": attrs.get("ip_type"),
                "asn_org": attrs.get("asn_org"),
                "account_count": len(connected_accounts),
                "accounts": sorted(list(connected_accounts)),
            })

    shared.sort(key=lambda x: (-x["account_count"], x["ip_id"]))
    return shared


def find_common_beneficiaries(
    graph: nx.MultiDiGraph, min_accounts: int = 2
) -> List[Dict[str, Any]]:
    """Discover beneficiaries receiving funds from at least `min_accounts` distinct accounts."""
    common = []

    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("entity_type") != "beneficiary":
            continue

        connected_accounts = set()
        total_amount = 0.0

        for u, v, k, data in graph.in_edges(node_id, keys=True, data=True):
            if data.get("rel_type") == "sends_to" and graph.nodes[u].get("entity_type") == "account":
                connected_accounts.add(u)
                total_amount += data.get("total_amount", 0.0)

        if len(connected_accounts) >= min_accounts:
            common.append({
                "beneficiary_id": node_id,
                "beneficiary_type": attrs.get("beneficiary_type"),
                "bank_ifsc_prefix": attrs.get("bank_ifsc_prefix"),
                "account_count": len(connected_accounts),
                "total_amount": round(total_amount, 2),
                "accounts": sorted(list(connected_accounts)),
            })

    common.sort(key=lambda x: (-x["account_count"], -x["total_amount"], x["beneficiary_id"]))
    return common


def find_connected_accounts(
    graph: nx.MultiDiGraph,
    account_id: str,
    via_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Discover all accounts connected to `account_id` through 2-hop shared infrastructure.
    
    Traverses: (account) -> [shared_entity] <- (peer_account)
    """
    if account_id not in graph:
        raise KeyError(f"Account ID '{account_id}' not found in graph.")

    allowed_entities = set(via_types) if via_types else {"device", "ip", "beneficiary", "merchant"}
    connected: Dict[str, Dict[str, Any]] = {}

    # 1. Outgoing to shared entities (device, IP, beneficiary, merchant)
    for _, entity_id, _, edge_data in graph.out_edges(account_id, keys=True, data=True):
        ent_attrs = graph.nodes.get(entity_id, {})
        ent_type = ent_attrs.get("entity_type")
        if ent_type not in allowed_entities:
            continue

        # Inward edges to this entity from other accounts
        for peer_acc, _, _, peer_edge_data in graph.in_edges(entity_id, keys=True, data=True):
            if peer_acc == account_id or graph.nodes[peer_acc].get("entity_type") != "account":
                continue

            if peer_acc not in connected:
                connected[peer_acc] = {
                    "account_id": peer_acc,
                    "shared_entities": [],
                    "shared_entity_types": set(),
                }

            connected[peer_acc]["shared_entities"].append({
                "entity_id": entity_id,
                "entity_type": ent_type,
                "via_relation": edge_data.get("rel_type"),
            })
            connected[peer_acc]["shared_entity_types"].add(ent_type)

    # Convert sets to sorted lists
    results = []
    for peer_id, item in connected.items():
        results.append({
            "account_id": peer_id,
            "connection_count": len(item["shared_entities"]),
            "shared_types": sorted(list(item["shared_entity_types"])),
            "shared_entities": item["shared_entities"],
        })

    results.sort(key=lambda x: (-x["connection_count"], x["account_id"]))
    return results


def find_multi_hop_connections(
    graph: nx.MultiDiGraph,
    source_account_id: str,
    target_account_id: Optional[str] = None,
    max_hops: int = 3,
) -> List[List[str]]:
    """Traverse discovery paths up to `max_hops` between accounts.
    
    CRITICAL DESIGN NOTE (DIRECTED VS DISCOVERY TRAVERSAL):
    The underlying entity graph is strictly directed (e.g. account -> device, account -> transaction).
    However, financial abuse rings and shared infrastructure clusters are structurally uncovered
    by finding co-membership (e.g. Account A and Account B co-link to Device D).
    
    This function uses `graph.to_undirected(as_view=True)` as a read-only symmetric discovery projection.
    It does NOT create, duplicate, or mutate edges in the underlying MultiDiGraph.
    Use `explain_multi_hop_path()` to verify the exact directed edges, original direction, and provenance.
    """
    if source_account_id not in graph:
        raise KeyError(f"Source account '{source_account_id}' not found in graph.")

    # Create a read-only undirected view for symmetric relationship discovery
    undirected_G = graph.to_undirected(as_view=True)

    if target_account_id:
        if target_account_id not in graph:
            raise KeyError(f"Target account '{target_account_id}' not found in graph.")
        try:
            paths = list(
                nx.all_simple_paths(
                    undirected_G,
                    source=source_account_id,
                    target=target_account_id,
                    cutoff=max_hops,
                )
            )
            return paths
        except nx.NetworkXNoPath:
            return []
    else:
        lengths = nx.single_source_shortest_path_length(
            undirected_G, source=source_account_id, cutoff=max_hops
        )
        reachable = []
        for n, dist in lengths.items():
            if n != source_account_id and graph.nodes[n].get("entity_type") == "account":
                path = nx.shortest_path(undirected_G, source=source_account_id, target=n)
                reachable.append(path)
        reachable.sort(key=lambda p: (len(p), p[-1]))
        return reachable


def explain_multi_hop_path(
    graph: nx.MultiDiGraph, path: List[str]
) -> List[Dict[str, Any]]:
    """Deconstruct a multi-hop discovery path into its underlying directed edges.
    
    Validates that each hop corresponds to an actual edge in the MultiDiGraph,
    identifying whether the discovery traversal moved forward or reverse along the directed edge,
    and preserving relationship type and provenance without fabricating reverse edges.
    """
    explained_steps = []
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]

        # Check forward directed edge: u -> v
        if graph.has_edge(u, v):
            edge_dict = graph.get_edge_data(u, v)
            first_key = next(iter(edge_dict))
            edge_data = edge_dict[first_key]
            explained_steps.append({
                "from_node": u,
                "to_node": v,
                "directed_edge": (u, v),
                "direction": "forward",
                "rel_type": edge_data.get("rel_type"),
                "source_record": edge_data.get("source_record"),
                "timestamp": edge_data.get("timestamp") or edge_data.get("first_seen"),
            })
        # Check reverse directed edge: v -> u
        elif graph.has_edge(v, u):
            edge_dict = graph.get_edge_data(v, u)
            first_key = next(iter(edge_dict))
            edge_data = edge_dict[first_key]
            explained_steps.append({
                "from_node": u,
                "to_node": v,
                "directed_edge": (v, u),
                "direction": "reverse",
                "rel_type": edge_data.get("rel_type"),
                "source_record": edge_data.get("source_record"),
                "timestamp": edge_data.get("timestamp") or edge_data.get("first_seen"),
            })
        else:
            raise ValueError(f"No edge connects '{u}' and '{v}' in the underlying graph.")

    return explained_steps


def trace_transaction_relationships(
    graph: nx.MultiDiGraph, entity_id: str
) -> Dict[str, Any]:
    """Trace complete contextual flow for a transaction or account."""
    if entity_id not in graph:
        raise KeyError(f"Entity '{entity_id}' not found in graph.")

    attrs = graph.nodes[entity_id]
    etype = attrs.get("entity_type")

    if etype == "transaction":
        # Find origin account
        account_id = None
        for u, _, _, data in graph.in_edges(entity_id, keys=True, data=True):
            if data.get("rel_type") == "participates_in":
                account_id = u
                break

        # Find endpoints (device, IP, beneficiary, merchant)
        endpoints = {"devices": [], "ips": [], "beneficiaries": [], "merchants": []}
        for _, v, _, data in graph.out_edges(entity_id, keys=True, data=True):
            rel = data.get("rel_type")
            target_attrs = dict(graph.nodes[v])
            if rel == "uses_device":
                endpoints["devices"].append(v)
            elif rel == "uses_ip":
                endpoints["ips"].append(v)
            elif rel == "involves_beneficiary":
                endpoints["beneficiaries"].append(v)
            elif rel == "involves_merchant":
                endpoints["merchants"].append(v)

        return {
            "transaction_id": entity_id,
            "account_id": account_id,
            "amount": attrs.get("amount"),
            "timestamp": attrs.get("timestamp"),
            "scenario_type": attrs.get("scenario_type"),
            "ground_truth_label": attrs.get("ground_truth_label"),
            "endpoints": endpoints,
        }

    elif etype == "account":
        tx_nodes = []
        for _, v, _, data in graph.out_edges(entity_id, keys=True, data=True):
            if data.get("rel_type") == "participates_in":
                tx_attrs = dict(graph.nodes[v])
                tx_nodes.append({
                    "transaction_id": v,
                    "timestamp": tx_attrs.get("timestamp"),
                    "amount": tx_attrs.get("amount"),
                    "scenario_type": tx_attrs.get("scenario_type"),
                    "status": tx_attrs.get("status"),
                })
        tx_nodes.sort(key=lambda x: x["timestamp"])

        return {
            "account_id": entity_id,
            "customer_id": attrs.get("customer_id"),
            "scenario_type": attrs.get("scenario_type"),
            "ground_truth_label": attrs.get("ground_truth_label"),
            "transaction_count": len(tx_nodes),
            "transactions": tx_nodes,
        }
    else:
        raise ValueError(f"Trace requires transaction or account ID, got '{etype}'.")
