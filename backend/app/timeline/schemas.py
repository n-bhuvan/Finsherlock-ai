"""RingGuard AI — Timeline Engine Schemas.

Stage 9: Evidence + Timeline Engine.
Defines Pydantic data models for chronological investigation timelines,
strictly grounded in verified database timestamps without invented event times.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TimelineEventType(str, Enum):
    """Factual historical event categories."""
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    TRANSACTION = "TRANSACTION"
    LARGE_INCOMING_TRANSACTION = "LARGE_INCOMING_TRANSACTION"
    RAPID_TRANSFER = "RAPID_TRANSFER"
    CONNECTED_ACCOUNT_ACTIVITY = "CONNECTED_ACCOUNT_ACTIVITY"


class TimelineSeverity(str, Enum):
    """Visual priority level for timeline UI representation."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class TimelineEvent(BaseModel):
    """Chronological event representation grounded strictly in a verified database record."""
    event_id: str = Field(
        ...,
        description="Deterministic identifier derived from underlying primary keys."
    )
    event_type: TimelineEventType = Field(
        ...,
        description="Factual classification of the event."
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp representing the exact instant of the underlying record."
    )
    timestamp_source: str = Field(
        ...,
        description="Exact database table/column providing this timestamp (e.g. 'transactions.timestamp')."
    )
    title: str = Field(
        ...,
        description="Short headline describing the event."
    )
    description: str = Field(
        ...,
        description="Detailed factual description based on verified event attributes."
    )
    related_entities: List[str] = Field(
        default_factory=list,
        description="Entities involved in the event (accounts, devices, IPs, beneficiaries)."
    )
    supporting_record_ids: List[str] = Field(
        default_factory=list,
        description="Underlying primary keys backing this event (e.g. transaction_id)."
    )
    source: str = Field(
        ...,
        description="Originating database table (e.g. 'transactions', 'accounts')."
    )
    severity: TimelineSeverity = Field(
        ...,
        description="Visual indicator level for analyst prioritization."
    )


class TimelineResponse(BaseModel):
    """API response envelope for chronological event reconstruction."""
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
        description="Point-in-time boundary applied (t <= T). Future events are strictly excluded."
    )
    total_events: int = Field(
        ...,
        description="Total number of events reconstructed."
    )
    events: List[TimelineEvent] = Field(
        default_factory=list,
        description="Chronological event sequence strictly sorted by timestamp ascending."
    )
    risk_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Separate derived model assessment metadata from Stage 8 (isolated from historical events)."
    )
    disclaimer: str = Field(
        "Chronological timeline reconstruction based on verified database records up to the investigation timestamp. Derived model evaluations are isolated from historical events.",
        description="Mandatory defense-only analytical boundary notice."
    )
