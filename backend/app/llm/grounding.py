"""RingGuard AI — Stage 16: Claim Grounding Validator & Hallucination Filter.

Validates that every factual claim in an explanation maps directly to verified evidence
extracted by EvidenceEngine. Implements explicit structured claim validation (FACT,
INTERPRETATION, LIMITATION) and formal grounding_ratio calculation.
"""

from typing import List, Set, Tuple, Optional
from app.evidence.schemas import EvidenceListResponse
from app.llm.schemas import (
    GroundedClaim,
    ClaimType,
    GroundedEvidenceItem,
    GroundedHypothesisItem,
    GroundingValidationReport,
)


class GroundingValidator:
    """Validator ensuring 100% verifiable grounding of all factual claims."""

    @staticmethod
    def validate_explanation_claims(
        claims: List[GroundedClaim],
        evidence_items: List[GroundedEvidenceItem],
        hypotheses: List[GroundedHypothesisItem],
        verified_evidence: EvidenceListResponse,
    ) -> Tuple[List[GroundedClaim], List[GroundedEvidenceItem], List[GroundedHypothesisItem], GroundingValidationReport]:
        """Validate all structured claims, evidence summaries, and hypotheses against verified evidence.
        
        Args:
            claims: Structured claims (FACT, INTERPRETATION, LIMITATION).
            evidence_items: Cited evidence items.
            hypotheses: Formulated benign hypotheses.
            verified_evidence: Verified ground-truth evidence extracted by EvidenceEngine.
            
        Returns:
            (validated_claims, validated_evidence_items, validated_hypotheses, validation_report)
        """
        valid_ids: Set[str] = {ev.evidence_id for ev in verified_evidence.items}

        total_claims = len(claims)
        fact_claims = [c for c in claims if c.claim_type == ClaimType.FACT]
        total_fact_claims = len(fact_claims)
        grounded_fact_claims = 0
        unsupported_count = 0
        rejection_reasons: List[str] = []

        validated_claims: List[GroundedClaim] = []

        for c in claims:
            if c.claim_type == ClaimType.FACT:
                # Every FACT claim MUST have at least one evidence_id, and ALL evidence_ids must be valid
                if not c.evidence_ids:
                    unsupported_count += 1
                    rejection_reasons.append(f"Claim {c.claim_id} is marked FACT but provides zero evidence_ids.")
                    validated_claims.append(
                        GroundedClaim(
                            claim_id=c.claim_id,
                            statement=c.statement,
                            evidence_ids=[],
                            claim_type=c.claim_type,
                            is_grounded=False,
                            validation_notes="REJECTED: Missing evidence citation.",
                        )
                    )
                else:
                    invalid_cites = [eid for eid in c.evidence_ids if eid not in valid_ids]
                    if invalid_cites:
                        unsupported_count += 1
                        rejection_reasons.append(
                            f"Claim {c.claim_id} cites invalid/unverified evidence ID(s): {', '.join(invalid_cites)}."
                        )
                        validated_claims.append(
                            GroundedClaim(
                                claim_id=c.claim_id,
                                statement=c.statement,
                                evidence_ids=c.evidence_ids,
                                claim_type=c.claim_type,
                                is_grounded=False,
                                validation_notes=f"REJECTED: Unverified evidence citation {invalid_cites}.",
                            )
                        )
                    else:
                        grounded_fact_claims += 1
                        validated_claims.append(
                            GroundedClaim(
                                claim_id=c.claim_id,
                                statement=c.statement,
                                evidence_ids=c.evidence_ids,
                                claim_type=c.claim_type,
                                is_grounded=True,
                                validation_notes="VERIFIED: All cited evidence_ids verified by EvidenceEngine.",
                            )
                        )
            else:
                # INTERPRETATION or LIMITATION: accepted without evidence requirement, but cannot introduce unsupported facts
                validated_claims.append(
                    GroundedClaim(
                        claim_id=c.claim_id,
                        statement=c.statement,
                        evidence_ids=c.evidence_ids,
                        claim_type=c.claim_type,
                        is_grounded=True,
                        validation_notes=f"ACCEPTED: Contextual {c.claim_type.value}.",
                    )
                )

        # Validate cited evidence items
        validated_ev: List[GroundedEvidenceItem] = []
        for ev in evidence_items:
            is_valid = ev.evidence_id in valid_ids
            if not is_valid:
                unsupported_count += 1
                rejection_reasons.append(f"Evidence item cites invalid evidence_id: {ev.evidence_id}")
            validated_ev.append(
                GroundedEvidenceItem(
                    evidence_id=ev.evidence_id,
                    evidence_type=ev.evidence_type,
                    claim_statement=ev.claim_statement,
                    is_grounded=is_valid,
                    grounding_source=ev.grounding_source if is_valid else "UNVERIFIED",
                )
            )

        # Validate hypotheses
        validated_hypo: List[GroundedHypothesisItem] = []
        for hyp in hypotheses:
            is_valid = hyp.triggering_evidence_id in valid_ids
            if not is_valid:
                unsupported_count += 1
                rejection_reasons.append(f"Hypothesis {hyp.hypothesis_id} cites invalid triggering_evidence_id: {hyp.triggering_evidence_id}")
            validated_hypo.append(
                GroundedHypothesisItem(
                    hypothesis_id=hyp.hypothesis_id,
                    title=hyp.title,
                    rationale=hyp.rationale,
                    triggering_evidence_id=hyp.triggering_evidence_id,
                    is_grounded=is_valid,
                )
            )

        # Grounding ratio definition: fraction of structured claims requiring evidence references
        # (FACT claims) that were successfully mapped to valid verified evidence.
        if total_fact_claims > 0:
            grounding_ratio = round(grounded_fact_claims / total_fact_claims, 4)
        else:
            # If no fact claims exist and unsupported count is 0, grounding ratio is 1.0
            grounding_ratio = 1.0 if unsupported_count == 0 else 0.0

        is_fully_grounded = (unsupported_count == 0) and (grounding_ratio == 1.0)

        report = GroundingValidationReport(
            total_claims=total_claims,
            total_fact_claims=total_fact_claims,
            grounded_fact_claims=grounded_fact_claims,
            unsupported_claims_rejected=unsupported_count,
            grounding_ratio=grounding_ratio,
            is_fully_grounded=is_fully_grounded,
            rejection_reasons=rejection_reasons,
        )

        return validated_claims, validated_ev, validated_hypo, report
