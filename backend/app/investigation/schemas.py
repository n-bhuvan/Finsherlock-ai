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
