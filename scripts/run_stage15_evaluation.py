#!/usr/bin/env python3
"""RingGuard AI — Stage 15 Investigation Efficiency Evaluation Pipeline.

Stage 15: Investigation Efficiency + Business Impact.
Executes deterministic playback of the Bounded Uncertainty-Driven Investigation
Agent across verified held-out evaluation slices:
1. Overall (Held-out test set, N=300)
2. Ring Fraud (Held-out true positives, N=26)
3. Hard Negatives (Challenging legitimate cases)
4. Cold Start (LIMITED / UNAVAILABLE graph confidence)
5. Mature (VERIFIED graph confidence)

Persists results to ml/data/evaluation/investigation_efficiency.json.
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
from app.investigation.agent import InvestigationAgent, TOOL_SIMULATED_COSTS
from app.investigation.schemas import StoppingReason, NextBestActionType
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
            "average_tool_cost": 0.0,
            "stopping_reason_distribution": {},
            "action_distribution": {},
        }

    # Strict invariant enforcement: uncertainty must be in [0.05, 0.95] for every case
    for r in results:
        assert 0.05 <= r.initial_uncertainty <= 0.95, (
            f"Invariant violation: initial_uncertainty {r.initial_uncertainty} out of [0.05, 0.95] in {slice_name}"
        )
        assert 0.05 <= r.current_uncertainty <= 0.95, (
            f"Invariant violation: current_uncertainty {r.current_uncertainty} out of [0.05, 0.95] in {slice_name}"
        )

    steps = [r.step_count for r in results]
    u_inits = [r.initial_uncertainty for r in results]
    u_finals = [r.current_uncertainty for r in results]
    u_reductions = [r.total_uncertainty_reduction for r in results]
    costs = [r.total_simulated_tool_cost for r in results]

    stop_reasons: Dict[str, int] = {}
    actions: Dict[str, int] = {}

    for r in results:
        sr = r.stopping_reason.value if hasattr(r.stopping_reason, "value") else str(r.stopping_reason)
        stop_reasons[sr] = stop_reasons.get(sr, 0) + 1

        act = r.next_best_action.recommended_action.value if hasattr(r.next_best_action.recommended_action, "value") else str(r.next_best_action.recommended_action)
        actions[act] = actions.get(act, 0) + 1

    avg_u_init = round(float(np.mean(u_inits)), 4)
    avg_u_final = round(float(np.mean(u_finals)), 4)
    assert 0.05 <= avg_u_init <= 0.95, f"Average U0 {avg_u_init} out of bounds"
    assert 0.05 <= avg_u_final <= 0.95, f"Average Uk {avg_u_final} out of bounds"

    return {
        "slice_name": slice_name,
        "sample_count": len(results),
        "average_steps": round(float(np.mean(steps)), 2),
        "median_steps": round(float(np.median(steps)), 2),
        "average_initial_uncertainty": avg_u_init,
        "average_final_uncertainty": avg_u_final,
        "average_uncertainty_reduction": round(float(np.mean(u_reductions)), 4),
        "average_tool_cost": round(float(np.mean(costs)), 2),
        "stopping_reason_distribution": stop_reasons,
        "action_distribution": actions,
    }


def main():
    print("=" * 75)
    print("RINGGUARD AI -- STAGE 15 INVESTIGATION EFFICIENCY EVALUATION")
    print("=" * 75)

    # 1. Verify Frozen Model Binaries
    model_a_path = REPO_ROOT / "models" / "ringguard_baseline_xgb_v1.joblib"
    model_b_path = REPO_ROOT / "models" / "ringguard_graph_xgb_v1.joblib"

    expected_hash_a = "ed8fa6e28177614e7fd494767e74ed9987a54b23a38ada74efe5a8cb8a7b06f0"
    expected_hash_b = "3ddd77d9caa27e65f7369ecd9e1cb6267404f4ff73a132a2b735f5da4568752e"

    hash_a = get_file_sha256(model_a_path)
    hash_b = get_file_sha256(model_b_path)

    print(f"\n[VERIFICATION] Model A SHA-256: {hash_a}")
    print(f"[VERIFICATION] Model B SHA-256: {hash_b}")
    assert hash_a == expected_hash_a, f"Model A binary modified! {hash_a} != {expected_hash_a}"
    assert hash_b == expected_hash_b, f"Model B binary modified! {hash_b} != {expected_hash_b}"
    print("[PASS] Model A and Model B binaries verified frozen and unmodified.")

    # 2. Load Held-Out Test Set (N=300)
    print("\n[INFO] Loading held-out test partition (N=300)...")
    mb_loader = GraphEnhancedXGBoostModel()
    X_b, y_b, meta_b = mb_loader.load_dataset()
    _, _, (X_test_b, y_test_b, meta_test_b) = mb_loader.chronological_split(X_b, y_b, meta_b)

    test_ids = list(meta_test_b.index)
    print(f"Total Held-Out Test Samples: {len(test_ids)}")

    # 3. Execute Investigation Agent on Held-Out Samples
    print("\n[INFO] Running bounded investigation agent across held-out transactions...")
    db = SessionLocal()
    agent = InvestigationAgent(db)

    results_by_id: Dict[str, Any] = {}
    t_start = time.time()

    for idx, tx_id in enumerate(test_ids):
        if (idx + 1) % 50 == 0 or idx == len(test_ids) - 1:
            print(f"  Processed {idx + 1}/{len(test_ids)} transactions...")
        res = agent.run_investigation(tx_id, max_steps=5, tool_budget=150.0)
        results_by_id[tx_id] = res

    elapsed = time.time() - t_start
    print(f"[COMPLETE] Executed {len(test_ids)} investigations in {elapsed:.2f}s ({elapsed/len(test_ids):.3f}s/tx).")

    # 4. Partition Slices
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

    # Slice 5: Hard Negatives (Legitimate cases with high baseline velocity or amount)
    legit_ids = [tx_id for tx_id, is_ring in zip(test_ids, y_test_b) if is_ring == 0]
    legit_subset = X_test_b.loc[legit_ids]
    # Hard negatives: highest exposure or velocity
    hard_neg_ids = list(legit_subset.sort_values(by="tx_amount", ascending=False).head(30).index)
    hard_neg_results = [results_by_id[tid] for tid in hard_neg_ids]

    # 5. Compute Metrics Across Slices
    slices_data: Dict[str, Any] = {
        "overall": compute_slice_metrics("Overall (Held-Out Test)", overall_results),
        "ring_fraud": compute_slice_metrics("Ring Fraud Cases", ring_results),
        "hard_negatives": compute_slice_metrics("Hard Negatives (High Exposure)", hard_neg_results),
        "cold_start": compute_slice_metrics("Cold Start (Limited Graph)", cold_start_results),
        "mature": compute_slice_metrics("Mature (Verified Graph)", mature_results),
    }

    # 6. Workflow Compression Summary
    total_steps = sum(r.step_count for r in overall_results)
    max_possible_steps = len(overall_results) * 9
    avg_steps = float(np.mean([r.step_count for r in overall_results]))
    avg_cost = float(np.mean([r.total_simulated_tool_cost for r in overall_results]))
    avg_init_u = float(np.mean([r.initial_uncertainty for r in overall_results]))
    avg_red_u = float(np.mean([r.total_uncertainty_reduction for r in overall_results]))

    step_reduction_pct = round((1.0 - (total_steps / max_possible_steps)) * 100.0, 2)
    cost_savings_pct = round((1.0 - (avg_cost / 350.0)) * 100.0, 2)

    avg_final_u = float(np.mean([r.current_uncertainty for r in overall_results]))

    workflow_summary = {
        "total_cases_evaluated": len(overall_results),
        "maximum_unbounded_tool_calls_possible": max_possible_steps,
        "actual_bounded_tool_calls_executed": total_steps,
        "workflow_compression_percentage": step_reduction_pct,
        "tool_call_reduction_vs_hypothetical_all_9_tool_execution_pct": step_reduction_pct,
        "average_steps_per_investigation": round(avg_steps, 2),
        "average_simulated_tool_cost_inr": round(avg_cost, 2),
        "human_analyst_cost_benchmark_inr": 350.00,
        "simulated_investigation_cost_savings_percentage": cost_savings_pct,
        "average_initial_uncertainty": round(avg_init_u, 4),
        "average_final_uncertainty": round(avg_final_u, 4),
        "average_uncertainty_reduction": round(avg_red_u, 4),
        "relative_uncertainty_reduction_percentage": round((avg_red_u / avg_init_u) * 100.0, 2),
        "cost_distinction_note": (
            "Average simulated tool-query cost reflects operational automated query costs. "
            "The ₹350 human-review benchmark is a separate modeled cost category for human analyst review time."
        ),
    }

    output_payload = {
        "status": "Available",
        "metadata": {
            "stage": 15,
            "title": "Investigation Efficiency + Business Impact Benchmark",
            "evaluation_date": pd.Timestamp.now().isoformat(),
            "sample_size": len(overall_results),
            "max_tool_budget_inr": 150.0,
            "human_review_benchmark_inr": 350.0,
            "customer_friction_cost_inr": 1200.0,
            "default_interception_rate": 0.85,
        },
        "slices": slices_data,
        "workflow_compression_summary": workflow_summary,
        "disclaimer": "Investigation efficiency metrics are derived from deterministic playback across verified evaluation slices.",
    }

    # 7. Persist Output File
    out_path = REPO_ROOT / "ml" / "data" / "evaluation" / "investigation_efficiency.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\n[SAVED] Persisted Stage 15 evaluation metrics to {out_path}")

    # 8. Print Summary Report
    print("\n" + "=" * 85)
    print("STAGE 15 BENCHMARK RESULTS SUMMARY:")
    print("=" * 85)
    print(f"Total Held-Out Cases Evaluated : {len(overall_results)}")
    print(f"Tool-call reduction vs hypothetical all-9-tool execution: {step_reduction_pct:.2f}% ({avg_steps:.2f} avg steps / case)")
    print(f"Average simulated tool-query cost: INR {avg_cost:.2f} ({cost_savings_pct:.2f}% below the INR 350 human-review benchmark; separate modeled cost categories)")
    print(f"Average Uncertainty Reduction  : {avg_red_u:.4f} ({workflow_summary['relative_uncertainty_reduction_percentage']:.2f}% relative reduction)")
    print("-" * 85)
    for s_name, s_data in slices_data.items():
        print(f"Slice: {s_data['slice_name']:<30} | N={s_data['sample_count']:<4} | Steps={s_data['average_steps']:<4} | Cost=INR {s_data['average_tool_cost']:<6} | U0={s_data['average_initial_uncertainty']:.4f} | Uk={s_data['average_final_uncertainty']:.4f} | dU={s_data['average_uncertainty_reduction']:.4f}")
    print("=" * 85)

    db.close()


if __name__ == "__main__":
    main()
