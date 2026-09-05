"""RingGuard AI — Controlled Investigation Tool Schemas.

Stage 10: Controlled Investigation Tools.
Defines Pydantic data models for deterministic, bounded, read-only investigation tools.
Strictly excludes synthetic scenario_type, scenario_id, and ground-truth metadata.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ToolExecutionStatus(str, Enum):
    """Execution status for investigation tools."""
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT_FOUND"
    EMPTY = "EMPTY"
    LIMITED = "LIMITED"
    INVALID_INPUT = "INVALID_INPUT"
    UNAVAILABLE = "UNAVAILABLE"


class ToolExecutionResult(BaseModel):
    """Standardized envelope for all investigation tool executions."""
    tool_name: str = Field(
        ...,
        description="Name of the executed controlled tool."
    )
    status: ToolExecutionStatus = Field(
        ...,
        description="Execution status code."
    )
    target: str = Field(
        ...,
        description="Target entity ID (account_id or transaction_id)."
    )
    as_of: Optional[str] = Field(
        None,
        description="Point-in-time evaluation timestamp applied (t <= as_of)."
    )
    result: Any = Field(
        None,
        description="Structured data payload containing verified facts."
    )
    result_count: int = Field(
        0,
        description="Number of records returned in result."
    )
    source: str = Field(
        ...,
        description="Underlying source subsystem (e.g. 'database.accounts', 'stage9.evidence_engine')."
    )
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Resolved Stage 9 evidence IDs backed by genuine evidence objects (empty list if none exist)."
    )
    limitations: Optional[str] = Field(
        None,
        description="Explicit bounds applied (e.g. limits, depth, temporal boundaries)."
    )
    error_details: Optional[str] = Field(
        None,
        description="Structured error details when status != SUCCESS."
    )
    disclaimer: str = Field(
        "Controlled read-only investigation tool output. Analytical facts only. Does not constitute an automated fraud determination or enforcement decision.",
        description="Mandatory defense-only analytical boundary notice."
    )


# ==============================================================================
# SPECIFIC TOOL PAYLOAD SCHEMAS (STRIPPED OF SCENARIO & GROUND TRUTH METADATA)
# ==============================================================================

class AccountInfoResult(BaseModel):
    """Factual account entity details."""
    account_id: str
    customer_id: str
    account_created_at: str
    account_status: str
    account_type: str


class TransactionRecord(BaseModel):
    """Factual transaction record from database."""
    transaction_id: str
    account_id: str
    timestamp: str
    amount: float
    transaction_type: str
    status: str
    channel: str
    device_id: str
    ip_id: str
    beneficiary_id: Optional[str] = None
    merchant_id: Optional[str] = None


class RelatedAccountRecord(BaseModel):
    """Directly connected account discovered through shared attributes."""
    related_account_id: str
    relationship_type: str
    shared_entity_id: str
    shared_entity_type: str
    supporting_transaction_ids: List[str] = Field(default_factory=list)


class SharedDeviceRecord(BaseModel):
    """Device co-used by the investigated account and other accounts."""
    device_id: str
    device_type: str
    device_os: str
    co_using_accounts: List[str] = Field(default_factory=list)
    supporting_transaction_ids: List[str] = Field(default_factory=list)


class SharedIPRecord(BaseModel):
    """IP address co-used by the investigated account and other accounts."""
    ip_id: str
    ip_address: str
    ip_type: str
    asn_org: str
    country: str
    co_using_accounts: List[str] = Field(default_factory=list)
    supporting_transaction_ids: List[str] = Field(default_factory=list)


class CommonBeneficiaryRecord(BaseModel):
    """Beneficiary recipient receiving funds from multiple accounts."""
    beneficiary_id: str
    beneficiary_type: str
    bank_ifsc_prefix: str
    co_sending_accounts: List[str] = Field(default_factory=list)
    supporting_transaction_ids: List[str] = Field(default_factory=list)


class FundFlowHop(BaseModel):
    """Actual verified financial transfer supported by an underlying transaction record."""
    hop_number: int
    transaction_id: str
    timestamp: str
    amount: float
    source_account_id: str
    beneficiary_id: Optional[str] = None
    merchant_id: Optional[str] = None
    channel: str
    status: str


class RiskFeaturesResult(BaseModel):
    """Stage 8 feature values and derived model evaluation context."""
    transaction_id: str
    model_name: str
    model_version: str
    feature_count: int
    graph_feature_count: int
    features: Dict[str, float]
    predicted_ring_probability: float
    decision_threshold: float = 0.50
    risk_band: str
    note: str = "Derived Machine Learning model evaluation. Contextual risk assessment only, not direct proof of fraud."


# ==============================================================================
# STAGE 12: DETERMINISTIC SYNTHESIZED INVESTIGATOR DOSSIER SCHEMAS
# ==============================================================================

class DossierEvidenceItem(BaseModel):
    """Structured evidence item linked to verified data records."""
    evidence_id: str = Field(..., description="Stage 9 deterministic evidence identifier")
    evidence_type: str = Field(..., description="Observed signal type")
    severity: str = Field(..., description="Assessed priority/severity")
    title: str = Field(..., description="Concise factual headline")
    description: str = Field(..., description="Detailed factual observation")
    related_entities: List[str] = Field(default_factory=list, description="Verified accounts, devices, IPs")
    supporting_transaction_ids: List[str] = Field(default_factory=list, description="Underlying transactions")
    provenance_status: str = Field("VERIFIED", description="Provenance anchor status")


class BenignHypothesisItem(BaseModel):
    """Potential benign alternative explanation requiring human verification."""
    hypothesis_id: str = Field(..., description="Deterministic hypothesis identifier")
    title: str = Field(..., description="Headline of the benign scenario")
    description: str = Field(..., description="Explanation of how observed data could have a legitimate origin")
    triggering_signal: str = Field(..., description="Observed pattern prompting this hypothesis")
    status: str = Field("HYPOTHESIS", description="Always HYPOTHESIS, never asserted as fact")
    disclaimer: str = Field(
        "Potential Benign Explanation — Additional verification required.",
        description="Mandatory hypothesis classification banner"
    )


class RecommendedInquiryItem(BaseModel):
    """Strictly non-autonomous investigative inquiry for human risk analysts."""
    inquiry_id: str = Field(..., description="Deterministic inquiry identifier")
    priority: str = Field(..., description="Triage priority: HIGH, MEDIUM, LOW")
    recommended_action: str = Field(..., description="Specific investigative or verification step")
    target_entity_or_attribute: str = Field(..., description="Target entity or attribute to inspect")
    verification_purpose: str = Field(..., description="Investigative hypothesis being tested")


class InvestigatorDossierResponse(BaseModel):
    """Unified deterministic post-hoc case brief for risk investigations."""
    case_id: str = Field(..., description="Deterministic case identifier (e.g. CASE_TXN_00000203)")
    transaction_id: str = Field(..., description="Primary investigated transaction ID")
    target_account_id: str = Field(..., description="Originating account ID")
    amount: float = Field(..., description="Transaction amount in INR")
    timestamp: str = Field(..., description="Point-in-time timestamp")
    channel: str = Field(..., description="Payment channel (UPI, IMPS, NETBANKING, CARD)")
    status: str = Field("COMPLETED", description="Transaction processing status")
    model_a_probability: float = Field(..., ge=0.0, le=1.0, description="Model A baseline probability")
    model_b_probability: float = Field(..., ge=0.0, le=1.0, description="Model B network-enhanced probability")
    risk_band: str = Field(..., description="Categorical presentation risk band")
    executive_summary: str = Field(..., description="Synthesized factual case brief")
    corroborating_evidence_chain: List[DossierEvidenceItem] = Field(
        default_factory=list, description="Top verified evidence items"
    )
    potential_benign_explanations: List[BenignHypothesisItem] = Field(
        default_factory=list, description="Alternative legitimate hypotheses"
    )
    recommended_follow_up_inquiries: List[RecommendedInquiryItem] = Field(
        default_factory=list, description="Human analyst verification checklist"
    )
    markdown_dossier: str = Field(
        ..., description="Pre-formatted Markdown document ready for 1-click clipboard copying"
    )
    disclaimer: str = Field(
        "Analytical investigation dossier prepared for human risk analysts. Contains no automated blocking, throttling, or autonomous enforcement actions.",
        description="Regulatory boundary statement"
    )


# ==============================================================================
# STAGE 15: BOUNDED UNCERTAINTY INVESTIGATION AGENT SCHEMAS
# ==============================================================================

class StoppingReason(str, Enum):
    """Explicit deterministic stopping reasons for bounded investigation."""
    SUFFICIENT_EVIDENCE = "SUFFICIENT_EVIDENCE"
    UNCERTAINTY_LOW_ENOUGH = "UNCERTAINTY_LOW_ENOUGH"
    INFORMATION_GAIN_TOO_LOW = "INFORMATION_GAIN_TOO_LOW"
    INVESTIGATION_COST_TOO_HIGH = "INVESTIGATION_COST_TOO_HIGH"
    EVIDENCE_EXHAUSTED = "EVIDENCE_EXHAUSTED"
    CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW = "CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW"
    MAX_INVESTIGATION_STEPS = "MAX_INVESTIGATION_STEPS"
    IN_PROGRESS = "IN_PROGRESS"


class NextBestActionType(str, Enum):
    """Categorical next-best-action recommendations (strictly advisory)."""
    ALLOW = "ALLOW"
    MONITOR = "MONITOR"
    REQUEST_ADDITIONAL_VERIFICATION = "REQUEST_ADDITIONAL_VERIFICATION"
    HOLD_FOR_REVIEW = "HOLD_FOR_REVIEW"
    ESCALATE_TO_ANALYST = "ESCALATE_TO_ANALYST"


class InvestigationTraceStep(BaseModel):
    """Auditable record of a single real executed investigation tool step."""
    step_number: int = Field(..., description="1-indexed sequence number of this investigation step")
    tool_name: str = Field(..., description="Name of executed controlled tool")
    target_id: str = Field(..., description="Entity or transaction ID evaluated")
    simulated_cost: float = Field(..., description="Configured simulated operational query cost in INR")
    expected_information_gain: float = Field(
        ..., ge=0.0, le=1.0, description="Pre-execution expected information gain estimate"
    )
    selection_reason: str = Field(..., description="Deterministic rationale for choosing this tool")
    uncertainty_before: float = Field(..., ge=0.05, le=0.95, description="Investigative uncertainty before step in [0.05, 0.95]")
    uncertainty_after: float = Field(..., ge=0.05, le=0.95, description="Investigative uncertainty after step in [0.05, 0.95]")
    uncertainty_reduction: float = Field(..., description="Net reduction in investigative uncertainty")
    tool_status: str = Field(..., description="Status returned by tool (SUCCESS, EMPTY, LIMITED, etc.)")
    evidence_count: int = Field(..., description="Number of verified factual records or evidence items extracted")
    evidence_summary: str = Field(..., description="Concise factual description of discovered evidence")
    timestamp: str = Field(..., description="ISO execution timestamp")


class NextBestActionResponse(BaseModel):
    """Advisory decision support recommendation for human risk investigator."""
    recommended_action: NextBestActionType = Field(..., description="Recommended action type")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Recommendation confidence level")
    evidence_sufficiency: str = Field(..., description="Categorical evidence sufficiency: HIGH, MODERATE, LOW")
    expected_financial_impact: str = Field(..., description="Factual narrative of estimated economic risk/benefit")
    reason: str = Field(..., description="Core operational justification for recommendation")
    policy_relevant_factors: List[str] = Field(default_factory=list, description="Key criteria driving recommendation")
    human_approval_required: bool = Field(
        True, description="Strict safety flag: human approval is mandatory for any operational/financial action"
    )


class InvestigationStateResponse(BaseModel):
    """Full state envelope of a bounded uncertainty investigation session."""
    transaction_id: str = Field(..., description="Investigated transaction ID")
    account_id: str = Field(..., description="Target account ID")
    exposure_amount: float = Field(..., description="Transaction exposure amount in INR")
    model_a_probability: float = Field(..., ge=0.0, le=1.0, description="Uncalibrated Model A baseline probability")
    model_b_probability: float = Field(..., ge=0.0, le=1.0, description="Uncalibrated Model B graph probability")
    calibrated_risk: float = Field(..., ge=0.0, le=1.0, description="Stage 14 Platt-calibrated probability")
    graph_confidence: str = Field(..., description="Stage 14 graph confidence: UNAVAILABLE, LIMITED, VERIFIED")
    initial_uncertainty: float = Field(
        ..., ge=0.05, le=0.95, description="Prior investigative-state uncertainty before tool executions, bounded strictly in [0.05, 0.95]"
    )
    current_uncertainty: float = Field(
        ..., ge=0.05, le=0.95, description="Current investigative-state uncertainty after completed steps, bounded strictly in [0.05, 0.95]"
    )
    total_uncertainty_reduction: float = Field(..., description="Cumulative reduction in uncertainty")
    step_count: int = Field(..., description="Number of executed investigation steps")
    max_steps: int = Field(5, description="Upper bound on investigation steps")
    total_simulated_tool_cost: float = Field(..., description="Cumulative simulated tool cost in INR")
    max_tool_budget: float = Field(150.0, description="Upper bound on automated tool budget in INR")
    stopping_status: str = Field(..., description="'STOPPED' or 'IN_PROGRESS'")
    stopping_reason: StoppingReason = Field(..., description="Explicit deterministic stopping reason")
    stopping_rationale: str = Field(..., description="Plain-language explanation of stopping trigger")
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Deterministic queue prioritization score")
    trace: List[InvestigationTraceStep] = Field(default_factory=list, description="Ordered real execution trace")
    evidence_collected: List[Dict[str, Any]] = Field(default_factory=list, description="Factual evidence gathered")
    tools_executed: List[str] = Field(default_factory=list, description="List of tools already executed")
    candidate_tools_remaining: List[str] = Field(default_factory=list, description="Tools eligible for execution")
    next_best_action: NextBestActionResponse = Field(..., description="Advisory recommendation with human approval flag")
    modeled_economics: Dict[str, Any] = Field(default_factory=dict, description="Stage 12/14 compatible economic estimates")
    disclaimer: str = Field(
        "Bounded uncertainty investigation output. Factual analysis only. All next-best-action recommendations are advisory and strictly require human approval.",
        description="Mandatory defense-only regulatory notice"
    )


class CasePriorityItem(BaseModel):
    """Prioritized case item for triage queue."""
    transaction_id: str
    account_id: str
    timestamp: str
    amount: float
    calibrated_risk: float
    investigative_uncertainty: float = Field(..., ge=0.05, le=0.95, description="Initial investigative uncertainty in [0.05, 0.95]")
    network_leverage: float
    priority_score: float
    triage_rank: int
    recommended_action: str
    priority_reason: str


class CasePrioritizationResponse(BaseModel):
    """Response envelope for case triage prioritization queue."""
    total_pending_cases: int
    cases: List[CasePriorityItem]
    prioritization_formula: str = Field(
        "Priority = 0.35 * Risk + 0.30 * min(Amount, 100000)/100000 + 0.20 * Uncertainty + 0.15 * min(1.0, g_connected_accounts_count/10.0)",
        description="Deterministic formula used for case ranking"
    )
    disclaimer: str = Field(
        "Triage prioritization scoring for investigator workflow optimization. Does not execute autonomous decisions.",
        description="Defense-only disclaimer"
    )


class InvestigationEfficiencySlice(BaseModel):
    """Efficiency and uncertainty reduction metrics for an evaluation slice."""
    slice_name: str
    sample_count: int
    average_steps: float
    median_steps: float
    average_initial_uncertainty: float = Field(..., ge=0.05, le=0.95, description="Average initial uncertainty in [0.05, 0.95]")
    average_final_uncertainty: float = Field(..., ge=0.05, le=0.95, description="Average final uncertainty in [0.05, 0.95]")
    average_uncertainty_reduction: float
    average_tool_cost: float
    stopping_reason_distribution: Dict[str, int]
    action_distribution: Dict[str, int]


class InvestigationEfficiencyResponse(BaseModel):
    """Response envelope for Stage 15 sliced investigation efficiency metrics."""
    status: str
    metadata: Dict[str, Any]
    slices: Dict[str, InvestigationEfficiencySlice]
    workflow_compression_summary: Dict[str, Any]
    disclaimer: str = Field(
        "Investigation efficiency metrics are derived from deterministic playback across verified evaluation slices.",
        description="Disclaimer"
    )


class RunInvestigationRequest(BaseModel):
    """Request payload to initiate bounded uncertainty investigation."""
    transaction_id: str = Field(..., min_length=3, max_length=64, description="Transaction ID to investigate")
    max_steps: Optional[int] = Field(5, ge=1, le=9, description="Maximum allowed investigation steps (1-9)")
    tool_budget: Optional[float] = Field(150.0, ge=15.0, le=500.0, description="Tool budget in INR")
    interception_rate: Optional[float] = Field(0.85, ge=0.50, le=1.00, description="Assumed interception rate (50%-100%)")


# ==============================================================================
# STAGE 17: UNCERTAINTY-DRIVEN INVESTIGATION DATA CONTRACTS
# ==============================================================================

class EvidenceQualityType(str, Enum):
    """Classification of evidence quality obtained from tool execution."""
    STRONG = "STRONG"
    WEAK_OR_EMPTY = "WEAK_OR_EMPTY"
    CONFLICTING = "CONFLICTING"


class AdaptiveInvestigationStep(BaseModel):
    """Step record within an uncertainty-driven investigation trace."""
    step_number: int = Field(..., ge=1, le=9, description="1-indexed sequence number of the investigation step.")
    tool_name: str = Field(..., description="Name of the selected controlled investigation tool.")
    target_id: str = Field(..., description="Entity ID queried by the tool (account or transaction).")
    tool_cost: float = Field(..., ge=0.0, description="Simulated tool execution cost in INR.")
    estimated_information_gain: float = Field(..., ge=0.0, le=1.0, description="Pre-execution deterministic information-gain estimate EIG.")
    actual_information_yield: float = Field(..., ge=0.0, le=1.0, description="Post-execution measured information yield.")
    uncertainty_before: float = Field(..., ge=0.05, le=0.95, description="Investigative uncertainty prior to step execution.")
    uncertainty_after: float = Field(..., ge=0.05, le=0.95, description="Investigative uncertainty updated after step execution.")
    uncertainty_reduction: float = Field(..., description="Absolute change in uncertainty (U_before - U_after).")
    evidence_count: int = Field(..., ge=0, description="Count of verified records returned.")
    evidence_ids: List[str] = Field(default_factory=list, description="Stage 9 genuine evidence IDs linked to discovered records.")
    evidence_quality: EvidenceQualityType = Field(..., description="Evidence classification: STRONG, WEAK_OR_EMPTY, CONFLICTING.")
    step_rationale: str = Field(..., description="Concise, non-technical factual explanation of step selection and finding.")
    timestamp: str = Field(..., description="ISO 8601 execution timestamp.")


class AdaptiveInvestigationResponse(BaseModel):
    """Response envelope for Stage 17 uncertainty-driven investigation session."""
    transaction_id: str = Field(..., description="Unique transaction ID under investigation.")
    account_id: str = Field(..., description="Transacting source account ID.")
    timestamp: str = Field(..., description="Target transaction timestamp (ISO 8601). Point-in-time boundary.")
    exposure_amount: float = Field(..., ge=0.0, description="Transaction monetary exposure in INR.")
    calibrated_risk_score: float = Field(..., ge=0.0, le=1.0, description="Model B post-hoc Platt-calibrated risk probability.")
    model_b_raw_probability: float = Field(..., ge=0.0, le=1.0, description="Model B raw (uncalibrated) risk probability.")
    model_a_raw_probability: float = Field(..., ge=0.0, le=1.0, description="Model A baseline raw risk probability.")
    graph_confidence: str = Field(..., description="Stage 14 graph confidence: VERIFIED, LIMITED, UNAVAILABLE.")

    # Uncertainty Tracking
    initial_uncertainty: float = Field(..., ge=0.05, le=0.95, description="Initial investigative uncertainty U_0.")
    final_uncertainty: float = Field(..., ge=0.05, le=0.95, description="Final investigative uncertainty U_k after stopping.")
    uncertainty_reduction: float = Field(..., description="Absolute uncertainty reduction (U_0 - U_k).")
    relative_uncertainty_reduction: float = Field(..., description="Relative reduction = (U_0 - U_k) / U_0.")

    # Step & Budget Tracking
    step_count: int = Field(..., ge=0, le=9, description="Total investigation steps executed.")
    max_steps: int = Field(default=5, description="Maximum allowable steps (5).")
    total_tool_cost: float = Field(..., ge=0.0, le=150.0, description="Sum of tool execution costs in INR (max ₹150.00).")
    max_tool_budget: float = Field(default=150.0, description="Maximum allowed tool budget in INR (₹150.00).")
    selected_tools: List[str] = Field(default_factory=list, description="Ordered sequence of executed tool names.")
    candidate_tools_remaining: List[str] = Field(default_factory=list, description="Eligible tools remaining unexecuted.")

    # Trace & Evidence
    steps: List[AdaptiveInvestigationStep] = Field(default_factory=list, description="Chronological step execution trace.")
    evidence_ids: List[str] = Field(default_factory=list, description="All unique evidence IDs discovered across all steps.")

    # Stopping Decision
    stop_decision: str = Field(..., description="Investigation termination decision: STOP or CONTINUE.")
    stopping_reason: str = Field(..., description="Formal stopping condition trigger.")
    stopping_rationale: str = Field(..., description="Explainable reason why the investigation stopped.")

    # Cross-Stage Integration (Reusing Stages 15 & 16)
    stage15_systemic_anomaly_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Stage 15 multi-scope systemic risk anomaly score.")
    stage16_priority_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Stage 16 deterministic composite portfolio priority score.")
    stage16_expected_value: Optional[float] = Field(None, description="Stage 16 decision-theoretic expected value in INR.")
    stage16_priority_rank: Optional[int] = Field(None, ge=1, description="Stage 16 portfolio priority rank.")

    # Governance & Safety
    human_approval_required: bool = Field(default=True, description="Strict regulatory requirement: human review mandatory before any action.")
    disclaimer: str = Field(
        default="INVESTIGATION DECISION SUPPORT: Read-only investigative uncertainty engine. Does not take autonomous financial or account enforcement actions.",
        description="Regulatory safety disclaimer."
    )


class AdaptiveBenchmarkSlice(BaseModel):
    """Efficiency and uncertainty reduction metrics for an evaluation slice in Stage 17."""
    slice_name: str
    sample_count: int
    average_steps: float
    median_steps: float
    average_initial_uncertainty: float = Field(..., ge=0.05, le=0.95)
    average_final_uncertainty: float = Field(..., ge=0.05, le=0.95)
    average_uncertainty_reduction: float
    relative_uncertainty_reduction: float
    average_tool_cost: float
    evidence_sufficiency_rate: float
    budget_compliance_rate: float
    stopping_reason_distribution: Dict[str, int]


class AdaptiveBenchmarkResponse(BaseModel):
    """Response envelope for Stage 17 uncertainty-driven investigation benchmark."""
    status: str
    metadata: Dict[str, Any]
    slices: Dict[str, AdaptiveBenchmarkSlice]
    comparison_with_v1: Dict[str, Any]
    methodology_notes: str
    disclaimer: str



