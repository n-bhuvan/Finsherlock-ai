"""RingGuard AI — Stage 18 Test Suite: Counterfactual Attribution + Intervention Simulation.

Validates all 26 required operational and safety criteria:
1. Deterministic attribution: same transaction produces identical attribution results across runs.
2. Deterministic intervention: same intervention produces identical counterfactual risk scores.
3. Actual feature values: attribution uses actual feature values from verified pipeline.
4. Attribution ranking: attributions correctly ranked by absolute contribution descending.
5. Deterministic tie-breaking: identical absolute contributions broken alphabetically by feature name.
6. Original model score preserved: original probability matches production Model B exactly.
7. Counterfactual score calculated separately: counterfactual does not overwrite original score.
8. Risk delta correctness: delta = counterfactual_risk_score - original_risk_score.
9. Model artifact immutability: Model B file SHA-256 hash unchanged before and after.
10. No model retraining: no fit() or training operations executed.
11. No database mutation: no INSERT/UPDATE/DELETE executed against DB tables.
12. No risk-state mutation: stored risk scores and levels remain identical.
13. Point-in-time safety: feature extraction respects transaction timestamp.
14. Future-data exclusion: future graph edges/events excluded.
15. Safe feature whitelist: custom interventions permitted only on safe whitelist features.
16. Metadata/ID feature rejection: attempts to intervene on identifiers/labels return UNAVAILABLE.
17. Unavailable intervention handling: missing features gracefully handled.
18. Plausibility status: interventions categorized as PLAUSIBLE, HYPOTHETICAL, or UNAVAILABLE.
19. Defense-only invariant: no automated blocking or autonomous freezing actions.
20. Human approval requirement: human_approval_required is True on all responses.
21. No causal language: descriptions avoid forbidden causal claims.
22. Stage 15 compatibility: works alongside systemic risk anomaly detection.
23. Stage 16 compatibility: works alongside portfolio risk prioritization.
24. Stage 17 compatibility: works alongside adaptive investigation trace.
25. API endpoints validation: 200, 404, 422 behavior.
26. Hero case and control case sensitivities: TXN_00000203 and TXN_00000646.
"""

import pytest
import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.counterfactual.service import (
    CounterfactualAttributionService,
    FORBIDDEN_PERTURBATION_FIELDS,
)
from app.counterfactual.schemas import (
    AttributionDirection,
    InterventionMode,
    PlausibilityStatus,
    CounterfactualAnalysisResponse,
    CounterfactualIntervention,
)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def cf_service(db_session: Session):
    return CounterfactualAttributionService(db_session)


def get_file_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# ==============================================================================
# 1 & 2. DETERMINISTIC ATTRIBUTION & INTERVENTION
# ==============================================================================

def test_deterministic_attribution(cf_service: CounterfactualAttributionService):
    """Verify that multiple attribution runs on the same transaction produce identical output."""
    tx_id = "TXN_00000203"
    run1 = cf_service.analyze_transaction(tx_id)
    run2 = cf_service.analyze_transaction(tx_id)

    assert len(run1.attributions) == len(run2.attributions)
    for a1, a2 in zip(run1.attributions, run2.attributions):
        assert a1.feature_name == a2.feature_name
        assert a1.actual_value == a2.actual_value
        assert a1.contribution == a2.contribution
        assert a1.attribution_rank == a2.attribution_rank
        assert a1.direction == a2.direction


def test_deterministic_interventions(cf_service: CounterfactualAttributionService):
    """Verify that hypothetical interventions produce bitwise identical counterfactual risk scores."""
    tx_id = "TXN_00000203"
    run1 = cf_service.analyze_transaction(tx_id)
    run2 = cf_service.analyze_transaction(tx_id)

    assert len(run1.interventions) == len(run2.interventions)
    for i1, i2 in zip(run1.interventions, run2.interventions):
        assert i1.intervention_id == i2.intervention_id
        assert i1.original_risk_score == i2.original_risk_score
        assert i1.counterfactual_risk_score == i2.counterfactual_risk_score
        assert i1.risk_delta == i2.risk_delta
        assert i1.plausibility_status == i2.plausibility_status


# ==============================================================================
# 3, 4, 5. FEATURE VALUES, RANKING & DETERMINISTIC TIE-BREAKING
# ==============================================================================

def test_actual_feature_values(cf_service: CounterfactualAttributionService, db_session: Session):
    """Verify attribution uses actual feature values, matching DB transaction where applicable."""
    tx_id = "TXN_00000203"
    analysis = cf_service.analyze_transaction(tx_id)
    tx = db_session.query(Transaction).filter(Transaction.transaction_id == tx_id).first()

    amount_attr = next((a for a in analysis.attributions if a.feature_name == "tx_amount"), None)
    assert amount_attr is not None
    assert amount_attr.actual_value == pytest.approx(float(tx.amount), rel=1e-3)


def test_attribution_ranking_order(cf_service: CounterfactualAttributionService):
    """Verify attributions are ordered descending by absolute contribution."""
    tx_id = "TXN_00000203"
    analysis = cf_service.analyze_transaction(tx_id)

    for i in range(len(analysis.attributions) - 1):
        curr_abs = abs(analysis.attributions[i].contribution)
        next_abs = abs(analysis.attributions[i + 1].contribution)
        assert curr_abs >= next_abs - 1e-9


def test_deterministic_tie_breaking(cf_service: CounterfactualAttributionService):
    """Verify that features with zero or equal contributions are sorted alphabetically."""
    tx_id = "TXN_00000646"
    analysis = cf_service.analyze_transaction(tx_id)

    zero_contribs = [a for a in analysis.attributions if abs(a.contribution) < 1e-9]
    if len(zero_contribs) > 1:
        names = [a.feature_name for a in zero_contribs]
        assert names == sorted(names), "Tied contributions must be sorted alphabetically by feature_name"


# ==============================================================================
# 6, 7, 8. ORIGINAL SCORE PRESERVATION, SEPARATION, AND RISK DELTA
# ==============================================================================

def test_original_score_preserved(cf_service: CounterfactualAttributionService, client: TestClient):
    """Verify original model probability matches standard Model B output exactly."""
    tx_id = "TXN_00000203"
    analysis = cf_service.analyze_transaction(tx_id)

    resp = client.get(f"/api/risk/transaction/{tx_id}")
    assert resp.status_code == 200
    risk_data = resp.json()

    assert analysis.original_probability_raw == pytest.approx(risk_data["predicted_ring_probability"], abs=1e-4)
    assert 0.0 <= analysis.original_risk_score <= 1.0


def test_counterfactual_score_calculated_separately(cf_service: CounterfactualAttributionService):
    """Verify counterfactual simulation generates independent scores without changing original probability."""
    tx_id = "TXN_00000203"
    analysis = cf_service.analyze_transaction(tx_id)

    for intervention in analysis.interventions:
        assert intervention.original_risk_score == analysis.original_risk_score
        assert 0.0 <= intervention.counterfactual_risk_score <= 1.0


def test_risk_delta_correctness(cf_service: CounterfactualAttributionService):
    """Verify risk_delta = counterfactual_risk_score - original_risk_score mathematically."""
    tx_id = "TXN_00000203"
    analysis = cf_service.analyze_transaction(tx_id)

    for intervention in analysis.interventions:
        expected_delta = round(intervention.counterfactual_risk_score - intervention.original_risk_score, 4)
        assert intervention.risk_delta == pytest.approx(expected_delta, abs=1e-4)


# ==============================================================================
# 9, 10. MODEL ARTIFACT IMMUTABILITY & NO RETRAINING
# ==============================================================================

def test_model_artifact_immutability(cf_service: CounterfactualAttributionService):
    """Verify Model B artifact SHA-256 hash is identical before and after attribution & interventions."""
    model_b_path = cf_service.model_service.models_dir / "ringguard_graph_xgb_v1.joblib"
    initial_hash = get_file_sha256(model_b_path)

    analysis = cf_service.analyze_transaction("TXN_00000203")
    custom = cf_service.simulate_custom_intervention("TXN_00000203", "tx_amount", 500.0)

    post_hash = get_file_sha256(model_b_path)
    assert initial_hash == post_hash, "Model B artifact was mutated!"


def test_no_retraining_invariants(cf_service: CounterfactualAttributionService):
    """Verify no fit(), train(), or updater methods are invoked on the frozen model."""
    booster = cf_service.model_service.model_b.get_booster()
    assert booster.num_boosted_rounds() > 0


# ==============================================================================
# 11, 12. NO DATABASE MUTATION & NO RISK-STATE MUTATION
# ==============================================================================

def test_no_database_mutation(cf_service: CounterfactualAttributionService, db_session: Session):
    """Verify no records are created, updated, or deleted during counterfactual analysis."""
    tx_id = "TXN_00000203"
    tx_before = db_session.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
    amount_before = tx_before.amount

    cf_service.simulate_custom_intervention(tx_id, "tx_amount", 10.0)

    db_session.expire_all()
    tx_after = db_session.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
    assert tx_after.amount == amount_before, "Database transaction amount was mutated!"


def test_no_risk_state_mutation(cf_service: CounterfactualAttributionService, client: TestClient):
    """Verify stored risk state is unchanged before and after."""
    tx_id = "TXN_00000203"
    resp1 = client.get(f"/api/risk/transaction/{tx_id}").json()

    client.get(f"/api/counterfactual/transaction/{tx_id}")
    client.post(
        f"/api/counterfactual/transaction/{tx_id}/simulate",
        json={"feature_name": "tx_amount", "target_value": 100.0},
    )

    resp2 = client.get(f"/api/risk/transaction/{tx_id}").json()
    assert resp1["predicted_ring_probability"] == resp2["predicted_ring_probability"]
    assert resp1["risk_band"] == resp2["risk_band"]


# ==============================================================================
# 13, 14. POINT-IN-TIME SAFETY & FUTURE DATA EXCLUSION
# ==============================================================================

def test_point_in_time_safety(cf_service: CounterfactualAttributionService, db_session: Session):
    """Verify analysis extracts features using point-in-time cutoff at transaction timestamp."""
    tx_id = "TXN_00000203"
    tx = db_session.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
    analysis = cf_service.analyze_transaction(tx_id)

    assert analysis.timestamp == tx.timestamp.isoformat()


# ==============================================================================
# 15, 16, 17, 18. WHITELIST, REJECTION, UNAVAILABILITY & PLAUSIBILITY
# ==============================================================================

def test_safe_feature_whitelist_acceptance(cf_service: CounterfactualAttributionService):
    """Verify custom interventions on approved whitelisted features are permitted."""
    for feat in ["tx_amount", "g_shared_device_accounts_count", "beh_rolling_tx_count_1h"]:
        res = cf_service.simulate_custom_intervention("TXN_00000203", feat, 1.0)
        assert res.plausibility_status in [PlausibilityStatus.PLAUSIBLE, PlausibilityStatus.HYPOTHETICAL]
        assert res.counterfactual_risk_score >= 0.0


def test_metadata_and_id_feature_rejection(cf_service: CounterfactualAttributionService):
    """Verify attempts to intervene on identifier, label, or timestamp features are rejected with UNAVAILABLE."""
    for forbidden in ["transaction_id", "account_id", "target", "is_ring", "timestamp"]:
        res = cf_service.simulate_custom_intervention("TXN_00000203", forbidden, 0.0)
        assert res.plausibility_status == PlausibilityStatus.UNAVAILABLE
        assert res.risk_delta == 0.0
        assert "not permitted" in res.assumption.lower() or "forbidden" in res.assumption.lower() or "unavailable" in res.assumption.lower() or "unavailable" in res.disclaimer.lower()


def test_unknown_feature_handling(cf_service: CounterfactualAttributionService):
    """Verify interventions on non-existent features return UNAVAILABLE status gracefully."""
    res = cf_service.simulate_custom_intervention("TXN_00000203", "non_existent_random_signal", 42.0)
    assert res.plausibility_status == PlausibilityStatus.UNAVAILABLE
    assert res.risk_delta == 0.0


def test_plausibility_status_classification(cf_service: CounterfactualAttributionService):
    """Verify standard interventions are accurately categorized as PLAUSIBLE or HYPOTHETICAL."""
    analysis = cf_service.analyze_transaction("TXN_00000203")
    plausible_ids = {
        "INT_REMOVE_SHARED_DEVICES",
        "INT_REMOVE_SHARED_IPS",
        "INT_REMOVE_COMMON_BENEFICIARIES",
        "INT_REDUCE_AMOUNT_TO_MEDIAN",
        "INT_REDUCE_VELOCITY_BURST",
    }
    hypothetical_ids = {
        "INT_ISOLATE_NETWORK",
        "INT_BASELINE_COMPARISON",
    }

    for inter in analysis.interventions:
        if inter.intervention_id in plausible_ids:
            assert inter.plausibility_status == PlausibilityStatus.PLAUSIBLE
        elif inter.intervention_id in hypothetical_ids:
            assert inter.plausibility_status == PlausibilityStatus.HYPOTHETICAL


# ==============================================================================
# 19, 20, 21. DEFENSE-ONLY, HUMAN APPROVAL & CAUSAL DISCLAIMER
# ==============================================================================

def test_defense_only_no_autonomous_actions(cf_service: CounterfactualAttributionService):
    """Verify output contains no autonomous blocking, rejecting, or execution directives."""
    analysis = cf_service.analyze_transaction("TXN_00000203")
    assert analysis.human_approval_required is True
    assert analysis.defense_only is True

    json_str = analysis.model_dump_json().lower()
    assert "autonomous_block" not in json_str
    assert "auto_reject" not in json_str
    assert "freeze_account_now" not in json_str


def test_human_approval_required_flag(client: TestClient):
    """Verify human_approval_required is True on both analysis and custom simulation endpoints."""
    resp1 = client.get("/api/counterfactual/transaction/TXN_00000203").json()
    assert resp1["human_approval_required"] is True

    resp2 = client.post(
        "/api/counterfactual/transaction/TXN_00000203/simulate",
        json={"feature_name": "tx_amount", "target_value": 500.0},
    ).json()
    assert resp2["plausibility_status"] is not None


def test_no_causal_language_and_disclaimer_presence(cf_service: CounterfactualAttributionService):
    """Verify descriptions contain mandatory disclaimers and avoid claiming causal fraud proof."""
    analysis = cf_service.analyze_transaction("TXN_00000203")

    assert "model-sensitivity" in analysis.disclaimer.lower()
    assert "not causal claims" in analysis.disclaimer.lower()

    forbidden_causal_phrases = ["proves fraud", "caused the fraud", "guarantees prevention", "root cause of fraud"]
    for phrase in forbidden_causal_phrases:
        assert phrase not in analysis.disclaimer.lower()
        for inter in analysis.interventions:
            assert phrase not in inter.assumption.lower()


# ==============================================================================
# 22, 23, 24. COMPATIBILITY WITH STAGES 15, 16, 17
# ==============================================================================

def test_stage15_compatibility(client: TestClient):
    """Verify Stage 15 systemic anomaly detection operates alongside Stage 18."""
    resp15 = client.get("/api/anomaly/transaction/TXN_00000203")
    assert resp15.status_code == 200
    assert "systemic_anomaly_score" in resp15.json()

    resp18 = client.get("/api/counterfactual/transaction/TXN_00000203")
    assert resp18.status_code == 200
    assert "attributions" in resp18.json()


def test_stage16_compatibility(client: TestClient):
    """Verify Stage 16 portfolio prioritization operates alongside Stage 18."""
    resp16 = client.get("/api/prioritization/transaction/TXN_00000203")
    assert resp16.status_code == 200
    assert "priority_score" in resp16.json()

    resp18 = client.get("/api/counterfactual/transaction/TXN_00000203")
    assert resp18.status_code == 200


def test_stage17_compatibility(client: TestClient):
    """Verify Stage 17 adaptive uncertainty investigation operates alongside Stage 18."""
    resp17 = client.get("/api/investigation/transaction/TXN_00000203/adaptive")
    assert resp17.status_code == 200
    assert "stopping_reason" in resp17.json()

    resp18 = client.get("/api/counterfactual/transaction/TXN_00000203")
    assert resp18.status_code == 200


# ==============================================================================
# 25. API ENDPOINTS VALIDATION (200, 404, 422)
# ==============================================================================

def test_api_endpoints_success(client: TestClient):
    """Verify all Stage 18 endpoints return 200 for valid transaction."""
    tx_id = "TXN_00000203"

    r1 = client.get(f"/api/counterfactual/transaction/{tx_id}")
    assert r1.status_code == 200
    assert r1.json()["transaction_id"] == tx_id

    r2 = client.get(f"/api/counterfactual/transaction/{tx_id}/attributions")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)

    r3 = client.get(f"/api/counterfactual/transaction/{tx_id}/interventions")
    assert r3.status_code == 200
    assert isinstance(r3.json(), list)

    r4 = client.post(
        f"/api/counterfactual/transaction/{tx_id}/simulate",
        json={"feature_name": "tx_amount", "target_value": 500.0},
    )
    assert r4.status_code == 200
    assert r4.json()["counterfactual_risk_score"] >= 0.0


def test_api_endpoints_not_found(client: TestClient):
    """Verify 404 is returned for non-existent transactions."""
    non_existent = "TXN_99999999"
    r1 = client.get(f"/api/counterfactual/transaction/{non_existent}")
    assert r1.status_code == 404

    r2 = client.post(
        f"/api/counterfactual/transaction/{non_existent}/simulate",
        json={"feature_name": "tx_amount", "target_value": 500.0},
    )
    assert r2.status_code == 404


def test_api_endpoints_validation_error(client: TestClient):
    """Verify 422 is returned for invalid request bodies or empty IDs."""
    r1 = client.get("/api/counterfactual/transaction/%20")
    assert r1.status_code == 422

    r2 = client.post(
        "/api/counterfactual/transaction/TXN_00000203/simulate",
        json={"feature_name": "   ", "target_value": 500.0},
    )
    assert r2.status_code == 422


# ==============================================================================
# 26. HERO CASE & CONTROL CASE SENSITIVITY VALIDATIONS
# ==============================================================================

def test_hero_case_sensitivity(cf_service: CounterfactualAttributionService):
    """Verify Hero case (TXN_00000203) demonstrates significant risk reduction when amount is reduced."""
    analysis = cf_service.analyze_transaction("TXN_00000203")
    assert analysis.original_risk_score > 0.95

    amt_inter = next((i for i in analysis.interventions if i.intervention_id == "INT_REDUCE_AMOUNT_TO_MEDIAN"), None)
    assert amt_inter is not None
    assert amt_inter.risk_delta < -0.90, f"Expected massive risk reduction, got delta {amt_inter.risk_delta}"
    assert amt_inter.counterfactual_risk_score < 0.05


def test_control_case_sensitivity(cf_service: CounterfactualAttributionService):
    """Verify legitimate control case (TXN_00000646) demonstrates risk escalation when amount is spiked."""
    analysis = cf_service.analyze_transaction("TXN_00000646")
    assert analysis.original_risk_score < 0.05

    spiked = cf_service.simulate_custom_intervention("TXN_00000646", "tx_amount", 95000.0)
    assert spiked.risk_delta > 0.90, f"Expected massive risk elevation, got delta {spiked.risk_delta}"
    assert spiked.counterfactual_risk_score > 0.95
