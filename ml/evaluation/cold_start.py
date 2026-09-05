"""RingGuard AI — Cold-Start Segmentation & Evaluation Engine.

Stage 14: Cold Start + Calibration + Thresholding.
Implements deterministic graph confidence precedence, cold-start segmentation,
sample-size sufficiency auditing, and separate slice evaluation.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from ml.evaluation.metrics import evaluate_binary_predictions


def determine_graph_confidence(row: pd.Series) -> str:
    """Deterministic graph confidence precedence:
    
    1. UNAVAILABLE: Account is completely isolated from historical co-usage graphs (g_connected_accounts_count == 0).
    2. LIMITED: Account is in early behavioral infancy (beh_is_first_tx == 1 or beh_hist_tx_count <= 2).
    3. VERIFIED: Mature account with established graph relationships.
    """
    if "g_connected_accounts_count" in row and row["g_connected_accounts_count"] == 0:
        return "UNAVAILABLE"
    elif (row.get("beh_is_first_tx", 0) == 1) or (row.get("beh_hist_tx_count", 999) <= 2):
        return "LIMITED"
    else:
        return "VERIFIED"


def audit_cold_start_rules(df_feat: pd.DataFrame, df_meta: pd.DataFrame) -> List[Dict[str, Any]]:
    """Audit candidate cold-start rules and report sample counts and sufficiency status."""
    rules = [
        {
            "rule_id": "RULE_1_NEW_ACCOUNT",
            "name": "Account Age <= 3 Days",
            "description": "Accounts created within 3 days of transaction time",
            "mask": (df_feat["beh_account_age_days"] <= 3.0).values,
        },
        {
            "rule_id": "RULE_2_LOW_VELOCITY",
            "name": "Historical Tx Count <= 2",
            "description": "Accounts with 2 or fewer prior transactions",
            "mask": (df_feat["beh_hist_tx_count"] <= 2).values,
        },
        {
            "rule_id": "RULE_3_FIRST_TRANSACTION",
            "name": "First Account Transaction",
            "description": "Account's very first observed transaction",
            "mask": (df_feat["beh_is_first_tx"] == 1).values,
        },
        {
            "rule_id": "RULE_4_ISOLATED_GRAPH",
            "name": "Isolated Co-usage Graph",
            "description": "Accounts with zero connected accounts in co-usage graph",
            "mask": (df_feat["g_connected_accounts_count"] == 0).values if "g_connected_accounts_count" in df_feat else np.zeros(len(df_feat), dtype=bool),
        },
    ]

    audits = []
    y_true = df_meta["is_ring"].values.astype(int)

    for r in rules:
        count = int(np.sum(r["mask"]))
        pos_count = int(np.sum(y_true[r["mask"]]))
        neg_count = count - pos_count

        if count == 0 or count < 20:
            status = f"LIMITED / INSUFFICIENT EVIDENCE (N={count})"
            sufficiency = "INSUFFICIENT"
        else:
            status = f"EVALUATED (N={count})"
            sufficiency = "SUFFICIENT"

        audits.append({
            "rule_id": r["rule_id"],
            "rule_name": r["name"],
            "description": r["description"],
            "sample_count": count,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "status": status,
            "sufficiency": sufficiency,
        })

    return audits


def evaluate_cold_start_slices(
    X_a: pd.DataFrame,
    X_b: pd.DataFrame,
    y_true: np.ndarray,
    model_a: Any,
    model_b: Any,
    threshold: float = 0.70,
) -> Dict[str, Any]:
    """Evaluate Model A and Model B on Cold-Start vs Mature slices without mutating Model B inputs."""
    # Compute confidence for all rows using X_b point-in-time features
    confidences = [determine_graph_confidence(X_b.iloc[i]) for i in range(len(X_b))]
    conf_arr = np.array(confidences)

    is_cold = (conf_arr == "UNAVAILABLE") | (conf_arr == "LIMITED")
    is_mature = conf_arr == "VERIFIED"

    # Pristine model inference — ZERO feature tampering
    p_a = model_a.predict_proba(X_a)[:, 1]
    p_b = model_b.predict_proba(X_b)[:, 1]

    slices = {}
    for slice_name, mask in [("overall", np.ones(len(y_true), dtype=bool)), ("cold_start", is_cold), ("mature", is_mature)]:
        s_y = y_true[mask]
        s_pa = p_a[mask]
        s_pb = p_b[mask]

        if len(s_y) == 0:
            slices[slice_name] = {
                "sample_count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "threshold": threshold,
                "model_a": None,
                "model_b": None,
                "deltas": None,
                "status": "EMPTY_SLICE",
            }
            continue

        mA = evaluate_binary_predictions(s_y, s_pa, threshold=threshold)
        mB = evaluate_binary_predictions(s_y, s_pb, threshold=threshold)

        slices[slice_name] = {
            "sample_count": int(np.sum(mask)),
            "positive_count": int(np.sum(s_y == 1)),
            "negative_count": int(np.sum(s_y == 0)),
            "threshold": threshold,
            "model_a": mA,
            "model_b": mB,
            "deltas": {
                "pr_auc_delta": round(mB["pr_auc"] - mA["pr_auc"], 4),
                "roc_auc_delta": round(mB["roc_auc"] - mA["roc_auc"], 4),
                "precision_delta": round(mB["precision"] - mA["precision"], 4),
                "recall_delta": round(mB["recall"] - mA["recall"], 4),
                "f1_delta": round(mB["f1"] - mA["f1"], 4),
                "fpr_delta": round(mB["false_positive_rate"] - mA["false_positive_rate"], 4),
                "fp_delta": mB["confusion_matrix"]["false_positives"] - mA["confusion_matrix"]["false_positives"],
                "tp_delta": mB["confusion_matrix"]["true_positives"] - mA["confusion_matrix"]["true_positives"],
            }
        }

    return {
        "confidence_distribution": {
            "UNAVAILABLE": int(np.sum(conf_arr == "UNAVAILABLE")),
            "LIMITED": int(np.sum(conf_arr == "LIMITED")),
            "VERIFIED": int(np.sum(conf_arr == "VERIFIED")),
        },
        "slices": slices,
        "advisory_policy": (
            "Cold-Start Decision Support Policy: If graph_confidence is LIMITED or UNAVAILABLE, "
            "investigators are advised to rely primarily on transactional baseline signals and route "
            "to Tier-1 identity verification. No automated blocking or clearing is performed."
        )
    }
