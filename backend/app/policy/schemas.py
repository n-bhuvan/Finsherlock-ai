"""RingGuard AI — Policy Engine & Next-Best-Action Data Contracts.

Stage 19: Deterministic Risk Policy Engine + Next-Best-Action.
Defines typed contracts for human decision-support, policy rules, and auditability.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PolicyAction(str, Enum):
    """Deterministic policy recommendation actions for human analysts."""
    ALLOW = "ALLOW"
    MONITOR = "MONITOR"
    REQUEST_VERIFICATION = "REQUEST_VERIFICATION"
    HOLD_FOR_REVIEW = "HOLD_FOR_REVIEW"
    ESCALATE = "ESCALATE"
    FALLBACK_REVIEW = "FALLBACK_REVIEW"


class ActionPriority(str, Enum):
    """Urgency level of the recommended human analyst action."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM_HIGH = "MEDIUM_HIGH"
    MEDIUM = "MEDIUM"
    LOW_MEDIUM = "LOW_MEDIUM"
    LOW = "LOW"


class HumanReviewRole(str, Enum):
    """Specific organizational human analyst role required for review."""
    SENIOR_RISK_ANALYST = "SENIOR_RISK_ANALYST"
    RISK_ANALYST = "RISK_ANALYST"
    FRAUD_INVESTIGATOR = "FRAUD_INVESTIGATOR"
    AUTOMATED_TELEMETRY_ANALYST = "AUTOMATED_TELEMETRY_ANALYST"
    NONE = "NONE"


class PolicyRuleDefinition(BaseModel):
    """Definition and metadata for a deterministic policy rule."""
    rule_id: str = Field(..., description="Unique canonical policy rule identifier.")
    precedence: int = Field(..., description="1-indexed deterministic evaluation priority.")
    recommended_action: PolicyAction = Field(..., description="Recommended human action.")
    title: str = Field(..., description="Human-readable rule title.")
    condition_description: str = Field(..., description="Exact deterministic condition logic.")
    rationale_template: str = Field(..., description="Explanation template describing why the action was chosen.")
    required_human_role: HumanReviewRole = Field(..., description="Assigned human reviewer role.")
    action_priority: ActionPriority = Field(..., description="Urgency classification.")


class PolicyDecision(BaseModel):
    """Comprehensive Next-Best-Action decision payload for a transaction."""
    transaction_id: str = Field(..., description="Target transaction identifier.")
    account_id: str = Field(..., description="Associated account identifier.")
    timestamp: str = Field(..., description="Point-in-time ISO timestamp enforced.")

    # Core Decision Signals from Preceding Stages
    calibrated_risk_score: float = Field(..., description="Model B post-hoc Platt-calibrated risk probability.")
    expected_value: float = Field(..., description="Decision-theoretic expected value saved in INR.")
    priority_score: float = Field(..., description="Stage 16 composite portfolio prioritization score.")
    systemic_anomaly_score: float = Field(..., description="Stage 15 multi-scope systemic anomaly score.")
    investigative_uncertainty: float = Field(..., description="Stage 17 final investigative uncertainty.")
    evidence_domains: List[str] = Field(default_factory=list, description="Corroborated structural evidence domains (e.g. DEVICE, IP, BENEFICIARY, FUND_FLOW).")
    evidence_count: int = Field(..., ge=0, description="Count of verified evidence records discovered.")
    corroborated_structural_domains: int = Field(..., ge=0, description="Count of distinct structural domains corroborated.")
    has_conflicting_evidence: bool = Field(default=False, description="Whether contradictory or conflicting evidence was discovered.")

    # Next-Best-Action Policy Recommendation
    recommended_action: PolicyAction = Field(..., description="Deterministic human decision recommendation.")
    action_priority: ActionPriority = Field(..., description="Priority classification of the recommendation.")
    policy_rule_id: str = Field(..., description="Identifier of the winning rule that triggered this decision.")
    policy_version: str = Field(default="ringguard_policy_v1", description="Static deterministic policy ruleset version.")
    policy_reason: str = Field(..., description="Clear, factual, non-causal explanation for the decision.")
    required_human_role: HumanReviewRole = Field(..., description="Human role responsible for action.")
    required_verification: str = Field(..., description="Concrete forensic verification steps for the analyst.")

    # Contextual Evidence and Auditability
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="Stage 9 evidence IDs substantiating this policy outcome.")
    blocking_conditions: List[str] = Field(default_factory=list, description="Conditions preventing immediate automated clearance.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Decision confidence = 1.0 - investigative_uncertainty.")

    # Absolute Safety & Governance Boundaries
    human_approval_required: bool = Field(default=True, description="Strict human-in-the-loop requirement. Always True.")
    execution_status: str = Field(default="NOT_EXECUTED", description="Execution boundary flag. Always NOT_EXECUTED.")
    autonomous_action_taken: bool = Field(default=False, description="Strict defense-only flag. Always False.")
    disclaimer: str = Field(..., description="Mandatory operational disclaimer tailored to the recommended action.")

    # Stage 18 Counterfactual Context (Optional summary)
    counterfactual_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Key model sensitivity and top driver context from Stage 18."
    )


class PolicyRulesCatalogResponse(BaseModel):
    """Response schema exposing transparent policy rule specifications and precedence."""
    policy_version: str = Field(default="ringguard_policy_v1", description="Policy version.")
    rule_count: int = Field(..., description="Total count of active deterministic policy rules.")
    precedence_order: List[str] = Field(..., description="Exact evaluation order (precedence 1 to N).")
    rules: List[PolicyRuleDefinition] = Field(..., description="Catalog of deterministic rule specifications.")
