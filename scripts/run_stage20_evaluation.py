"""RingGuard AI — Stage 20 Outcome Verification & Drift Monitoring Benchmark.

Evaluates distribution drift across all 15 core features between
Reference Train (N=1400) and Comparison Test (N=300), and validates
post-decision outcome verification across all 300 held-out test cases.

Label: SIMULATED / SYNTHETIC BENCHMARK
"""

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.monitoring.service import DriftMonitoringService, OutcomeVerificationService
from app.monitoring.schemas import DriftStatus, OutcomeStatus

FROZEN_FILES = {
    "model_a": {
        "path": REPO_ROOT / "models" / "ringguard_baseline_xgb_v1.joblib",
        "expected_hash": "ed8fa6e28177614e7fd494767e74ed9987a54b23a38ada74efe5a8cb8a7b06f0",
    },
    "model_b": {
        "path": REPO_ROOT / "models" / "ringguard_graph_xgb_v1.joblib",
        "expected_hash": "3ddd77d9caa27e65f7369ecd9e1cb6267404f4ff73a132a2b735f5da4568752e",
    },
    "calibrator_a": {
        "path": REPO_ROOT / "models" / "calibrator_model_a.joblib",
        "expected_hash": "f5a1692e98b73fb8d46f99c67b873f41a74c1e4d53918aecbf56a6ed2518e83f",
    },
    "calibrator_b": {
        "path": REPO_ROOT / "models" / "calibrator_model_b.joblib",
        "expected_hash": "9539db0ebbc35c545623a0edab8e6676410cee9bcb9ad3ce85bc360e33c4ec3d",
    },
    "v1_investigation_benchmark": {
        "path": REPO_ROOT / "ml" / "data" / "evaluation" / "investigation_efficiency.json",
        "expected_hash": "948d22df7563cba7397364a7b499992bbbbd5cae2d6b629307b8a91bf2e294a9",
    },
    "stage17_benchmark": {
        "path": REPO_ROOT / "ml" / "data" / "evaluation" / "stage17_investigation_benchmark.json",
        "expected_hash": "a6387bb7e01c7210aee2fe4993780941696767bb4d66e93a986fa8da457a9837",
    },
    "stage18_benchmark": {
        "path": REPO_ROOT / "ml" / "data" / "evaluation" / "stage18_counterfactual_benchmark.json",
        "expected_hash": "1ba21990fa2ca0d2fe2082362f9106a994863411a35f7df1e9279e5284a93ded",
    },
}


def get_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def verify_frozen_hashes() -> None:
    """Verify that all 7 frozen artifacts are byte-for-byte identical to baseline."""
    for name, spec in FROZEN_FILES.items():
        actual_hash = get_file_sha256(spec["path"])
        if actual_hash != spec["expected_hash"]:
            raise ValueError(
                f"Frozen artifact '{name}' was modified!\n"
                f"Expected: {spec['expected_hash']}\n"
                f"Actual:   {actual_hash}"
            )


def main():
    print("=" * 80)
    print("RINGGUARD AI — STAGE 20 OUTCOME VERIFICATION & DRIFT MONITORING BENCHMARK")
    print("=" * 80)

    # 1. Verify frozen artifacts before execution
    print("\n[INFO] Verifying all 7 frozen baseline artifacts...")
    verify_frozen_hashes()
    print("[PASS] All 7 frozen artifacts verified byte-for-byte intact.")

    # 2. Evaluate distribution drift
    print("\n[INFO] Initializing Drift Monitoring Engine...")
    t0 = time.perf_counter()
    drift_service = DriftMonitoringService()
    drift_res = drift_service.evaluate_distribution_drift(
        reference_window="train",
        comparison_window="test",
    )
    drift_elapsed = time.perf_counter() - t0
    print(f"[PASS] Distribution drift evaluated in {drift_elapsed:.3f}s")
    print(f"       Overall Drift Status: {drift_res.overall_status.value}")
    print(f"       Monitored Features:   {len(drift_res.metrics)}")
    print(f"       Significant Drift:    {len(drift_res.significant_features)} features ({', '.join(drift_res.significant_features) or 'None'})")
    print(f"       Watch Status:         {len(drift_res.watch_features)} features ({', '.join(drift_res.watch_features) or 'None'})")

    # 3. Evaluate outcome verification across all 300 held-out test cases
    print("\n[INFO] Initializing Outcome Verification Service...")
    t1 = time.perf_counter()
    outcome_service = OutcomeVerificationService(db=None)

    test_df = drift_service.partitions["test"]
    test_txn_ids = list(test_df.index)
    total_test = len(test_txn_ids)
    print(f"[INFO] Verifying outcomes for {total_test} held-out test cases...")

    verified_cases: Dict[str, Any] = {}
    confirmed_count = 0
    match_count = 0
    operational_unavailable_count = 0

    for idx, tx_id in enumerate(test_txn_ids):
        # Simulated benchmark verification
        res_sim = outcome_service.verify_transaction_outcome(tx_id, evaluation_context="SIMULATED_BENCHMARK")
        # Operational verification (to prove operational context strictly returns UNAVAILABLE)
        res_ops = outcome_service.verify_transaction_outcome(tx_id, evaluation_context="OPERATIONAL")

        assert res_ops.outcome_status == OutcomeStatus.OUTCOME_UNAVAILABLE
        assert res_ops.observed_outcome is None
        operational_unavailable_count += 1

        if res_sim.outcome_status == OutcomeStatus.OUTCOME_CONFIRMED:
            confirmed_count += 1
            if res_sim.outcome_match:
                match_count += 1

        verified_cases[tx_id] = {
            "transaction_id": tx_id,
            "prediction_at_decision": res_sim.prediction_at_decision,
            "observed_outcome": res_sim.observed_outcome,
            "outcome_status": res_sim.outcome_status.value,
            "outcome_match": res_sim.outcome_match,
            "operational_status": res_ops.outcome_status.value,
            "verification_source": res_sim.verification_source,
            "human_review_required": res_sim.human_review_required,
        }

    outcome_elapsed = time.perf_counter() - t1
    total_elapsed = drift_elapsed + outcome_elapsed

    confirmation_rate = round((confirmed_count / total_test) * 100.0, 2)
    match_rate = round((match_count / confirmed_count) * 100.0, 2) if confirmed_count > 0 else 0.0

    print(f"[PASS] Outcome verification completed in {outcome_elapsed:.3f}s")
    print(f"       Total Cases Evaluated: {total_test}")
    print(f"       Confirmed Outcomes:    {confirmed_count}/{total_test} ({confirmation_rate}%)")
    print(f"       Prediction/Outcome Match Rate: {match_rate}%")
    print(f"       Operational Protection: {operational_unavailable_count}/{total_test} strictly OUTCOME_UNAVAILABLE")

    # 4. Verify post-execution frozen hashes
    print("\n[INFO] Verifying frozen artifacts post-execution...")
    verify_frozen_hashes()
    print("[PASS] Zero model or calibrator mutation confirmed.")

    # 5. Assemble JSON benchmark payload
    metrics_list = [m.model_dump(mode="json") for m in drift_res.metrics]

    benchmark_output = {
        "benchmark_name": "stage20_outcome_verification_drift_monitoring",
        "benchmark_label": "SIMULATED / SYNTHETIC BENCHMARK",
        "monitoring_version": "v1.0.0-monitoring-verification",
        "evaluation_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "drift_summary": {
            "overall_status": drift_res.overall_status.value,
            "reference_window": drift_res.reference_window,
            "comparison_window": drift_res.comparison_window,
            "reference_sample_size": 1400,
            "comparison_sample_size": 300,
            "total_features_monitored": len(drift_res.metrics),
            "significant_features_count": len(drift_res.significant_features),
            "watch_features_count": len(drift_res.watch_features),
            "significant_features": drift_res.significant_features,
            "watch_features": drift_res.watch_features,
            "elapsed_seconds": round(drift_elapsed, 4),
        },
        "outcome_verification_summary": {
            "total_cases_evaluated": total_test,
            "confirmed_outcomes_count": confirmed_count,
            "confirmation_rate": confirmation_rate,
            "prediction_outcome_match_rate": match_rate,
            "operational_unavailable_rate": 100.0,
            "elapsed_seconds": round(outcome_elapsed, 4),
            "mean_latency_ms": round((outcome_elapsed / total_test) * 1000.0, 2),
        },
        "safety_invariants": {
            "human_review_required": True,
            "execution_status": "NOT_EXECUTED",
            "autonomous_action_taken": False,
            "zero_database_mutation": True,
            "zero_model_mutation": True,
            "operational_leakage_prevented": True,
        },
        "feature_metrics": metrics_list,
        "cases_evaluated": verified_cases,
    }

    out_file = REPO_ROOT / "ml" / "data" / "evaluation" / "stage20_monitoring_benchmark.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_output, f, indent=2)

    print(f"\n[PASS] Stage 20 benchmark successfully saved to:\n       {out_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
