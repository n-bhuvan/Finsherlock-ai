#!/usr/bin/env python3
"""RingGuard AI — Stage 17 Adaptive Investigation Benchmark Pipeline.

V2 Stage 17: Uncertainty-Driven Investigation + Stopping Policy.
Executes deterministic playback of the Adaptive Investigation Engine
across verified held-out evaluation slices:
1. Overall (Held-out test set, N=300)
2. Ring Fraud (Held-out true positives, y==1)
3. Hard Negatives (Challenging high-exposure legitimate cases)
4. Cold Start (LIMITED / UNAVAILABLE graph confidence)
5. Mature (VERIFIED graph confidence)
6. Ambiguous (calibrated risk between 0.30 and 0.70)

Adheres strictly to:
- Correction 1: Slice counts and memberships derived dynamically from held-out metadata.
- Correction 7: Preserves V1 ml/data/evaluation/investigation_efficiency.json byte-for-byte.
  Saves results to ml/data/evaluation/stage17_investigation_benchmark.json.
"""

import json
import hashlib
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Ensure repo root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.db.session import SessionLocal
from app.investigation.adaptive import AdaptiveInvestigationEngine, TOOL_SIMULATED_COSTS
from app.investigation.schemas import StoppingReason
from ml.models.graph_model import GraphEnhancedXGBoostModel
from ml.evaluation.cold_start import determine_graph_confidence


def get_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def compute_slice_metrics(slice_name: str, results: List[Any]) -> Dict[str, Any]:
    """Compute aggregated efficiency and uncertainty reduction metrics for a slice."""
    if not results:
        return {
            "slice_name": slice_name,
            "sample_count": 0,
            "average_steps": 0.0,
            "median_steps": 0.0,
            "average_initial_uncertainty": 0.05,
            "average_final_uncertainty": 0.05,
            "average_uncertainty_reduction": 0.0,
            "relative_uncertainty_reduction": 0.0,
            "average_tool_cost": 0.0,
            "evidence_sufficiency_rate": 0.0,
            "budget_compliance_rate": 1.0,
            "stopping_reason_distribution": {},
        }

    # Strict invariant enforcement: uncertainty must be in [0.05, 0.95] for every case
    for r in results:
        assert 0.05 <= r.initial_uncertainty <= 0.95, (
            f"Invariant violation: initial_uncertainty {r.initial_uncertainty} out of [0.05, 0.95] in {slice_name}"
        )
        assert 0.05 <= r.final_uncertainty <= 0.95, (
            f"Invariant violation: final_uncertainty {r.final_uncertainty} out of [0.05, 0.95] in {slice_name}"
        )

    steps = [r.step_count for r in results]
    u_inits = [r.initial_uncertainty for r in results]
    u_finals = [r.final_uncertainty for r in results]
    u_reductions = [r.uncertainty_reduction for r in results]
    costs = [r.total_tool_cost for r in results]

    stop_reasons: Dict[str, int] = {}
    for r in results:
        sr = r.stopping_reason.value if hasattr(r.stopping_reason, "value") else str(r.stopping_reason)
        stop_reasons[sr] = stop_reasons.get(sr, 0) + 1

    avg_u_init = round(float(np.mean(u_inits)), 4)
    avg_u_final = round(float(np.mean(u_finals)), 4)
    avg_red = round(float(np.mean(u_reductions)), 4)
    rel_red = round(avg_red / avg_u_init, 4) if avg_u_init > 0 else 0.0

    sufficient_count = stop_reasons.get("SUFFICIENT_EVIDENCE", 0)
    sufficiency_rate = round(sufficient_count / len(results), 4)

    compliant_count = sum(1 for c in costs if c <= 150.0)
    compliance_rate = round(compliant_count / len(results), 4)

    return {
        "slice_name": slice_name,
        "sample_count": len(results),
        "average_steps": round(float(np.mean(steps)), 2),
        "median_steps": round(float(np.median(steps)), 2),
        "average_initial_uncertainty": avg_u_init,
        "average_final_uncertainty": avg_u_final,
        "average_uncertainty_reduction": avg_red,
        "relative_uncertainty_reduction": rel_red,
        "average_tool_cost": round(float(np.mean(costs)), 2),
        "evidence_sufficiency_rate": sufficiency_rate,
        "budget_compliance_rate": compliance_rate,
        "stopping_reason_distribution": stop_reasons,
    }


def main():
    print("=" * 75)
    print("RINGGUARD AI -- STAGE 17 ADAPTIVE INVESTIGATION BENCHMARK")
    print("=" * 75)

    # 1. Verify Frozen Model Binaries
    model_a_path = REPO_ROOT / "models" / "ringguard_baseline_xgb_v1.joblib"
    model_b_path = REPO_ROOT / "models" / "ringguard_graph_xgb_v1.joblib"
    calib_b_path = REPO_ROOT / "models" / "calibrator_model_b.joblib"

    expected_hash_a = "ed8fa6e28177614e7fd494767e74ed9987a54b23a38ada74efe5a8cb8a7b06f0"
    expected_hash_b = "3ddd77d9caa27e65f7369ecd9e1cb6267404f4ff73a132a2b735f5da4568752e"
    expected_hash_calib = "9539db0ebbc35c545623a0edab8e6676410cee9bcb9ad3ce85bc360e33c4ec3d"

    hash_a = get_file_sha256(model_a_path)
    hash_b = get_file_sha256(model_b_path)
    hash_calib = get_file_sha256(calib_b_path)

    print(f"\n[VERIFICATION] Model A SHA-256: {hash_a}")
    print(f"[VERIFICATION] Model B SHA-256: {hash_b}")
    print(f"[VERIFICATION] Calibrator B SHA-256: {hash_calib}")
    assert hash_a == expected_hash_a, f"Model A binary modified! {hash_a} != {expected_hash_a}"
    assert hash_b == expected_hash_b, f"Model B binary modified! {hash_b} != {expected_hash_b}"
    assert hash_calib == expected_hash_calib, f"Calibrator B binary modified! {hash_calib} != {expected_hash_calib}"
    print("[PASS] Model and calibrator binaries verified frozen and unmodified.")

    # 2. Load Held-Out Test Set (N=300)
    print("\n[INFO] Loading held-out test partition (N=300)...")
    mb_loader = GraphEnhancedXGBoostModel()
    X_b, y_b, meta_b = mb_loader.load_dataset()
    _, _, (X_test_b, y_test_b, meta_test_b) = mb_loader.chronological_split(X_b, y_b, meta_b)

    test_ids = list(meta_test_b.index)
    print(f"Total Held-Out Test Samples: {len(test_ids)}")

    # 3. Execute Adaptive Investigation Engine on Held-Out Samples
    print("\n[INFO] Running AdaptiveInvestigationEngine across held-out transactions...")
    db = SessionLocal()
    engine = AdaptiveInvestigationEngine(db)

    results_by_id: Dict[str, Any] = {}
    t_start = time.time()

    for idx, tx_id in enumerate(test_ids):
        if (idx + 1) % 50 == 0 or idx == len(test_ids) - 1:
            print(f"  Processed {idx + 1}/{len(test_ids)} transactions...")
        res = engine.run_investigation(tx_id, max_steps=5, tool_budget=150.0)
        results_by_id[tx_id] = res

    elapsed = time.time() - t_start
    print(f"[COMPLETE] Executed {len(test_ids)} adaptive investigations in {elapsed:.2f}s ({elapsed/len(test_ids):.3f}s/tx).")

    # 4. Partition Slices Dynamically (Correction 1)
    # Slice 1: Overall
    overall_results = list(results_by_id.values())

    # Slice 2: Ring Fraud (y == 1)
    ring_ids = [tx_id for tx_id, is_ring in zip(test_ids, y_test_b) if is_ring == 1]
    ring_results = [results_by_id[tid] for tid in ring_ids]

    # Slice 3: Cold Start (confidence LIMITED or UNAVAILABLE)
    confidences = {tx_id: determine_graph_confidence(row) for tx_id, row in X_test_b.iterrows()}
    cold_start_ids = [tid for tid in test_ids if confidences.get(tid) in ["LIMITED", "UNAVAILABLE"]]
    cold_start_results = [results_by_id[tid] for tid in cold_start_ids]

    # Slice 4: Mature (confidence VERIFIED)
    mature_ids = [tid for tid in test_ids if confidences.get(tid) == "VERIFIED"]
    mature_results = [results_by_id[tid] for tid in mature_ids]

    # Slice 5: Hard Negatives (Legitimate cases with highest exposure)
    legit_ids = [tx_id for tx_id, is_ring in zip(test_ids, y_test_b) if is_ring == 0]
    legit_subset = X_test_b.loc[legit_ids]
    hard_neg_ids = list(legit_subset.sort_values(by="tx_amount", ascending=False).head(30).index)
    hard_neg_results = [results_by_id[tid] for tid in hard_neg_ids]

    # Slice 6: Ambiguous Cases (0.30 <= calibrated_risk <= 0.70)
    ambig_ids = [tid for tid, r in results_by_id.items() if 0.30 <= r.calibrated_risk_score <= 0.70]
    ambig_results = [results_by_id[tid] for tid in ambig_ids]

    print(f"\n[INFO] Derived Slice Memberships:")
    print(f"  Overall: {len(overall_results)}")
    print(f"  Ring Fraud: {len(ring_results)}")
    print(f"  Hard Negatives: {len(hard_neg_results)}")
    print(f"  Cold Start: {len(cold_start_results)}")
    print(f"  Mature: {len(mature_results)}")
    print(f"  Ambiguous (0.30 <= p <= 0.70): {len(ambig_results)}")

    # 5. Compute Metrics Across Slices
    slices_data: Dict[str, Any] = {
        "overall": compute_slice_metrics("Overall (Held-Out Test)", overall_results),
        "ring_fraud": compute_slice_metrics("Ring Fraud Cases", ring_results),
        "hard_negatives": compute_slice_metrics("Hard Negatives (High Exposure)", hard_neg_results),
        "cold_start": compute_slice_metrics("Cold Start (Limited Graph)", cold_start_results),
        "mature": compute_slice_metrics("Mature (Verified Graph)", mature_results),
        "ambiguous": compute_slice_metrics("Ambiguous Cases (0.30 <= p <= 0.70)", ambig_results),
    }

    # 6. Load Historical V1 Baseline for Comparison (Correction 7)
    v1_bench_path = REPO_ROOT / "ml" / "data" / "evaluation" / "investigation_efficiency.json"
    v1_comparison: Dict[str, Any] = {}
    if v1_bench_path.exists():
        with open(v1_bench_path, "r", encoding="utf-8") as f:
            v1_data = json.load(f)
        v1_slices = v1_data.get("slices", {})
        v1_comparison = {
            "v1_overall": {
                "average_steps": v1_slices.get("overall", {}).get("average_steps"),
                "average_tool_cost": v1_slices.get("overall", {}).get("average_tool_cost"),
                "average_initial_uncertainty": v1_slices.get("overall", {}).get("average_initial_uncertainty"),
                "average_final_uncertainty": v1_slices.get("overall", {}).get("average_final_uncertainty"),
                "average_uncertainty_reduction": v1_slices.get("overall", {}).get("average_uncertainty_reduction"),
            },
            "v1_ring_fraud": {
                "average_steps": v1_slices.get("ring_fraud", {}).get("average_steps"),
                "average_tool_cost": v1_slices.get("ring_fraud", {}).get("average_tool_cost"),
                "average_initial_uncertainty": v1_slices.get("ring_fraud", {}).get("average_initial_uncertainty"),
                "average_final_uncertainty": v1_slices.get("ring_fraud", {}).get("average_final_uncertainty"),
                "average_uncertainty_reduction": v1_slices.get("ring_fraud", {}).get("average_uncertainty_reduction"),
            },
            "stage17_overall": {
                "average_steps": slices_data["overall"]["average_steps"],
                "average_tool_cost": slices_data["overall"]["average_tool_cost"],
                "average_initial_uncertainty": slices_data["overall"]["average_initial_uncertainty"],
                "average_final_uncertainty": slices_data["overall"]["average_final_uncertainty"],
                "average_uncertainty_reduction": slices_data["overall"]["average_uncertainty_reduction"],
            },
            "stage17_ring_fraud": {
                "average_steps": slices_data["ring_fraud"]["average_steps"],
                "average_tool_cost": slices_data["ring_fraud"]["average_tool_cost"],
                "average_initial_uncertainty": slices_data["ring_fraud"]["average_initial_uncertainty"],
                "average_final_uncertainty": slices_data["ring_fraud"]["average_final_uncertainty"],
                "average_uncertainty_reduction": slices_data["ring_fraud"]["average_uncertainty_reduction"],
            },
            "methodology_compatibility": "Identical held-out test partition (N=300), identical tool costs and budget (max INR 150.0), identical initial uncertainty heuristic.",
        }

    # 7. Persist to Stage 17 Benchmark File (Preserves V1 baseline untouched)
    stage17_bench_path = REPO_ROOT / "ml" / "data" / "evaluation" / "stage17_investigation_benchmark.json"
    benchmark_payload = {
        "status": "Available",
        "metadata": {
            "stage": 17,
            "title": "Stage 17 Adaptive Uncertainty-Driven Investigation Benchmark",
            "evaluation_date": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "sample_size": len(test_ids),
            "max_tool_budget_inr": 150.0,
            "max_steps": 5,
        },
        "slices": slices_data,
        "comparison_with_v1": v1_comparison,
        "methodology_notes": (
            "Evaluated across all 300 held-out test transactions from the chronological split. "
            "Slice memberships derived dynamically from metadata. "
            "Strict point-in-time temporal boundaries applied to all tool queries."
        ),
        "disclaimer": "Simulated benchmark evaluation on synthetic transactions. Read-only defense-only decision support.",
    }

    with open(stage17_bench_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_payload, f, indent=2)

    print(f"\n[PASS] Stage 17 benchmark successfully persisted to {stage17_bench_path}")

    # Print summary table
    print("\n" + "=" * 75)
    print("STAGE 17 BENCHMARK SUMMARY TABLE")
    print("=" * 75)
    print(f"{'Slice':<32} | {'N':>4} | {'Steps':>5} | {'Cost (INR)':>10} | {'U0':>6} | {'Uk':>6} | {'Red':>6} | {'Suff%':>5}")
    print("-" * 80)
    for s_key, s_val in slices_data.items():
        print(
            f"{s_val['slice_name']:<32} | "
            f"{s_val['sample_count']:>4} | "
            f"{s_val['average_steps']:>5.2f} | "
            f"{s_val['average_tool_cost']:>10.2f} | "
            f"{s_val['average_initial_uncertainty']:>6.4f} | "
            f"{s_val['average_final_uncertainty']:>6.4f} | "
            f"{s_val['average_uncertainty_reduction']:>6.4f} | "
            f"{s_val['evidence_sufficiency_rate']*100:>4.1f}%"
        )
    print("=" * 80)

    db.close()


if __name__ == "__main__":
    main()
