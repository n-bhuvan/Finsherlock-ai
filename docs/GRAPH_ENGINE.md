# RingGuard AI — NetworkX Graph Engine Specification & Architecture

> **Stage 4: NetworkX Graph Engine**  
> *In-Memory Multi-Relational Network Topology & Feature Engineering Infrastructure*

---

## 1. Overview & Purpose

The **RingGuard AI Graph Engine** constructs an in-memory, multi-relational entity network representing structural relationships across customers, bank accounts, financial transactions, endpoint hardware devices, network IP access points, recipient beneficiaries, and commercial merchants.

Built using **NetworkX 3.6+**, the graph engine serves as an infrastructure and feature-generation layer for downstream risk modeling (Stage 5 Feature Engineering and Stage 6 XGBoost Model). It operates in a **strictly read-only mode** against the Stage 3 PostgreSQL database.

---

## 2. Fundamental Safety & Non-Goals

> [!CAUTION]
> **Essential Safety Invariants:**
> 1. **No Autonomous Enforcement:** The graph engine performs analysis only. It never blocks payments, restricts accounts, moves funds, or alters database state.
> 2. **Shared Attributes Do NOT Equate to Fraud:** In legitimate environments, users legitimately share family devices, campus Wi-Fi / commercial broadband IPs, and utility merchants (e.g. `LEGITIMATE_LOOKALIKE` hard negatives). A shared device, shared IP, or common beneficiary **must not independently determine fraud**.
> 3. **No Target Leakage:** Graph-derived predictive feature matrices strictly exclude `scenario_type` and `ground_truth_label`.
> 4. **No Unverified Data / Zero Fabricated Edges:** Every node and relationship corresponds directly to an existing database record in PostgreSQL.

---

## 3. Technology & Dependencies

- **Graph Framework:** NetworkX (`networkx>=3.2.0,<4.0.0`, currently running v3.6.1)
- **Language & Runtime:** Python 3.13+
- **Data Preparation:** Pandas & NumPy
- **Persistence Source:** Read-only connection to PostgreSQL 18 via SQLAlchemy 2.0
- **Graph Type:** `networkx.MultiDiGraph` (directed multigraph preserving distinct transaction occurrences)

---

## 4. Node Types & Schema

The graph contains **3,400 nodes** across 7 distinct entity types:

| Entity Type | Node ID Format | Attributes Preserved | Provenance Reference |
|---|---|---|---|
| `customer` | `CUST_000001` | `name`, `email`, `phone_hash`, `risk_tier`, `created_at` | `customers.customer_id` |
| `account` | `ACC_000001` | `customer_id`, `created_at`, `status`, `account_type`, `scenario_id`, `scenario_type`, `ground_truth_label` | `accounts.account_id` |
| `transaction` | `TXN_00000001` | `account_id`, `timestamp`, `amount`, `transaction_type`, `status`, `channel`, `scenario_id`, `scenario_type`, `ground_truth_label` | `transactions.transaction_id` |
| `device` | `DEV_000001` | `device_type`, `os`, `fingerprint_hash`, `created_at` | `devices.device_id` |
| `ip` | `IP_000001` | `ip_address`, `ip_type`, `asn_org`, `country` | `ips.ip_id` |
| `beneficiary` | `BEN_000001` | `beneficiary_type`, `bank_ifsc_prefix`, `account_hash` | `beneficiaries.beneficiary_id` |
| `merchant` | `MER_000001` | `merchant_category`, `merchant_name`, `merchant_risk_rating` | `merchants.merchant_id` |

---

## 5. Relationship Types, Directions & Semantics

The graph contains **11,814 directed edges** categorized into two complementary tiers:
1. **Granular Transaction Links:** Capturing precise financial chronology.
2. **Direct Bipartite Links:** Capturing aggregated account interaction channels.

```
                         ┌──────────────┐
                         │   customer   │
                         └──────┬───────┘
                                │ owns
                                ▼
                         ┌──────────────┐
     ┌───────────────────┤   account    ├───────────────────┐
     │                   └──────┬───────┘                   │
     │ transacts_with           │ participates_in           │ sends_to
     ▼                          ▼                           ▼
┌──────────┐ uses_device ┌─────────────┐ uses_ip      ┌───────────┐
│ merchant │◄────────────┤ transaction ├─────────────►│    ip     │
└──────────┘             └──────┬──────┘              └───────────┘
                                │ involves_beneficiary
                                ▼
                         ┌──────────────┐
                         │ beneficiary  │
                         └──────────────┘
```

### Relationship Catalog:

| Relationship Type | Source Entity | Target Entity | Edge Count | Key Attributes |
|---|---|---|---|---|
| `owns` | `customer` | `account` | 500 | `created_at`, `source_record` |
| `participates_in` | `account` | `transaction` | 2,000 | `timestamp`, `amount`, `status`, `source_record` |
| `uses_device` (tx) | `transaction` | `device` | 2,000 | `timestamp`, `source_record` |
| `uses_device` (acc) | `account` | `device` | 759 | `transaction_count`, `first_seen`, `last_seen`, `tx_ids` |
| `uses_ip` (tx) | `transaction` | `ip` | 2,000 | `timestamp`, `source_record` |
| `uses_ip` (acc) | `account` | `ip` | 734 | `transaction_count`, `first_seen`, `last_seen`, `tx_ids` |
| `involves_beneficiary` | `transaction` | `beneficiary` | 754 | `timestamp`, `amount`, `source_record` |
| `sends_to` | `account` | `beneficiary` | 613 | `transaction_count`, `total_amount`, `first_seen`, `last_seen` |
| `involves_merchant` | `transaction` | `merchant` | 1,246 | `timestamp`, `amount`, `source_record` |
| `transacts_with` | `account` | `merchant` | 1,208 | `transaction_count`, `total_amount`, `first_seen`, `last_seen` |

---

## 6. Directed vs. Discovery Traversal Behavior

### Strict Underlying Direction
The entity graph is strictly directed. Causality and funds flow outward:
- Accounts own transactions (`account -> transaction`).
- Transactions use devices and IPs (`transaction -> device`, `transaction -> ip`).
- Devices and IPs never originate transactions; no reverse edges are fabricated in the database or `MultiDiGraph`.

### Undirected Relationship Discovery Projection
To detect **co-membership**, **syndicate hubs**, and **abuse rings**, fraud investigations search for shared infrastructure (e.g. Account A and Account B are connected because both point to Device D).

The function `find_multi_hop_connections()` creates a temporary, read-only symmetric discovery view:
```python
undirected_view = graph.to_undirected(as_view=True)
```
- **Invariant:** No reverse edges are created or added to the underlying `MultiDiGraph`.
- **Explainability:** Callers can use `explain_multi_hop_path(graph, path)` to inspect any multi-hop discovery sequence and deconstruct every hop into its true underlying directed edge, original direction (`forward` vs `reverse`), relationship type, and timestamp.

---

## 7. Traversal Query API (`ml/graph/traversal.py`)

- `get_account_neighbors(graph, account_id, relation_types=None)`: Retrieves inward and outward neighbors directly linked to an account.
- `find_shared_devices(graph, min_accounts=2)`: Discovers devices used across 2 or more distinct accounts.
- `find_shared_ips(graph, min_accounts=2)`: Discovers IPs used across 2 or more distinct accounts.
- `find_common_beneficiaries(graph, min_accounts=2)`: Discovers beneficiaries receiving funds from 2 or more distinct accounts.
- `find_connected_accounts(graph, account_id)`: Discovers 2-hop connected accounts via shared infrastructure.
- `find_multi_hop_connections(graph, source, target, max_hops=3)`: Traverses simple paths between accounts across shared infrastructure.
- `explain_multi_hop_path(graph, path)`: Deconstructs paths into directed edges with relationship types and directions.
- `trace_transaction_relationships(graph, entity_id)`: Reconstructs the full contextual graph neighborhood for a transaction or account.

---

## 8. Graph Feature Engineering & Target Leakage Prevention

Downstream Machine Learning (Stage 5/6) consumes topological metrics extracted by `GraphFeatureExtractor` ([ml/graph/features.py](file:///c:/Users/bhuva/Desktop/Finsherlock/ml/graph/features.py)).

### Strict Target Leakage Isolation

To prevent target leakage, the extractor strictly decouples predictive features from ground-truth labels and scenario provenance:

```
GraphFeatureExtractor
 ├── extract_predictive_features()  ──► DataFrame [500 rows x 23 cols: account_id + 22 predictive features]
 └── extract_account_metadata()     ──► DataFrame [500 rows x 3 cols: account_id, scenario_type, ground_truth_label]
```

### 1. Account Metadata & Labels (`METADATA_COLUMNS`):
- `account_id`
- `scenario_type` *(ground-truth provenance, excluded from training)*
- `ground_truth_label` *(target variable, excluded from training)*

### 2. Predictive Features (`PREDICTIVE_FEATURE_COLUMNS`):
- **Degree Centrality:** `degree`, `in_degree`, `out_degree`
- **Endpoint Diversity:** `device_count`, `ip_count`, `beneficiary_count`, `merchant_count`
- **Neighborhood Density:** `connected_accounts_count`, `shared_device_accounts_count`, `shared_ip_accounts_count`, `shared_beneficiary_accounts_count`
- **Sharing Indicators:** `has_shared_device`, `has_shared_ip`, `has_common_beneficiary`
- **Sharing Depth:** `max_device_sharing_degree`, `max_ip_sharing_degree`, `max_beneficiary_sharing_degree`
- **Transaction Dynamics:** `tx_count`, `total_tx_amount`, `avg_tx_amount`
- **Community Topology:** `component_id`, `component_size`

---

## 9. Determinism & Reproducibility

- The graph builder sorts records deterministically during construction.
- Rebuilding the graph against the same PostgreSQL database produces **100% identical node sets, edge sets, edge attributes, and feature matrices**.
