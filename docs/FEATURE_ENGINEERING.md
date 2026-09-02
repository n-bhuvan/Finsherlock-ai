# RingGuard AI — Feature Engineering Specification

> **Stage 5: Feature Engineering**  
> *Leakage-Safe, Point-in-Time Behavioral, Transaction & Graph Feature Pipelines*

---

## 1. Overview & Objectives

In Stage 5, RingGuard AI establishes the machine learning feature engineering infrastructure. It extracts point-in-time transaction properties, account behavioral dynamics, and incremental NetworkX graph features from the Stage 3 PostgreSQL database.

The pipeline produces two strictly aligned datasets for downstream comparative experiments:
- **MODEL A:** Transaction-level features + Behavioral features only (Baseline model).
- **MODEL B:** Transaction-level features + Behavioral features + Point-in-Time Graph features (Network-aware model).

---

## 2. Core Safety & Leakage Prevention Rules

> [!CAUTION]
> **Strict Machine Learning Invariants:**
> 1. **Zero Target Leakage:** Neither `ground_truth_label`, `scenario_type`, `scenario_id`, nor binary target indicators (`is_ring`) ever enter predictive feature matrices. They are isolated in a separate `target_metadata.csv` contract.
> 2. **Point-in-Time Temporal Safety ($t \le T$):** For any transaction at time $T$, all historical, behavioral, and graph features are computed strictly using information established at or before $T$. Future events ($t > T$) have **zero influence** on past features.
> 3. **Identifier Isolation:** `account_id` and `transaction_id` are primary indexes / join keys, never numeric or predictive model features.
> 4. **Identical Row Ordering & Indexing:** Model A, Model B, and target metadata share 100% identical transaction ordering and indexing, guaranteeing fair, controlled evaluation in Stages 6 and 7.

---

## 3. Feature Catalog & Specifications

### A. Transaction Features (15 Features)
Instantaneous attributes directly observable on the incoming transaction event $T$:

| Feature Name | Source Column / Table | Calculation / Logic | Temporal Semantics |
|---|---|---|---|
| `tx_amount` | `transactions.amount` | Raw monetary value (INR) | Instantaneous ($t = T$) |
| `tx_log_amount` | `transactions.amount` | $\log(1 + \text{amount})$ | Instantaneous ($t = T$) |
| `tx_hour` | `transactions.timestamp` | Hour of day ($0\text{--}23$) | Instantaneous ($t = T$) |
| `tx_day_of_week` | `transactions.timestamp` | Day of week ($0 = \text{Mon}, 6 = \text{Sun}$) | Instantaneous ($t = T$) |
| `tx_day_of_month` | `transactions.timestamp` | Day of month ($1\text{--}31$) | Instantaneous ($t = T$) |
| `tx_is_weekend` | `transactions.timestamp` | $1$ if Saturday or Sunday, else $0$ | Instantaneous ($t = T$) |
| `tx_is_night` | `transactions.timestamp` | $1$ if hour $\in [0, 5]$, else $0$ | Instantaneous ($t = T$) |
| `tx_is_transfer_p2p`| `transactions.transaction_type`| $1$ if `TRANSFER_P2P`, else $0$ | Instantaneous ($t = T$) |
| `tx_is_payment_p2m` | `transactions.transaction_type`| $1$ if `PAYMENT_P2M`, else $0$ | Instantaneous ($t = T$) |
| `tx_channel_upi` | `transactions.channel` | $1$ if `UPI`, else $0$ | Instantaneous ($t = T$) |
| `tx_channel_imps` | `transactions.channel` | $1$ if `IMPS`, else $0$ | Instantaneous ($t = T$) |
| `tx_channel_card` | `transactions.channel` | $1$ if `CARD`, else $0$ | Instantaneous ($t = T$) |
| `tx_channel_netbanking` | `transactions.channel`| $1$ if `NETBANKING`, else $0$ | Instantaneous ($t = T$) |
| `tx_has_beneficiary`| `transactions.beneficiary_id`| $1$ if beneficiary present, else $0$| Instantaneous ($t = T$) |
| `tx_has_merchant` | `transactions.merchant_id` | $1$ if merchant present, else $0$ | Instantaneous ($t = T$) |

---

### B. Point-in-Time Behavioral Features (22 Features)
Historical baseline and rolling velocity features computed strictly over prior transactions ($t < T$):

| Feature Name | Source | Calculation / Formula | Temporal Rule |
|---|---|---|---|
| `beh_account_age_days` | `accounts.account_created_at` | $(T - \text{created\_at}) / 86400$ | Point-in-time at $T$ |
| `beh_tx_sequence_num` | Transaction sequence | Ordinal index of transaction for this account | Historical ($1, 2, 3\dots$) |
| `beh_time_since_last_tx_sec` | Prior transaction | $(T - T_{\text{prev}})$ in seconds ($-1.0$ if first tx) | Prior transaction ($t < T$) |
| `beh_is_first_tx` | Transaction sequence | $1$ if first transaction for account, else $0$ | Point-in-time at $T$ |
| `beh_hist_tx_count` | Prior transactions | Count of prior transactions | Strictly prior ($t < T$) |
| `beh_hist_total_amount` | Prior transactions | Sum of amounts of prior transactions | Strictly prior ($t < T$) |
| `beh_hist_avg_amount` | Prior transactions | Mean amount of prior transactions ($0.0$ if none) | Strictly prior ($t < T$) |
| `beh_hist_max_amount` | Prior transactions | Max amount of prior transactions ($0.0$ if none) | Strictly prior ($t < T$) |
| `beh_hist_std_amount` | Prior transactions | Sample standard deviation of prior amounts | Strictly prior ($t < T$) |
| `beh_amount_to_hist_avg_ratio`| Prior transactions | $\text{tx\_amount} / (\text{hist\_avg} + 10^{-5})$ | Current vs prior |
| `beh_rolling_tx_count_1h`| Prior transactions | Count of transactions in $[T - 1\text{h}, T)$ | 1-hour window |
| `beh_rolling_amount_1h` | Prior transactions | Sum of amounts in $[T - 1\text{h}, T)$ | 1-hour window |
| `beh_rolling_tx_count_24h`| Prior transactions | Count of transactions in $[T - 24\text{h}, T)$ | 24-hour window |
| `beh_rolling_amount_24h`| Prior transactions | Sum of amounts in $[T - 24\text{h}, T)$ | 24-hour window |
| `beh_rolling_tx_count_7d` | Prior transactions | Count of transactions in $[T - 7\text{d}, T)$ | 7-day window |
| `beh_rolling_amount_7d` | Prior transactions | Sum of amounts in $[T - 7\text{d}, T)$ | 7-day window |
| `beh_hist_unique_devices`| Prior transactions | Distinct devices used by account before $T$ | Strictly prior ($t < T$) |
| `beh_hist_unique_ips` | Prior transactions | Distinct IPs used by account before $T$ | Strictly prior ($t < T$) |
| `beh_hist_unique_beneficiaries`| Prior transactions | Distinct beneficiaries sent to before $T$ | Strictly prior ($t < T$) |
| `beh_is_new_device` | Prior transactions | $1$ if device was never used before $T$, else $0$ | Novelty at $T$ |
| `beh_is_new_ip` | Prior transactions | $1$ if IP was never used before $T$, else $0$ | Novelty at $T$ |
| `beh_is_new_beneficiary`| Prior transactions | $1$ if beneficiary was never sent to before $T$| Novelty at $T$ |

---

### C. Point-in-Time Graph Features (21 Features)
Topological network features derived from an incremental NetworkX graph containing only entities and transactions established at or before time $T$ ($t \le T$):

| Feature Name | Source | Description | Point-in-Time Rule |
|---|---|---|---|
| `g_degree` | Incremental graph | Total degree of account in $G_T$ | Evaluated at $G_T$ |
| `g_in_degree` | Incremental graph | In-degree of account in $G_T$ | Evaluated at $G_T$ |
| `g_out_degree` | Incremental graph | Out-degree of account in $G_T$ | Evaluated at $G_T$ |
| `g_device_count` | Incremental graph | Number of devices linked to account in $G_T$ | Evaluated at $G_T$ |
| `g_ip_count` | Incremental graph | Number of IPs linked to account in $G_T$ | Evaluated at $G_T$ |
| `g_beneficiary_count` | Incremental graph | Number of beneficiaries linked to account in $G_T$ | Evaluated at $G_T$ |
| `g_merchant_count` | Incremental graph | Number of merchants linked to account in $G_T$ | Evaluated at $G_T$ |
| `g_connected_accounts_count`| Incremental graph | Peer accounts sharing any endpoint in $G_T$ | Evaluated at $G_T$ |
| `g_shared_device_accounts_count`| Incremental graph | Peer accounts sharing a device in $G_T$ | Evaluated at $G_T$ |
| `g_shared_ip_accounts_count`| Incremental graph | Peer accounts sharing an IP in $G_T$ | Evaluated at $G_T$ |
| `g_shared_beneficiary_accounts_count`| Incremental graph | Peer accounts sharing a beneficiary in $G_T$| Evaluated at $G_T$ |
| `g_has_shared_device` | Incremental graph | $1$ if shared device accounts $> 0$, else $0$ | Evaluated at $G_T$ |
| `g_has_shared_ip` | Incremental graph | $1$ if shared IP accounts $> 0$, else $0$ | Evaluated at $G_T$ |
| `g_has_common_beneficiary`| Incremental graph | $1$ if shared beneficiary accounts $> 0$, else $0$| Evaluated at $G_T$ |
| `g_max_device_sharing_degree`| Incremental graph | Max accounts on any device used by account in $G_T$| Evaluated at $G_T$ |
| `g_max_ip_sharing_degree`| Incremental graph | Max accounts on any IP used by account in $G_T$ | Evaluated at $G_T$ |
| `g_max_beneficiary_sharing_degree`| Incremental graph| Max accounts on any beneficiary in $G_T$ | Evaluated at $G_T$ |
| `g_tx_count` | Incremental graph | Transactions originated by account in $G_T$ | Evaluated at $G_T$ |
| `g_total_tx_amount` | Incremental graph | Total volume originated by account in $G_T$ | Evaluated at $G_T$ |
| `g_avg_tx_amount` | Incremental graph | Mean amount originated by account in $G_T$ | Evaluated at $G_T$ |
| `g_component_size` | Incremental graph | Size of connected component containing account in $G_T$| Evaluated at $G_T$ |

---

## 4. Model A and Model B Feature Contracts

### Model A: Baseline Feature Matrix
- **Scope:** Transaction Features (15) + Behavioral Features (22) = **37 Features**
- **Dimensions:** 2,000 rows × 37 columns
- **Purpose:** Represents conventional payment fraud detection systems that analyze individual transaction attributes and local account histories without cross-entity network awareness.

### Model B: Network-Aware Feature Matrix
- **Scope:** Model A Features (37) + Point-in-Time Graph Features (21) = **58 Features**
- **Dimensions:** 2,000 rows × 58 columns
- **Purpose:** Evaluates the incremental predictive value of network and community topology for detecting coordinated payment abuse rings.

### Target & Metadata Contract
- **File:** `target_metadata.csv`
- **Columns:** `transaction_id` (Index), `account_id`, `timestamp`, `scenario_type`, `ground_truth_label`, `is_ring` (binary integer: $1$ if `ground_truth_label == 'ring'` else $0$)
- **Row Count:** 2,000 rows aligned 1:1 with Model A and Model B.

---

## 5. Point-in-Time Temporal Correctness Proof

The temporal integrity of the pipeline is mathematically verified by two automated regression tests:
1. `test_point_in_time_behavioral_safety`: Truncating the dataset to the first 500 transactions produces **100% identical behavioral features** to those produced when all 2,000 transactions are processed.
2. `test_point_in_time_graph_safety`: Truncating the dataset to the first 300 transactions produces **100% identical graph features** to those produced when all 2,000 transactions are processed.

This guarantees that future transactions ($t > T$) have **zero impact** on earlier transactions.

---

## 6. Missing Value & Sentinel Strategy

- **First Transactions:** Accounts executing their first transaction have no prior historical transactions.
  - `beh_time_since_last_tx_sec`: Assigned sentinel value `-1.0`.
  - `beh_is_first_tx`: Assigned `1` (allowing tree models to easily split on this boundary).
  - `beh_hist_avg_amount`, `beh_hist_max_amount`, `beh_hist_std_amount`: Assigned `0.0`.
  - `beh_amount_to_hist_avg_ratio`: Assigned `1.0`.
- **Zero-Imputation for Initial Velocity:** Rolling window counts and totals default to `0` / `0.0` when no transactions fall in the window.
- **Audit Verification:** Total NaNs = 0, Total Infinities = 0 across both Model A and Model B.

---

## 7. Artifacts Generated (`ml/data/features/`)

```
ml/data/features/
├── model_a_features.csv    # 2,000 rows x 37 columns
├── model_b_features.csv    # 2,000 rows x 58 columns
├── target_metadata.csv     # 2,000 rows x 5 columns
└── feature_manifest.json   # Full schema, types, stats, and integrity audit
```
