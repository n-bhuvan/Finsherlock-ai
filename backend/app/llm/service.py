"""RingGuard AI — Stage 16: LLM Explanation Service.

Orchestrates:
1. Canonical risk feature and score extraction (immutability enforcement).
2. Prompt injection defense and input data minimization.
3. Provider execution with automated deterministic fallback.
4. Claim-level grounding validation against EvidenceEngine.
5. Hash-chained append-oriented audit log persistence.
6. Safe, grounded response synthesis.
"""

import time
import uuid
import hashlib
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.services.model_service import get_model_service, ModelService
from app.services.feature_service import get_feature_service, FeatureService
from ml.calibration.calibrator import RiskCalibrator
from app.evidence.engine import EvidenceEngine
from app.llm.schemas import (
    LLMExplanationResponse,
    ExplanationMetadata,
    GroundedClaim,
    ClaimType,
    GroundedEvidenceItem,
    GroundedHypothesisItem,
    GroundingValidationReport,
)
from app.llm.security import SecuritySanitizer
from app.llm.grounding import GroundingValidator
from app.llm.provider import get_llm_provider, DeterministicFallbackProvider, BaseLLMProvider
from app.audit.service import HashChainedAuditService
from ml.evaluation.cold_start import determine_graph_confidence


class LLMExplanationService:
    """Enterprise service for evidence-grounded, auditable LLM forensic explanations."""

    def __init__(
        self,
        model_service: Optional[ModelService] = None,
        feature_service: Optional[FeatureService] = None,
        audit_service: Optional[HashChainedAuditService] = None,
        models_dir: Optional[Any] = None,
    ):
        self.model_service = model_service or get_model_service()
        self.feature_service = feature_service or get_feature_service()
        self.audit_service = audit_service or HashChainedAuditService()
        self.fallback_provider = DeterministicFallbackProvider()

        if models_dir:
            from pathlib import Path
            self.models_dir = Path(models_dir)
        else:
            from pathlib import Path
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]
            self.models_dir = repo_root / "models"

        self.explanations_dir = repo_root / "ml" / "data" / "audit" / "explanations"
        self.explanations_dir.mkdir(parents=True, exist_ok=True)

        self._calibrator_b: Optional[RiskCalibrator] = None
        calib_b_path = self.models_dir / "calibrator_model_b.joblib"
        if calib_b_path.exists():
            try:
                self._calibrator_b = RiskCalibrator.load(calib_b_path)
            except Exception:
                self._calibrator_b = None

    def generate_explanation(
        self,
        db: Session,
        transaction_id: str,
        provider_override: Optional[str] = None,
        force_fallback: bool = False,
    ) -> LLMExplanationResponse:
        """Generate structured forensic explanation with strict grounding and audit logging.
        
        Args:
            db: Active SQLAlchemy database session.
            transaction_id: Target transaction ID.
            provider_override: Optional provider name.
            force_fallback: If True, forces deterministic fallback provider.
            
        Returns:
            LLMExplanationResponse schema with verified claims and audit hashes.
        """
        t_start = time.time()
        audit_id = f"AUD_EXP_{uuid.uuid4().hex[:12].upper()}"

        # 1. Fetch canonical data & compute IMMUTABLE model risk scores
        feats_a, txn = self.feature_service.get_features(db, transaction_id, model_type="baseline")
        feats_b, _ = self.feature_service.get_features(db, transaction_id, model_type="graph")

        model_a_prob = float(self.model_service.predict_baseline(feats_a))
        model_b_prob = float(self.model_service.predict_graph(feats_b))
        calibrated_risk = float(self._calibrator_b.predict_calibrated_proba([model_b_prob])[0]) if self._calibrator_b else model_b_prob
        risk_band = self.model_service.determine_risk_band(model_b_prob).value
        graph_confidence = determine_graph_confidence(feats_b.iloc[0] if hasattr(feats_b, "iloc") else feats_b)

        account_id = txn.account_id
        exposure_amount = float(txn.amount)
        as_of_timestamp = txn.timestamp.isoformat()

        # 2. Extract verified evidence set via EvidenceEngine
        evidence_engine = EvidenceEngine(db)
        verified_evidence = evidence_engine.extract_evidence_for_transaction(transaction_id)

        # 3. Security Pre-Processing: Scan for adversarial prompt injection in inputs
        injection_detected, detected_patterns = SecuritySanitizer.scan_for_prompt_injection(
            f"{transaction_id} {account_id} {txn.channel} {txn.status}"
        )

        is_fallback = force_fallback or injection_detected
        fallback_reason = None

        if injection_detected:
            fallback_reason = f"Prompt-injection attempt detected and neutralized: {detected_patterns}"
            provider = self.fallback_provider
        elif force_fallback:
            fallback_reason = "Deterministic fallback requested by client."
            provider = self.fallback_provider
        else:
            provider = get_llm_provider(provider_override)

        # 4. Execute Provider or Fallback
        raw_dict: Dict[str, Any] = {}
        prompt_used = (
            f"Forensic Explanation Prompt v1.0.0 for {transaction_id} | "
            f"Account: {account_id} | Exposure: ₹{exposure_amount:,.2f} | "
            f"Models: A={model_a_prob:.4f}, B={model_b_prob:.4f}, Cal={calibrated_risk:.4f}"
        )
        prompt_sha256 = hashlib.sha256(prompt_used.encode("utf-8")).hexdigest()

        try:
            raw_dict = provider.generate_raw_explanation(
                transaction_id=transaction_id,
                account_id=account_id,
                exposure_amount=exposure_amount,
                model_a_prob=model_a_prob,
                model_b_prob=model_b_prob,
                calibrated_risk=calibrated_risk,
                risk_band=risk_band,
                graph_confidence=graph_confidence,
                verified_evidence=verified_evidence,
                as_of_timestamp=as_of_timestamp,
            )
        except Exception as err:
            # Fallback on any provider error
            is_fallback = True
            fallback_reason = f"Provider '{provider.provider_name}' error: {str(err)}. Falling back to deterministic rules."
            provider = self.fallback_provider
            raw_dict = provider.generate_raw_explanation(
                transaction_id=transaction_id,
                account_id=account_id,
                exposure_amount=exposure_amount,
                model_a_prob=model_a_prob,
                model_b_prob=model_b_prob,
                calibrated_risk=calibrated_risk,
                risk_band=risk_band,
                graph_confidence=graph_confidence,
                verified_evidence=verified_evidence,
                as_of_timestamp=as_of_timestamp,
            )

        # 5. Parse and Validate Claims
        raw_claims = [
            GroundedClaim(**c) if isinstance(c, dict) else c
            for c in raw_dict.get("structured_claims", [])
        ]
        raw_ev = [
            GroundedEvidenceItem(**e) if isinstance(e, dict) else e
            for e in raw_dict.get("evidence_summaries", [])
        ]
        raw_hyp = [
            GroundedHypothesisItem(**h) if isinstance(h, dict) else h
            for h in raw_dict.get("benign_alternative_hypotheses", [])
        ]

        val_claims, val_ev, val_hyp, report = GroundingValidator.validate_explanation_claims(
            claims=raw_claims,
            evidence_items=raw_ev,
            hypotheses=raw_hyp,
            verified_evidence=verified_evidence,
        )

        # 6. Fallback if severe unsupported claims detected
        if report.unsupported_claims_rejected > 0 and not is_fallback:
            is_fallback = True
            fallback_reason = (
                f"Grounding validation rejected {report.unsupported_claims_rejected} unsupported factual claims. "
                "Activated deterministic verified fallback."
            )
            provider = self.fallback_provider
            raw_dict = provider.generate_raw_explanation(
                transaction_id=transaction_id,
                account_id=account_id,
                exposure_amount=exposure_amount,
                model_a_prob=model_a_prob,
                model_b_prob=model_b_prob,
                calibrated_risk=calibrated_risk,
                risk_band=risk_band,
                graph_confidence=graph_confidence,
                verified_evidence=verified_evidence,
                as_of_timestamp=as_of_timestamp,
            )
            raw_claims = [GroundedClaim(**c) for c in raw_dict.get("structured_claims", [])]
            raw_ev = [GroundedEvidenceItem(**e) for e in raw_dict.get("evidence_summaries", [])]
            raw_hyp = [GroundedHypothesisItem(**h) for h in raw_dict.get("benign_alternative_hypotheses", [])]
            val_claims, val_ev, val_hyp, report = GroundingValidator.validate_explanation_claims(
                claims=raw_claims,
                evidence_items=raw_ev,
                hypotheses=raw_hyp,
                verified_evidence=verified_evidence,
            )

        # 7. Output Sanitization
        exec_summary = SecuritySanitizer.sanitize_output(raw_dict.get("executive_summary", ""))
        risk_narrative = SecuritySanitizer.sanitize_output(raw_dict.get("risk_assessment_narrative", ""))
        topological_ring = SecuritySanitizer.sanitize_output(raw_dict.get("topological_ring_interpretation", ""))
        uncertainty = SecuritySanitizer.sanitize_output(raw_dict.get("uncertainty_and_limitations", ""))
        questions = [
            SecuritySanitizer.sanitize_output(q)
            for q in raw_dict.get("recommended_human_verification_questions", [])
        ]

        latency_ms = (time.time() - t_start) * 1000.0
        response_payload_str = json.dumps({
            "exec": exec_summary,
            "claims": [c.model_dump() for c in val_claims],
            "report": report.model_dump(),
        }, sort_keys=True)
        response_sha256 = hashlib.sha256(response_payload_str.encode("utf-8")).hexdigest()

        meta = ExplanationMetadata(
            provider=provider.provider_name,
            model=provider.model_name,
            prompt_version="v1.0.0-grounded-forensic",
            temperature=0.1,
            latency_ms=round(latency_ms, 2),
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
            prompt_sha256=prompt_sha256,
            response_sha256=response_sha256,
        )

        # 8. Append to Hash-Chained Audit Log
        status_code = "FALLBACK" if is_fallback else "SUCCESS"
        if injection_detected:
            status_code = "INJECTION_DEFENSE_TRIGGERED"

        self.audit_service.append_audit_record(
            audit_id=audit_id,
            transaction_id=transaction_id,
            account_id=account_id,
            provider=provider.provider_name,
            model_name=provider.model_name,
            prompt_version="v1.0.0-grounded-forensic",
            prompt_sha256=prompt_sha256,
            response_sha256=response_sha256,
            latency_ms=latency_ms,
            status=status_code,
            grounding_ratio=report.grounding_ratio,
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
            security_status="SECURE" if not injection_detected else "INJECTION_QUARANTINED",
            human_approval_required=True,
        )

        # 9. Synthesize response with IMMUTABLE risk scores
        response = LLMExplanationResponse(
            transaction_id=transaction_id,
            account_id=account_id,
            executive_summary=exec_summary,
            risk_assessment_narrative=risk_narrative,
            model_a_probability=model_a_prob,
            model_b_probability=model_b_prob,
            calibrated_risk=calibrated_risk,
            risk_band=risk_band,
            graph_confidence=graph_confidence,
            structured_claims=val_claims,
            evidence_summaries=val_ev,
            topological_ring_interpretation=topological_ring,
            benign_alternative_hypotheses=val_hyp,
            recommended_human_verification_questions=questions,
            uncertainty_and_limitations=uncertainty,
            grounding_validation=report,
            metadata=meta,
            audit_id=audit_id,
            human_approval_required=True,
        )

        # 10. Persist generated explanation for retrieval-only GET access
        try:
            saved_file = self.explanations_dir / f"{transaction_id}.json"
            saved_file.write_text(response.model_dump_json(indent=2), encoding="utf-8")
        except Exception:
            pass

        return response

    def get_saved_explanation(self, transaction_id: str) -> Optional[LLMExplanationResponse]:
        """Retrieve previously generated explanation for a specific transaction (Retrieval-Only).
        
        Strictly read-only:
        - Does NOT invoke any LLM provider
        - Does NOT generate explanations
        - Does NOT append to audit log
        - Does NOT mutate audit storage
        """
        saved_file = self.explanations_dir / f"{transaction_id}.json"
        if not saved_file.exists():
            return None
        try:
            content = saved_file.read_text(encoding="utf-8")
            return LLMExplanationResponse.model_validate_json(content)
        except Exception:
            return None

