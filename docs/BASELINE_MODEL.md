# RingGuard AI — Baseline Model Specification (Model A)

> **Stage 6: Transaction-Only Baseline XGBoost**  
> *Non-Network Machine Learning Baseline for Comparative Payment Risk Detection*

---

## 1. Objective & Purpose

Stage 6 establishes the primary machine learning benchmark for RingGuard AI: **Model A**.
Model A is trained strictly on **transaction-level and behavioral account features** (37 features), with graph and network intelligence intentionally excluded.

> [!IMPORTANT]
> **Core Architectural Purpose:**
> Stage 6 establishes the transaction + behavior baseline. Stage 7 will add point-in-time graph features (Model B) and compare incremental predictive value to quantify the specific impact of network intelligence.

---

## 2. Prediction Unit & Dataset Inputs

- **Prediction Unit:** **TRANSACTION** (each prediction row corresponds to exactly one payment transaction at its execution timestamp).
- **Input Datasets:**
  - `ml/data/features/model_a_features.csv` (2,000 rows × 37 predictive features)
  - `ml/data/features/target_metadata.csv` (2,000 rows × 5 metadata/target columns)
- **Target Variable:** `is_ring` (binary integer: $1$ for `ring` / positive class, $0$ for `legitimate` / negative class).
- **Excluded Datasets:** `ml/data/features/model_b_features.csv` is strictly unused in Stage 6.

---

## 3. Feature Set Specification

Model A utilizes exactly **37 predictive features**:

### A. Transaction Features (15):
`tx_amount`, `tx_log_amount`, `tx_hour`, `tx_day_of_week`, `tx_day_of_month`, `tx_is_weekend`, `tx_is_night`, `tx_is_transfer_p2p`, `tx_is_payment_p2m`, `tx_channel_upi`, `tx_channel_imps`, `tx_channel_card`, `tx_channel_netbanking`, `tx_has_beneficiary`, `tx_has_merchant`.

### B. Point-in-Time Behavioral Features (22):
`beh_account_age_days`, `beh_tx_sequence_num`, `beh_time_since_last_tx_sec`, `beh_is_first_tx`, `beh_hist_tx_count`, `beh_hist_total_amount`, `beh_hist_avg_amount`, `beh_hist_max_amount`, `beh_hist_std_amount`, `beh_amount_to_hist_avg_ratio`, `beh_rolling_tx_count_1h`, `beh_rolling_amount_1h`, `beh_rolling_tx_count_24h`, `beh_rolling_amount_24h`, `beh_rolling_tx_count_7d`, `beh_rolling_amount_7d`, `beh_hist_unique_devices`, `beh_hist_unique_ips`, `beh_hist_unique_beneficiaries`, `beh_is_new_device`, `beh_is_new_ip`, `beh_is_new_beneficiary`.

### C. Excluded Features & Target Isolation:
- **Graph Features (21):** Zero graph features are included (`g_*` columns strictly excluded).
- **Target Labels:** `ground_truth_label`, `scenario_type`, `scenario_id`, and `is_ring` strictly isolated in `target_metadata.csv`.
- **Entity Identifiers:** `transaction_id` is used solely as the DataFrame row index; `account_id`, `customer_id`, `device_id`, `ip_id`, `beneficiary_id`, and `merchant_id` are strictly excluded from predictive features.

---

## 4. Chronological Splitting Strategy

To prevent temporal data leakage, transactions are partitioned strictly chronologically:

| Split | Rows | Ratio | Start Timestamp | End Timestamp | Ring (Pos) | Legit (Neg) | Positive Rate |
|---|---|---|---|---|---|---|---|
| **TRAIN** | 1,400 | 70% | 2025-12-31 19:10:18+00:00 | 2026-02-12 00:49:53+00:00 | 152 | 1,248 | 10.86% |
| **VALIDATION** | 300 | 15% | 2026-02-12 00:50:03+00:00 | 2026-02-20 19:51:24+00:00 | 55 | 245 | 18.33% |
| **HELD-OUT TEST**| 300 | 15% | 2026-02-20 20:54:48+00:00 | 2026-03-01 17:45:54+00:00 | 26 | 274 | 8.67% |
| **TOTAL** | 2,000 | 100% | 2025-12-31 19:10:18+00:00 | 2026-03-01 17:45:54+00:00 | 233 | 1,767 | 11.65% |

- The **HELD-OUT TEST** set is never used for training, hyperparameter tuning, or threshold selection.
- All split index sets are completely disjoint ($Train \cap Val = \emptyset$, $Val \cap Test = \emptyset$, $Train \cap Test = \emptyset$).

---

## 5. Class Imbalance Handling

- Imbalance ratio is calculated strictly on the **Training set**:
  $$\text{scale\_pos\_weight} = \frac{\text{Negative Count}}{\text{Positive Count}} = \frac{1,248}{152} \approx 8.2105$$
- Validation and test labels are never used to compute training parameters.
- No synthetic oversampling (e.g. SMOTE) is applied to preserve genuine empirical transaction distributions.

---

## 6. Model Hyperparameters & Configuration

```python
XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    scale_pos_weight=8.2105,
    random_state=20260903,
    n_jobs=-1,
)
```

---

## 7. Performance & Evaluation Metrics

Evaluated at fixed baseline threshold $0.5$:

| Metric | TRAIN (1,400 rows) | VALIDATION (300 rows) | HELD-OUT TEST (300 rows) |
|---|---|---|---|
| **PR-AUC (Primary)** | **1.0000** | **1.0000** | **1.0000** |
| **Precision** | **1.0000** | **1.0000** | **1.0000** |
| **Recall** | **1.0000** | **1.0000** | **1.0000** |
| **F1 Score** | **1.0000** | **1.0000** | **1.0000** |
| **ROC-AUC** | **1.0000** | **1.0000** | **1.0000** |
| **False Positive Rate**| **0.0000** | **0.0000** | **0.0000** |
| **Confusion Matrix** | TP=152, FP=0, TN=1248, FN=0 | TP=55, FP=0, TN=245, FN=0 | TP=26, FP=0, TN=274, FN=0 |

---

## 8. Feature Importances (Top 10)

| Rank | Feature Name | Importance (Gain) | Category |
|---|---|---|---|
| 1 | `tx_log_amount` | 0.3776 | Transaction |
| 2 | `tx_amount` | 0.3147 | Transaction |
| 3 | `beh_hist_avg_amount` | 0.2001 | Behavioral |
| 4 | `tx_day_of_month` | 0.0236 | Transaction |
| 5 | `beh_rolling_amount_24h` | 0.0233 | Behavioral |
| 6 | `tx_is_transfer_p2p` | 0.0180 | Transaction |
| 7 | `tx_day_of_week` | 0.0149 | Transaction |
| 8 | `tx_channel_imps` | 0.0099 | Transaction |
| 9 | `beh_time_since_last_tx_sec`| 0.0081 | Behavioral |
| 10 | `tx_hour` | 0.0041 | Transaction |

---

## 9. Model Artifacts & Outputs

- `models/ringguard_baseline_xgb_v1.joblib`: Serialized trained XGBoost model.
- `models/ringguard_baseline_xgb_v1_metadata.json`: Model configuration, training timestamp, split boundaries, and evaluation metrics.
- `ml/data/evaluation/baseline_predictions.csv`: 2,000 transaction predictions with columns:
  - `transaction_id`, `timestamp`, `split`, `actual_label`, `predicted_ring_probability`
- `ml/data/evaluation/baseline_metrics.json`: JSON structure of all evaluation splits.
- `ml/data/evaluation/baseline_feature_importance.csv`: Ranked feature importance weights.

---

## 10. Limitations & Stage Boundary

1. **Synthetic Separability:** In this controlled Stage 2 dataset, ring fraud amounts and high burst volumes provide sharp separation using transaction and historical behavioral features alone.
2. **Lack of Network Context:** Model A cannot detect mule syndicates or account takeover rings that disguise transaction amounts to mimic legitimate peer-to-peer transfers. Stage 7 (Model B) will evaluate network topology.
3. **Threshold Calibration:** Model A predictions are output as raw model probabilities; decision threshold optimization and risk score calibration are deferred to subsequent stages.
