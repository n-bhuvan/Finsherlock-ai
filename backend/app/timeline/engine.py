"""RingGuard AI — Chronological Timeline Engine.

Stage 9: Evidence + Timeline Engine.
Reconstructs verified historical event sequences from PostgreSQL records.
Enforces point-in-time constraints (t <= T) and explicit temporal-source attribution.
Excludes derived model evaluations from the historical event sequence.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.account import Account
from app.timeline.schemas import (
    TimelineEventType,
    TimelineSeverity,
    TimelineEvent,
    TimelineResponse,
)
from app.services.model_service import get_model_service
from app.services.feature_service import get_feature_service


# Deterministic secondary ordering priority when timestamps are identical
EVENT_TYPE_ORDER_PRIORITY = {
    TimelineEventType.ACCOUNT_CREATED: 0,
    TimelineEventType.CONNECTED_ACCOUNT_ACTIVITY: 1,
    TimelineEventType.TRANSACTION: 2,
    TimelineEventType.RAPID_TRANSFER: 2,
    TimelineEventType.LARGE_INCOMING_TRANSACTION: 2,
}


class TimelineEngine:
    """Constructs strictly chronological event sequences up to point-in-time T."""

    def __init__(self, db: Session):
        self.db = db
        self.model_service = get_model_service()
        self.feature_service = get_feature_service()

    def reconstruct_timeline_for_transaction(self, transaction_id: str) -> TimelineResponse:
        """Reconstruct chronological events for the account of transaction T up to time T."""
        tx: Optional[Transaction] = (
            self.db.query(Transaction)
            .filter(Transaction.transaction_id == transaction_id)
            .first()
        )
        if not tx:
            raise KeyError(f"Transaction '{transaction_id}' not found in database.")

        T: datetime = tx.timestamp
        t_iso = T.isoformat()
        account_id = tx.account_id
        events: List[TimelineEvent] = []

        # 1. ACCOUNT CREATION EVENT
        acc: Optional[Account] = (
            self.db.query(Account)
            .filter(Account.account_id == account_id)
            .first()
        )
        if acc:
            acc_created_iso = acc.account_created_at.isoformat()
            events.append(
                TimelineEvent(
                    event_id=f"EVT_ACC_CREATED_{account_id}",
                    event_type=TimelineEventType.ACCOUNT_CREATED,
                    timestamp=acc_created_iso,
                    timestamp_source="accounts.account_created_at",
                    title=f"Account '{account_id}' Registered",
                    description=(
                        f"Account '{account_id}' ({acc.account_type}, status: {acc.account_status}) "
                        f"was created under customer '{acc.customer_id}'."
                    ),
                    related_entities=[account_id, acc.customer_id],
                    supporting_record_ids=[account_id],
                    source="accounts",
                    severity=TimelineSeverity.INFO,
                )
            )

        # 2. HISTORICAL TRANSACTIONS FOR ACCOUNT_ID (t <= T)
        account_txs = (
            self.db.query(Transaction)
            .filter(
                Transaction.account_id == account_id,
                Transaction.timestamp <= T,
            )
            .order_by(Transaction.timestamp.asc())
            .all()
        )

        prev_tx_time: Optional[datetime] = None
        for t in account_txs:
            amt = float(t.amount)
            # Check for rapid transfer burst (<= 15 minutes between consecutive transactions)
            is_burst = prev_tx_time is not None and (t.timestamp - prev_tx_time).total_seconds() <= 900
            prev_tx_time = t.timestamp

            if amt >= 15000.0:
                ev_type = TimelineEventType.LARGE_INCOMING_TRANSACTION
                severity = TimelineSeverity.HIGH if amt >= 25000.0 else TimelineSeverity.MEDIUM
                title = f"High-Value Transaction: {t.transaction_id}"
            elif is_burst:
                ev_type = TimelineEventType.RAPID_TRANSFER
                severity = TimelineSeverity.MEDIUM
                title = f"Rapid Transfer: {t.transaction_id}"
            else:
                ev_type = TimelineEventType.TRANSACTION
                severity = TimelineSeverity.LOW
                title = f"Transaction: {t.transaction_id}"

            entities = [t.account_id, t.device_id, t.ip_id]
            if t.beneficiary_id:
                entities.append(t.beneficiary_id)
            if t.merchant_id:
                entities.append(t.merchant_id)

            events.append(
                TimelineEvent(
                    event_id=f"EVT_TXN_{t.transaction_id}",
                    event_type=ev_type,
                    timestamp=t.timestamp.isoformat(),
                    timestamp_source="transactions.timestamp",
                    title=title,
                    description=(
                        f"Transaction {t.transaction_id}: INR {amt:,.2f} via {t.channel} "
                        f"(Type: {t.transaction_type}, Status: {t.status}, Device: {t.device_id}, IP: {t.ip_id})."
                    ),
                    related_entities=entities,
                    supporting_record_ids=[t.transaction_id],
                    source="transactions",
                    severity=severity,
                )
            )

        # 3. CONNECTED ACCOUNT ACTIVITY ON SHARED INFRASTRUCTURE (t <= T, within 48 hours of T)
        t_48h = T - timedelta(hours=48)
        connected_txs = (
            self.db.query(Transaction)
            .filter(
                (Transaction.device_id == tx.device_id) | (Transaction.ip_id == tx.ip_id),
                Transaction.account_id != account_id,
                Transaction.timestamp >= t_48h,
                Transaction.timestamp <= T,
            )
            .order_by(Transaction.timestamp.asc())
            .all()
        )

        for ct in connected_txs:
            c_amt = float(ct.amount)
            shared_elem = "device" if ct.device_id == tx.device_id else "IP"
            events.append(
                TimelineEvent(
                    event_id=f"EVT_CONN_TXN_{ct.transaction_id}",
                    event_type=TimelineEventType.CONNECTED_ACCOUNT_ACTIVITY,
                    timestamp=ct.timestamp.isoformat(),
                    timestamp_source="transactions.timestamp",
                    title=f"Connected Account Activity: {ct.account_id}",
                    description=(
                        f"Connected account '{ct.account_id}' executed transaction {ct.transaction_id} "
                        f"(INR {c_amt:,.2f}) using shared {shared_elem} ({ct.device_id if shared_elem=='device' else ct.ip_id})."
                    ),
                    related_entities=[ct.account_id, ct.device_id, ct.ip_id],
                    supporting_record_ids=[ct.transaction_id],
                    source="transactions",
                    severity=TimelineSeverity.MEDIUM if c_amt >= 10000.0 else TimelineSeverity.LOW,
                )
            )

        # 4. STRICT CHRONOLOGICAL ORDERING
        sorted_events = self._sort_timeline_events(events)

        # 5. RETRIEVE MODEL RISK CONTEXT (SEPARATE CONTAINER, NOT AN EVENT)
        risk_context: Optional[Dict[str, Any]] = None
        try:
            feats_b, _ = self.feature_service.get_features(self.db, transaction_id, model_type="graph")
            prob_b = self.model_service.predict_graph(feats_b)
            risk_context = {
                "evaluated_at": t_iso,
                "model_name": "ringguard_graph_xgb_v1",
                "predicted_ring_probability": round(prob_b, 6),
                "decision_threshold": 0.50,
                "risk_band": "HIGH" if prob_b >= 0.50 else ("MEDIUM" if prob_b >= 0.20 else "LOW"),
                "note": "Derived Machine Learning evaluation. Kept strictly distinct from real-world timeline events.",
            }
        except Exception:
            pass

        return TimelineResponse(
            target_id=transaction_id,
            target_type="transaction",
            timestamp_context=t_iso,
            total_events=len(sorted_events),
            events=sorted_events,
            risk_context=risk_context,
        )

    def reconstruct_timeline_for_account(self, account_id: str) -> TimelineResponse:
        """Reconstruct timeline for an account using its latest transaction point-in-time."""
        acc: Optional[Account] = (
            self.db.query(Account)
            .filter(Account.account_id == account_id)
            .first()
        )
        if not acc:
            raise KeyError(f"Account '{account_id}' not found in database.")

        latest_tx: Optional[Transaction] = (
            self.db.query(Transaction)
            .filter(Transaction.account_id == account_id)
            .order_by(Transaction.timestamp.desc())
            .first()
        )

        if latest_tx:
            resp = self.reconstruct_timeline_for_transaction(latest_tx.transaction_id)
            resp.target_id = account_id
            resp.target_type = "account"
            return resp

        # Account with zero transactions
        created_at_iso = acc.account_created_at.isoformat()
        single_event = TimelineEvent(
            event_id=f"EVT_ACC_CREATED_{account_id}",
            event_type=TimelineEventType.ACCOUNT_CREATED,
            timestamp=created_at_iso,
            timestamp_source="accounts.account_created_at",
            title=f"Account '{account_id}' Registered",
            description=f"Account '{account_id}' registered under customer '{acc.customer_id}'. Zero transactions recorded.",
            related_entities=[account_id, acc.customer_id],
            supporting_record_ids=[account_id],
            source="accounts",
            severity=TimelineSeverity.INFO,
        )
        return TimelineResponse(
            target_id=account_id,
            target_type="account",
            timestamp_context=created_at_iso,
            total_events=1,
            events=[single_event],
            risk_context=None,
        )

    def _sort_timeline_events(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Sort events strictly by timestamp ascending, with deterministic tie-breaking."""
        def event_key(e: TimelineEvent):
            type_prio = EVENT_TYPE_ORDER_PRIORITY.get(e.event_type, 5)
            # Sort primary by timestamp string (ISO format is lexicographically sortable)
            # Secondary by type priority, tertiary by event_id
            return (e.timestamp, type_prio, e.event_id)

        return sorted(events, key=event_key)
