#!/usr/bin/env python3
"""RingGuard AI — Stage 14 Cold Start, Calibration, and Thresholding Pipeline.

Stage 14: Cold Start + Calibration + Thresholding.
Orchestrates:
1. Cold-start segmentation, rule audit, and slice evaluation (zero input mutation).
2. Probability calibration fitting on Val-Calib (N=150) and deterministic selection.
3. Threshold policy optimization on Val-Thresh (N=150) across 4 discrete scenarios.
4. Economic sensitivity analysis (50%, 70%, 85%, 100% interception rates).
5. Post-freeze evaluation on the untouched held-out test set (N=300).
6. Persisting all evaluation artifacts under ml/data/evaluation/ and models/.
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import joblib

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.models.baseline import BaselineXGBoostModel
from ml.models.graph_model import GraphEnhancedXGBoostModel
from ml.calibration.calibrator import RiskCalibrator
from ml.calibration.metrics import compute_brier_score, compute_ece, compute_reliability_curve
from ml.evaluation.threshold_optimizer import ThresholdPolicyOptimizer
from ml.evaluation.cold_start import (
    determine_graph_confidence,
    audit_cold_start_rules,
    evaluate_cold_start_slices,
)
from ml.evaluation.metrics import evaluate_binary_predictions


def get_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def json_serialize(obj):
    """Serialize numpy types for standard JSON encoder."""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def main():
    print("=" * 75)
    print("RINGGUARD AI -- STAGE 14 PIPELINE: COLD START + CALIBRATION + THRESHOLDS")
    print("=" * 75)

    # 1. Verify Frozen Model Binaries SHA-256
    model_a_path = REPO_ROOT / "models" / "ringguard_baseline_xgb_v1.joblib"
    model_b_path = REPO_ROOT / "models" / "ringguard_graph_xgb_v1.joblib"

    expected_hash_a = "ed8fa6e28177614e7fd494767e74ed9987a54b23a38ada74efe5a8cb8a7b06f0"
    expected_hash_b = "3ddd77d9caa27e65f7369ecd9e1cb6267404f4ff73a132a2b735f5da4568752e"

    hash_a_pre = get_file_sha256(model_a_path)
    hash_b_pre = get_file_sha256(model_b_path)

    print(f"\n[VERIFICATION] Model A SHA-256: {hash_a_pre}")
    print(f"[VERIFICATION] Model B SHA-256: {hash_b_pre}")
    assert hash_a_pre == expected_hash_a, f"Model A binary modified! {hash_a_pre} != {expected_hash_a}"
    assert hash_b_pre == expected_hash_b, f"Model B binary modified! {hash_b_pre} != {expected_hash_b}"
    print("[PASS] Model A and Model B binaries verified frozen and unmodified.")

    # 2. Load Datasets and Models
    print("\n[INFO] Loading chronological feature datasets...")
    ma_loader = BaselineXGBoostModel()
    mb_loader = GraphEnhancedXGBoostModel()

    X_a, y_a, meta_a = ma_loader.load_dataset()
    X_b, y_b, meta_b = mb_loader.load_dataset()

    (X_train_a, y_train_a, meta_train_a), (X_val_a, y_val_a, meta_val_a), (X_test_a, y_test_a, meta_test_a) = ma_loader.chronological_split(X_a, y_a, meta_a)
    (X_train_b, y_train_b, meta_train_b), (X_val_b, y_val_b, meta_val_b), (X_test_b, y_test_b, meta_test_b) = mb_loader.chronological_split(X_b, y_b, meta_b)

    # Internal 50/50 Split of Validation Partition (N=300 -> Val-Calib N=150, Val-Thresh N=150)
    print("\n[INFO] Partitioning Validation set (N=300) into Val-Calib (N=150) and Val-Thresh (N=150)...")
    val_calib_mask = np.zeros(len(X_val_b), dtype=bool)
    val_calib_mask[:150] = True
    val_thresh_mask = ~val_calib_mask

    y_val_calib = y_val_b.iloc[:150].values
    y_val_thresh = y_val_b.iloc[150:].values
    amounts_val_thresh = X_val_b.iloc[150:]["tx_amount"].values

    y_test = y_test_b.values
    amounts_test = X_test_b["tx_amount"].values

    print(f"  Val-Calib : N={len(y_val_calib)}, Pos={int(y_val_calib.sum())}, Neg={len(y_val_calib) - int(y_val_calib.sum())}")
    print(f"  Val-Thresh: N={len(y_val_thresh)}, Pos={int(y_val_thresh.sum())}, Neg={len(y_val_thresh) - int(y_val_thresh.sum())}")
    print(f"  Held-Out  : N={len(y_test)}, Pos={int(y_test.sum())}, Neg={len(y_test) - int(y_test.sum())}")

    # Load frozen model binaries
    model_a = joblib.load(model_a_path)
    model_b = joblib.load(model_b_path)

    # 3. Compute Raw Probabilities
    print("\n[INFO] Computing uncalibrated probabilities for all partitions...")
    p_val_calib_a = model_a.predict_proba(X_val_a.iloc[:150])[:, 1]
    p_val_thresh_a = model_a.predict_proba(X_val_a.iloc[150:])[:, 1]
    p_test_a = model_a.predict_proba(X_test_a)[:, 1]

    p_val_calib_b = model_b.predict_proba(X_val_b.iloc[:150])[:, 1]
    p_val_thresh_b = model_b.predict_proba(X_val_b.iloc[150:])[:, 1]
    p_test_b = model_b.predict_proba(X_test_b)[:, 1]

    # 4. Calibration Phase: Fit on Val-Calib and Select Deterministically
    print("\n[INFO] Fitting Post-Hoc Calibrators on Val-Calib (N=150)...")
    calibrator_a = RiskCalibrator().fit(y_val_calib, p_val_calib_a)
    calibrator_b = RiskCalibrator().fit(y_val_calib, p_val_calib_b)

    print(f"  Model A Selected: {calibrator_a.selected_method.upper()} ({calibrator_a.selection_reason})")
    print(f"  Model B Selected: {calibrator_b.selected_method.upper()} ({calibrator_b.selection_reason})")

    # Persist Calibrator joblib models
    calib_model_dir = REPO_ROOT / "models"
    calib_model_dir.mkdir(parents=True, exist_ok=True)
    calibrator_a.save(calib_model_dir / "calibrator_model_a.joblib")
    calibrator_b.save(calib_model_dir / "calibrator_model_b.joblib")
    print("  Persisted calibrator models to models/calibrator_model_a.joblib and calibrator_model_b.joblib")

    # Compute calibration metrics on Val-Calib and Test
    calib_val_a_p_sel = calibrator_a.transform(p_val_calib_a)
    calib_test_a_p_sel = calibrator_a.transform(p_test_a)
    calib_val_b_p_sel = calibrator_b.transform(p_val_calib_b)
    calib_test_b_p_sel = calibrator_b.transform(p_test_b)

    calibration_artifacts = {
        "metadata": {
            "stage": 14,
            "title": "Post-Hoc Probability Calibration Evaluation",
            "unit_of_evaluation": "TRANSACTION",
            "val_calib_sample_count": 150,
            "val_calib_positive_count": int(y_val_calib.sum()),
            "val_calib_negative_count": int((y_val_calib == 0).sum()),
            "held_out_test_sample_count": 300,
            "held_out_test_positive_count": int(y_test.sum()),
            "held_out_test_negative_count": int((y_test == 0).sum()),
            "selection_algorithm": "Deterministic lowest Brier score on Val-Calib, fallback to raw if both degrade, Platt tie-breaker if |diff| <= 0.005",
        },
        "model_a": {
            "selected_calibrator": calibrator_a.selected_method,
            "selection_reason": calibrator_a.selection_reason,
            "val_calib": {
                "raw": {
                    "brier_score": round(compute_brier_score(y_val_calib, p_val_calib_a), 6),
                    "ece": round(compute_ece(y_val_calib, p_val_calib_a), 6),
                    "reliability_curve": compute_reliability_curve(y_val_calib, p_val_calib_a),
                },
                "platt": {
                    "brier_score": round(compute_brier_score(y_val_calib, calibrator_a.transform(p_val_calib_a, "platt")), 6),
                    "ece": round(compute_ece(y_val_calib, calibrator_a.transform(p_val_calib_a, "platt")), 6),
                    "reliability_curve": compute_reliability_curve(y_val_calib, calibrator_a.transform(p_val_calib_a, "platt")),
                },
                "isotonic": {
                    "brier_score": round(compute_brier_score(y_val_calib, calibrator_a.transform(p_val_calib_a, "isotonic")), 6),
                    "ece": round(compute_ece(y_val_calib, calibrator_a.transform(p_val_calib_a, "isotonic")), 6),
                    "reliability_curve": compute_reliability_curve(y_val_calib, calibrator_a.transform(p_val_calib_a, "isotonic")),
                },
            },
            "held_out_test": {
                "raw": {
                    "brier_score": round(compute_brier_score(y_test, p_test_a), 6),
                    "ece": round(compute_ece(y_test, p_test_a), 6),
                    "reliability_curve": compute_reliability_curve(y_test, p_test_a),
                },
                "selected_calibrated": {
                    "method": calibrator_a.selected_method,
                    "brier_score": round(compute_brier_score(y_test, calib_test_a_p_sel), 6),
                    "ece": round(compute_ece(y_test, calib_test_a_p_sel), 6),
                    "reliability_curve": compute_reliability_curve(y_test, calib_test_a_p_sel),
                },
            },
        },
        "model_b": {
            "selected_calibrator": calibrator_b.selected_method,
            "selection_reason": calibrator_b.selection_reason,
            "val_calib": {
                "raw": {
                    "brier_score": round(compute_brier_score(y_val_calib, p_val_calib_b), 6),
                    "ece": round(compute_ece(y_val_calib, p_val_calib_b), 6),
                    "reliability_curve": compute_reliability_curve(y_val_calib, p_val_calib_b),
                },
                "platt": {
                    "brier_score": round(compute_brier_score(y_val_calib, calibrator_b.transform(p_val_calib_b, "platt")), 6),
                    "ece": round(compute_ece(y_val_calib, calibrator_b.transform(p_val_calib_b, "platt")), 6),
                    "reliability_curve": compute_reliability_curve(y_val_calib, calibrator_b.transform(p_val_calib_b, "platt")),
                },
                "isotonic": {
                    "brier_score": round(compute_brier_score(y_val_calib, calibrator_b.transform(p_val_calib_b, "isotonic")), 6),
                    "ece": round(compute_ece(y_val_calib, calibrator_b.transform(p_val_calib_b, "isotonic")), 6),
                    "reliability_curve": compute_reliability_curve(y_val_calib, calibrator_b.transform(p_val_calib_b, "isotonic")),
                },
            },
            "held_out_test": {
                "raw": {
                    "brier_score": round(compute_brier_score(y_test, p_test_b), 6),
                    "ece": round(compute_ece(y_test, p_test_b), 6),
                    "reliability_curve": compute_reliability_curve(y_test, p_test_b),
                },
                "selected_calibrated": {
                    "method": calibrator_b.selected_method,
                    "brier_score": round(compute_brier_score(y_test, calib_test_b_p_sel), 6),
                    "ece": round(compute_ece(y_test, calib_test_b_p_sel), 6),
                    "reliability_curve": compute_reliability_curve(y_test, calib_test_b_p_sel),
                },
            },
        },
    }

    calib_out_path = REPO_ROOT / "ml" / "data" / "evaluation" / "calibration_results.json"
    calib_out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(calib_out_path, "w", encoding="utf-8") as f:
        json.dump(calibration_artifacts, f, indent=2, default=json_serialize)
    print(f"  Exported calibration results to {calib_out_path}")

    # 5. Threshold Optimization Phase: Optimize on Val-Thresh, Freeze, Evaluate Test
    print("\n[INFO] Running Threshold Policy Optimization on Val-Thresh (N=150)...")
    p_val_thresh_b_cal = calibrator_b.transform(p_val_thresh_b)
    p_test_b_cal = calibrator_b.transform(p_test_b)

    opt_b = ThresholdPolicyOptimizer(interception_rate=0.85, fp_friction_cost=1200.0, investigation_cost=350.0)
    opt_b.run_validation_sweep(y_val_thresh, p_val_thresh_b_cal, amounts_val_thresh)

    print("  Model B Policy Scenarios Derived on Val-Thresh:")
    for k, scen in opt_b.policy_scenarios.items():
        print(f"    [{k}] {scen['scenario_name']}: Threshold={scen['threshold']}, Status={scen['status']}, {scen['primary_metric']}={scen['primary_value']}")

    print("\n[INFO] Evaluating Held-Out Test Set (N=300) at Frozen Policy Thresholds...")
    test_results_b = opt_b.evaluate_held_out_test(y_test, p_test_b_cal, amounts_test)

    for k, res in test_results_b.items():
        m = res.get("metrics")
        if m:
            print(f"    [{k}] T={res['threshold_applied']}: Recall={m['recall']:.4f}, Prec={m['precision']:.4f}, F1={m['f1']:.4f}, NetValue=Rs.{res['modeled_economics']['modeled_net_value_saved']:,.2f}")
        else:
            print(f"    [{k}]: Status={res['status']}")

    # Baseline threshold reference (T=0.70 and T=0.50)
    ref_70_m = evaluate_binary_predictions(y_test, p_test_b_cal, threshold=0.70)
    ref_70_econ = opt_b._compute_economic_value(amounts_test, y_test, (p_test_b_cal >= 0.70).astype(int), 0.85, cm=ref_70_m["confusion_matrix"])
    ref_50_m = evaluate_binary_predictions(y_test, p_test_b_cal, threshold=0.50)
    ref_50_econ = opt_b._compute_economic_value(amounts_test, y_test, (p_test_b_cal >= 0.50).astype(int), 0.85, cm=ref_50_m["confusion_matrix"])

    # Held-out test sensitivity analysis across interception tiers at T*=0.99
    held_out_sensitivity = opt_b.compute_held_out_sensitivity(
        y_test, p_test_b_cal, amounts_test, threshold=opt_b.policy_scenarios["T_star_economic"]["threshold"]
    )

    threshold_artifacts = {
        "metadata": {
            "stage": 14,
            "title": "Threshold Policy Optimization & Economic Sensitivity",
            "model_evaluated": "Model B (Graph-Enhanced, Calibrated)",
            "unit_of_evaluation": "TRANSACTION",
            "validation_partition": "Val-Thresh (N=150, rows 1550-1699)",
            "test_partition": "Held-Out Test (N=300, rows 1700-1999)",
            "modeling_assumptions": {
                "default_interception_rate": 0.85,
                "fp_friction_cost_inr": 1200.0,
                "investigation_case_cost_inr": 350.0,
                "exposure_formula": "Modeled Net Value Saved = Modeled Loss Avoided (Exposure * Interception) - (FP * CFP) - ((TP + FP) * Cinv)",
                "disclosure": "Financial figures represent modeled loss avoided and modeled net value saved under stated operational assumptions.",
            },
        },
        "validation_derived_policies": opt_b.policy_scenarios,
        "validation_sweep_summary": {
            "step_count": len(opt_b.threshold_sweep),
            "min_threshold": 0.01,
            "max_threshold": 0.99,
            "sweep_sample": opt_b.threshold_sweep[::5],
        },
        "economic_sensitivity_analysis": opt_b.sensitivity_analysis,
        "held_out_test_sensitivity_analysis": held_out_sensitivity,
        "held_out_test_evaluation": test_results_b,
        "standard_threshold_benchmarks": {
            "threshold_0_70_production_baseline": {
                "threshold": 0.70,
                "metrics": ref_70_m,
                "modeled_economics": ref_70_econ,
            },
            "threshold_0_50_default": {
                "threshold": 0.50,
                "metrics": ref_50_m,
                "modeled_economics": ref_50_econ,
            },
        },
    }

    thresh_out_path = REPO_ROOT / "ml" / "data" / "evaluation" / "threshold_optimization.json"
    with open(thresh_out_path, "w", encoding="utf-8") as f:
        json.dump(threshold_artifacts, f, indent=2, default=json_serialize)
    print(f"  Exported threshold optimization results to {thresh_out_path}")

    # 6. Cold-Start Segmentation & Evaluation Phase
    print("\n[INFO] Running Cold-Start Segmentation & Rule Audit (Zero Input Mutation)...")
    rule_audit_results = audit_cold_start_rules(X_b, meta_b)
    for r in rule_audit_results:
        print(f"  Rule [{r['rule_id']}] {r['rule_name']}: N={r['sample_count']} -> Status: {r['status']}")

    # Slices on Full Dataset and Held-Out Test Set
    full_cold_start_eval = evaluate_cold_start_slices(
        X_a, X_b, y_b.values, model_a, model_b, threshold=0.70
    )
    test_cold_start_eval = evaluate_cold_start_slices(
        X_test_a, X_test_b, y_test, model_a, model_b, threshold=0.70
    )

    cold_start_artifacts = {
        "metadata": {
            "stage": 14,
            "title": "Cold-Start Graph Confidence Segmentation & Performance Slices",
            "unit_of_evaluation": "TRANSACTION",
            "evaluation_rule": "Model B 58-feature inputs were strictly untouched (zero feature tampering or ungrounded imputation).",
            "advisory_policy": (
                "Decision-Support Policy: When graph_confidence is LIMITED or UNAVAILABLE, investigators are advised "
                "to prioritize transactional and behavioral signals, request Tier-1 identity verification, and perform "
                "manual verification before taking action. Automated blocking is never performed autonomously."
            ),
        },
        "rule_sufficiency_audit": rule_audit_results,
        "full_dataset_evaluation": {
            "total_samples": 2000,
            "confidence_distribution": full_cold_start_eval["confidence_distribution"],
            "slices": full_cold_start_eval["slices"],
        },
        "held_out_test_evaluation": {
            "total_samples": 300,
            "confidence_distribution": test_cold_start_eval["confidence_distribution"],
            "slices": test_cold_start_eval["slices"],
        },
    }

    cold_out_path = REPO_ROOT / "ml" / "data" / "evaluation" / "cold_start_evaluation.json"
    with open(cold_out_path, "w", encoding="utf-8") as f:
        json.dump(cold_start_artifacts, f, indent=2, default=json_serialize)
    print(f"  Exported cold start evaluation results to {cold_out_path}")

    # 7. Post-Run SHA-256 Verification of Model Binaries
    hash_a_post = get_file_sha256(model_a_path)
    hash_b_post = get_file_sha256(model_b_path)
    print(f"\n[FINAL AUDIT] Model A SHA-256 post-run: {hash_a_post}")
    print(f"[FINAL AUDIT] Model B SHA-256 post-run: {hash_b_post}")
    assert hash_a_post == expected_hash_a, f"CRITICAL: Model A was modified during run! {hash_a_post} != {expected_hash_a}"
    assert hash_b_post == expected_hash_b, f"CRITICAL: Model B was modified during run! {hash_b_post} != {expected_hash_b}"
    print("[PASS] Frozen Model A and Model B binary checksums strictly preserved.")

    print("\n" + "=" * 75)
    print("STAGE 14 EVALUATION PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 75)


if __name__ == "__main__":
    main()
