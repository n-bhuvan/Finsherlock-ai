"""RingGuard AI — Evidence Engine Schemas.

Stage 9: Evidence + Timeline Engine.
Defines Pydantic data models for structured, traceable evidence items,
deterministic ranking, and analytical investigation responses.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Factual observed signals and analytical context types."""
    # Factual observed infrastructure / behavioral relationships
    SHARED_DEVICE = "SHARED_DEVICE"
    SHARED_IP = "SHARED_IP"
    COMMON_BENEFICIARY = "COMMON_BENEFICIARY"
    RELATED_ACCOUNT = "RELATED_ACCOUNT"
    MULTI_HOP_CONNECTION = "MULTI_HOP_CONNECTION"
    RAPID_FUND_FLOW = "RAPID_FUND_FLOW"
    TRANSACTION_ACTIVITY = "TRANSACTION_ACTIVITY"
    LARGE_INCOMING_TRANSACTION = "LARGE_INCOMING_TRANSACTION"
    ACCOUNT_AGE_CONTEXT = "ACCOUNT_AGE_CONTEXT"
    COORDINATED_TIMING = "COORDINATED_TIMING"
    NETWORK_CONTEXT = "NETWORK_CONTEXT"

    # Derived model analytical context (distinct from observed fraud proof)
    MODEL_RISK_CONTEXT = "MODEL_RISK_CONTEXT"


class EvidenceSeverity(str, Enum):
    """Categorical severity classification for human analyst prioritization."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class EvidenceItem(BaseModel):
    """Structured, verifiable evidence unit tied strictly to underlying records."""
    evidence_id: str = Field(
        ...,
        description="Deterministic identifier derived from underlying entity/transaction keys."
    )
    evidence_type: EvidenceType = Field(
        ...,
        description="Category of the observed signal or analytical context."
    )
    severity: EvidenceSeverity = Field(
        ...,
        description="Priority/severity level for analyst triage."
    )
    title: str = Field(
        ...,
        description="Concise factual headline of the evidence observation."
    )
    description: str = Field(
        ...,
        description="Detailed factual description constructed purely from verified data."
    )
    related_entities: List[str] = Field(
        default_factory=list,
        description="List of real entity identifiers directly involved (accounts, devices, IPs, beneficiaries)."
    )
    supporting_transaction_ids: List[str] = Field(
        default_factory=list,
        description="List of real transaction IDs supporting this observation."
    )
    timestamp_range: Optional[Dict[str, str]] = Field(
        None,
        description="Exact ISO start and end timestamps bounding the observed activity."
    )
    timestamp_source: str = Field(
        ...,
        description="Exact database table/column providing the temporal anchor (e.g. 'transactions.timestamp')."
    )
    source: str = Field(
        ...,
        description="Underlying source subsystem (e.g. 'database.transactions', 'database.devices', 'networkx.graph')."
    )
    status: str = Field(
        "VERIFIED",
        description="Data provenance status ('VERIFIED' when backed by actual records, else 'UNAVAILABLE')."
    )
    relevant_values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Quantitative metrics and attributes extracted from records."
    )
    rank: int = Field(
        ...,
        description="Deterministic priority ranking (1 = highest investigative relevance)."
    )


class EvidenceListResponse(BaseModel):
    """API response envelope for investigation evidence collection."""
    target_id: str = Field(
        ...,
        description="The transaction_id or account_id investigated."
    )
    target_type: str = Field(
        ...,
        description="'transaction' or 'account'."
    )
    timestamp_context: Optional[str] = Field(
        None,
        description="ISO 8601 point-in-time evaluation timestamp (t <= T constraint)."
    )
    total_evidence_items: int = Field(
        ...,
        description="Number of structured evidence items returned."
    )
    items: List[EvidenceItem] = Field(
        default_factory=list,
        description="List of evidence items ordered deterministically by rank."
    )
    disclaimer: str = Field(
        "Analytical evidence extraction only. Describes observed data relationships and does not constitute an automated fraud determination or enforcement decision.",
        description="Mandatory defense-only analytical boundary notice."
    )
