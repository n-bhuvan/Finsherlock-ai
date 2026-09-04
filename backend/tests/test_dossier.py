"""RingGuard AI — Stage 12 Investigator Dossier Test Suite.

Tests deterministic case brief generation, corroborating evidence chain,
potential benign explanations (hypotheses), non-autonomous recommended inquiries,
and markdown document compilation.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_generate_dossier_hero_case_txn_00000203():
    """Verify structured dossier generation for primary hero case TXN_00000203."""
    response = client.get("/api/investigation/transaction/TXN_00000203/dossier")
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "CASE_TXN_00000203"
    assert data["transaction_id"] == "TXN_00000203"
    assert data["target_account_id"] == "ACC_000213"
    assert data["amount"] == 99500.0
    assert data["channel"] == "IMPS"
    assert data["risk_band"] == "HIGH"
    assert 0.99 <= data["model_a_probability"] <= 1.0
    assert 0.99 <= data["model_b_probability"] <= 1.0

    # Executive summary
    assert "ACC_000213" in data["executive_summary"]
    assert "99,500" in data["executive_summary"]

    # Corroborating evidence chain
    assert len(data["corroborating_evidence_chain"]) > 0
    first_ev = data["corroborating_evidence_chain"][0]
    assert first_ev["evidence_id"].startswith("EVD_")
    assert first_ev["provenance_status"] == "VERIFIED"

    # Benign hypotheses (must be classified as hypotheses)
    assert len(data["potential_benign_explanations"]) > 0
    first_hypo = data["potential_benign_explanations"][0]
    assert first_hypo["status"] == "HYPOTHESIS"
    assert "Additional verification required" in first_hypo["disclaimer"]

    # Recommended inquiries (must be non-autonomous)
    assert len(data["recommended_follow_up_inquiries"]) > 0
    for inq in data["recommended_follow_up_inquiries"]:
        assert inq["priority"] in ("HIGH", "MEDIUM", "LOW")
        assert "recommended_action" in inq
        assert "verification_purpose" in inq
        # Verify no autonomous action keywords exist
        action_text = inq["recommended_action"].lower()
        assert "block payment" not in action_text
        assert "freeze account" not in action_text

    # Markdown dossier content
    md = data["markdown_dossier"]
    assert "# RingGuard AI — Investigator Dossier: CASE_TXN_00000203" in md
    assert "## 1. Case Metadata & Risk Assessment" in md
    assert "## 2. Executive Summary" in md
    assert "## 3. Corroborating Evidence Chain" in md
    assert "## 4. Potential Benign Explanations (Hypotheses)" in md
    assert "## 5. Recommended Follow-up Verification" in md
    assert "Defense-Only Compliance Boundary" in md


def test_generate_dossier_control_case_txn_00000646():
    """Verify dossier generation for low-risk control case TXN_00000646."""
    response = client.get("/api/investigation/transaction/TXN_00000646/dossier")
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "CASE_TXN_00000646"
    assert data["target_account_id"] == "ACC_000054"
    assert data["amount"] == 1159.95
    assert data["channel"] == "NETBANKING"
    assert data["risk_band"] == "LOW"
    assert data["model_a_probability"] < 0.20
    assert data["model_b_probability"] < 0.20


def test_dossier_nonexistent_transaction():
    """Verify 404 for nonexistent transaction."""
    response = client.get("/api/investigation/transaction/TXN_NONEXISTENT_999/dossier")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
