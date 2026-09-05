"""RingGuard AI — Stage 16: LLM Explanation Schemas.

Defines structured Pydantic models for evidence-grounded explanations,
explicit claim-level verification (FACT, INTERPRETATION, LIMITATION),
prompt-injection defense metadata, and audit record envelopes.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    """Classification of structured claims in an AI explanation."""
    FACT = "FACT"
    INTERPRETATION = "INTERPRETATION"
    LIMITATION = "LIMITATION"


class GroundedClaim(BaseModel):
    """Explicit structured claim requiring evidence verification if type is FACT."""
    claim_id: str = Field(..., description="Unique claim identifier, e.g. CLAIM_01")
    statement: str = Field(..., description="The factual or interpretive assertion")
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Verified evidence IDs supporting this claim (mandatory for FACT)",
    )
    claim_type: ClaimType = Field(
        ...,
        description="FACT requires >=1 verified evidence_id; INTERPRETATION/LIMITATION must not introduce unsupported facts",
    )
    is_grounded: bool = Field(False, description="Whether this claim successfully mapped to valid verified evidence")
    validation_notes: Optional[str] = Field(None, description="Grounding validator output notes")


class GroundedEvidenceItem(BaseModel):
    """Verified evidence item cited in the explanation."""
    evidence_id: str = Field(..., description="Verified Stage 9 evidence ID")
    evidence_type: str = Field(..., description="Evidence category, e.g. SHARED_DEVICE, SHARED_IP")
    claim_statement: str = Field(..., description="Factual summary grounded in this evidence record")
    is_grounded: bool = Field(True, description="True if evidence_id exists in verified evidence set")
    grounding_source: str = Field(..., description="Factual source, e.g. EvidenceEngine:SHARED_DEVICE")


class GroundedHypothesisItem(BaseModel):
    """Potential benign hypothesis referencing triggering evidence."""
    hypothesis_id: str = Field(..., description="Hypothesis identifier")
    title: str = Field(..., description="Hypothesis title")
    rationale: str = Field(..., description="Plausible non-fraud explanation")
    triggering_evidence_id: str = Field(..., description="Evidence ID prompting this benign hypothesis")
    is_grounded: bool = Field(True, description="True if triggering_evidence_id exists in verified evidence set")


class GroundingValidationReport(BaseModel):
    """Comprehensive claim-level grounding verification report."""
    total_claims: int = Field(..., description="Total structured claims generated")
    total_fact_claims: int = Field(..., description="Total FACT claims requiring evidence grounding")
    grounded_fact_claims: int = Field(..., description="FACT claims successfully validated against verified evidence")
    unsupported_claims_rejected: int = Field(..., description="Unsupported factual claims detected and rejected")
    grounding_ratio: float = Field(
        ..., ge=0.0, le=1.0,
        description="Fraction of structured claims requiring evidence references that were successfully mapped to valid verified evidence",
    )
    is_fully_grounded: bool = Field(..., description="True only if all FACT claims are verified and unsupported count is 0")
    rejection_reasons: List[str] = Field(default_factory=list, description="Specific rejection rationales for ungrounded claims")


class ExplanationMetadata(BaseModel):
    """Traceable execution and model metadata for explanation auditability."""
    provider: str = Field(..., description="Provider name: deterministic_fallback, gemini, etc.")
    model: str = Field(..., description="Model identifier used")
    prompt_version: str = Field("v1.0.0-grounded-forensic", description="Prompt version tag")
    temperature: float = Field(0.1, description="Sampling temperature")
    latency_ms: float = Field(..., description="Execution latency in milliseconds")
    is_fallback: bool = Field(False, description="Whether deterministic fallback was triggered")
    fallback_reason: Optional[str] = Field(None, description="Reason for fallback if triggered")
    prompt_sha256: str = Field(..., description="SHA-256 hash of input prompt")
    response_sha256: str = Field(..., description="SHA-256 hash of raw output")


class LLMExplanationResponse(BaseModel):
    """Complete evidence-grounded AI forensic explanation response."""
    transaction_id: str = Field(..., description="Target transaction ID")
    account_id: str = Field(..., description="Target account ID")
    executive_summary: str = Field(..., description="High-level factual brief")
    risk_assessment_narrative: str = Field(..., description="Factual narrative explaining model risk context")
    model_a_probability: float = Field(..., ge=0.0, le=1.0, description="Immutable Model A baseline probability")
    model_b_probability: float = Field(..., ge=0.0, le=1.0, description="Immutable Model B network probability")
    calibrated_risk: float = Field(..., ge=0.0, le=1.0, description="Immutable Platt-calibrated risk probability")
    risk_band: str = Field(..., description="Immutable risk band: LOW, MEDIUM, HIGH, CRITICAL")
    graph_confidence: str = Field(..., description="Immutable graph confidence: VERIFIED, LIMITED, UNAVAILABLE")
    structured_claims: List[GroundedClaim] = Field(default_factory=list, description="Explicit structured claim objects")
    evidence_summaries: List[GroundedEvidenceItem] = Field(default_factory=list, description="Directly cited verified evidence items")
    topological_ring_interpretation: str = Field(..., description="Analysis of graph topology and multi-hop structure")
    benign_alternative_hypotheses: List[GroundedHypothesisItem] = Field(default_factory=list, description="Plausible benign alternatives")
    recommended_human_verification_questions: List[str] = Field(default_factory=list, description="Targeted questions for human analyst")
    uncertainty_and_limitations: str = Field(..., description="Explicit statement of model and data boundary limitations")
    grounding_validation: GroundingValidationReport = Field(..., description="Audit report of claim grounding verification")
    metadata: ExplanationMetadata = Field(..., description="Execution and provider metadata")
    audit_id: str = Field(..., description="Unique audit identifier in hash chain")
    human_approval_required: bool = Field(True, description="Strict safety invariant: human approval mandatory")
    disclaimer: str = Field(
        "Factual forensic explanation generated for decision support. Does not constitute an autonomous decision or financial action.",
        description="Regulatory disclaimer",
    )


class GenerateExplanationRequest(BaseModel):
    """Request payload to generate evidence-grounded explanation."""
    transaction_id: str = Field(..., min_length=3, max_length=64, description="Transaction ID to explain")
    provider: Optional[str] = Field(None, description="Optional provider override: 'deterministic', 'gemini'")
    force_fallback: Optional[bool] = Field(False, description="Simulate provider failure and force deterministic fallback")
