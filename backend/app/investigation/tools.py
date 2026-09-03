"""RingGuard AI — Controlled Investigation Tools Implementation.

Stage 10: Controlled Investigation Tools.
Deterministic, bounded, read-only investigation tools for financial abuse detection.
Strictly relies on parameterized SQLAlchemy queries and verified database records.
Never fabricates evidence IDs, timestamps, amounts, or relationships.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.device import Device
from app.models.ip import IPAddress
from app.models.beneficiary import Beneficiary
from app.evidence.engine import EvidenceEngine
from app.evidence.schemas import EvidenceType
from app.timeline.engine import TimelineEngine
from app.services.model_service import get_model_service
from app.services.feature_service import get_feature_service
from app.investigation.permissions import PermissionGuard
from app.investigation.schemas import (
    ToolExecutionStatus,
    ToolExecutionResult,
    AccountInfoResult,
    TransactionRecord,
    RelatedAccountRecord,
    SharedDeviceRecord,
    SharedIPRecord,
    CommonBeneficiaryRecord,
    FundFlowHop,
    RiskFeaturesResult,
)


def _parse_as_of(as_of: Optional[str]) -> Optional[datetime]:
    """Safely parse ISO as_of string into timezone-aware datetime, handling URL-decoded spaces for +."""
    if not as_of:
        return None
    cleaned = as_of.strip()
    if not cleaned:
        return None
    # Handle URL unencoded plus sign that arrived as a space in timezone offset (e.g. " 05:30")
    if " " in cleaned and ("+" not in cleaned[10:]):
        cleaned = cleaned.replace(" ", "+")
    try:
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return None


# ==============================================================================
# TOOL 1: get_account
# ==============================================================================

def get_account(db: Session, account_id: str, as_of: Optional[str] = None) -> ToolExecutionResult:
    """Retrieve verified factual account metadata without scenario or ground-truth leakage."""
    PermissionGuard.check_permission("INVESTIGATION_READ")
    clean_id = account_id.strip()

    acc: Optional[Account] = (
        db.query(Account)
        .filter(Account.account_id == clean_id)
        .first()
    )
    if not acc:
        return ToolExecutionResult(
            tool_name="get_account",
            status=ToolExecutionStatus.NOT_FOUND,
            target=clean_id,
            as_of=as_of,
            result=None,
            result_count=0,
            source="database.accounts",
            evidence_ids=[],
            error_details=f"Account '{clean_id}' not found in database.",
        )

    as_of_dt = _parse_as_of(as_of)
    if as_of_dt and acc.account_created_at > as_of_dt:
        return ToolExecutionResult(
            tool_name="get_account",
            status=ToolExecutionStatus.NOT_FOUND,
            target=clean_id,
            as_of=as_of,
            result=None,
            result_count=0,
            source="database.accounts",
            evidence_ids=[],
            limitations=f"Account created after point-in-time boundary {as_of}.",
            error_details=f"Account '{clean_id}' did not exist at {as_of}.",
        )

    # Resolve genuine Stage 9 evidence IDs
    evidence_ids: List[str] = []
    try:
        ev_engine = EvidenceEngine(db)
        ev_resp = ev_engine.extract_evidence_for_account(clean_id)
        evidence_ids = [
            i.evidence_id for i in ev_resp.items
            if i.evidence_type == EvidenceType.ACCOUNT_AGE_CONTEXT
        ]
    except Exception:
        evidence_ids = []

    payload = AccountInfoResult(
        account_id=acc.account_id,
        customer_id=acc.customer_id,
        account_created_at=acc.account_created_at.isoformat(),
        account_status=acc.account_status,
        account_type=acc.account_type,
    )

    return ToolExecutionResult(
        tool_name="get_account",
        status=ToolExecutionStatus.SUCCESS,
        target=clean_id,
        as_of=as_of,
        result=payload.model_dump(),
        result_count=1,
        source="database.accounts",
        evidence_ids=evidence_ids,
        limitations="Restricted strictly to operational account schema fields.",
    )


# ==============================================================================
# TOOL 2: get_transactions
# ==============================================================================

def get_transactions(
    db: Session,
    account_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 50,
) -> ToolExecutionResult:
    """Retrieve bounded historical transactions with parameter binding and chronological sorting."""
    PermissionGuard.check_permission("INVESTIGATION_READ")
    clean_id = account_id.strip()

    acc_exists = db.query(Account).filter(Account.account_id == clean_id).count()
    if not acc_exists:
        return ToolExecutionResult(
            tool_name="get_transactions",
            status=ToolExecutionStatus.NOT_FOUND,
            target=clean_id,
            as_of=end_time,
            result=[],
            result_count=0,
            source="database.transactions",
            evidence_ids=[],
            error_details=f"Account '{clean_id}' not found in database.",
        )

    bounded_limit = min(max(1, limit), 100)
    query = db.query(Transaction).filter(Transaction.account_id == clean_id)

    start_dt = _parse_as_of(start_time)
    end_dt = _parse_as_of(end_time)

    if start_dt:
        query = query.filter(Transaction.timestamp >= start_dt)
    if end_dt:
        query = query.filter(Transaction.timestamp <= end_dt)

    txs = query.order_by(Transaction.timestamp.asc()).limit(bounded_limit).all()

    records = [
        TransactionRecord(
            transaction_id=t.transaction_id,
            account_id=t.account_id,
            timestamp=t.timestamp.isoformat(),
            amount=float(t.amount),
            transaction_type=t.transaction_type,
            status=t.status,
            channel=t.channel,
            device_id=t.device_id,
            ip_id=t.ip_id,
            beneficiary_id=t.beneficiary_id,
            merchant_id=t.merchant_id,
        ).model_dump()
        for t in txs
    ]

    # Resolve genuine Stage 9 evidence IDs
    evidence_ids: List[str] = []
    try:
        ev_engine = EvidenceEngine(db)
        ev_resp = ev_engine.extract_evidence_for_account(clean_id)
        evidence_ids = [
            i.evidence_id for i in ev_resp.items
            if i.evidence_type in (EvidenceType.RAPID_FUND_FLOW, EvidenceType.LARGE_INCOMING_TRANSACTION)
        ]
    except Exception:
        evidence_ids = []

    status = (
        ToolExecutionStatus.EMPTY if len(records) == 0
        else (ToolExecutionStatus.LIMITED if len(records) == bounded_limit else ToolExecutionStatus.SUCCESS)
    )

    return ToolExecutionResult(
        tool_name="get_transactions",
        status=status,
        target=clean_id,
        as_of=end_time,
        result=records,
        result_count=len(records),
        source="database.transactions",
        evidence_ids=evidence_ids,
        limitations=f"Bounded to limit={bounded_limit} items. Ordered by timestamp ASC.",
    )


# ==============================================================================
# TOOL 3: find_related_accounts
# ==============================================================================

def find_related_accounts(
    db: Session,
    account_id: str,
    as_of: Optional[str] = None,
    limit: int = 20,
) -> ToolExecutionResult:
    """Discover accounts connected via shared devices, IPs, or common beneficiaries."""
    PermissionGuard.check_permission("INVESTIGATION_READ")
    clean_id = account_id.strip()

    acc = db.query(Account).filter(Account.account_id == clean_id).first()
    if not acc:
        return ToolExecutionResult(
            tool_name="find_related_accounts",
            status=ToolExecutionStatus.NOT_FOUND,
            target=clean_id,
            as_of=as_of,
            result=[],
            result_count=0,
            source="database.transactions",
            evidence_ids=[],
            error_details=f"Account '{clean_id}' not found in database.",
        )

    bounded_limit = min(max(1, limit), 50)
    as_of_dt = _parse_as_of(as_of)

    # Base query for account transactions up to as_of
    tx_query = db.query(Transaction).filter(Transaction.account_id == clean_id)
    if as_of_dt:
        tx_query = tx_query.filter(Transaction.timestamp <= as_of_dt)
    my_txs = tx_query.all()

    my_devs = {t.device_id for t in my_txs}
    my_ips = {t.ip_id for t in my_txs}
    my_bens = {t.beneficiary_id for t in my_txs if t.beneficiary_id}

    related: Dict[str, RelatedAccountRecord] = {}

    # Query shared devices
    if my_devs:
        q = db.query(Transaction).filter(
            Transaction.device_id.in_(my_devs),
            Transaction.account_id != clean_id,
        )
        if as_of_dt:
            q = q.filter(Transaction.timestamp <= as_of_dt)
        for t in q.all():
            if t.account_id not in related:
                related[t.account_id] = RelatedAccountRecord(
                    related_account_id=t.account_id,
                    relationship_type="SHARED_DEVICE",
                    shared_entity_id=t.device_id,
                    shared_entity_type="device",
                    supporting_transaction_ids=[t.transaction_id],
                )
            elif t.transaction_id not in related[t.account_id].supporting_transaction_ids:
                related[t.account_id].supporting_transaction_ids.append(t.transaction_id)

    # Query shared IPs
    if my_ips:
        q = db.query(Transaction).filter(
            Transaction.ip_id.in_(my_ips),
            Transaction.account_id != clean_id,
        )
        if as_of_dt:
            q = q.filter(Transaction.timestamp <= as_of_dt)
        for t in q.all():
            if t.account_id not in related:
                related[t.account_id] = RelatedAccountRecord(
                    related_account_id=t.account_id,
                    relationship_type="SHARED_IP",
                    shared_entity_id=t.ip_id,
                    shared_entity_type="ip",
                    supporting_transaction_ids=[t.transaction_id],
                )
            elif t.transaction_id not in related[t.account_id].supporting_transaction_ids:
                related[t.account_id].supporting_transaction_ids.append(t.transaction_id)

    # Query common beneficiaries
    if my_bens:
        q = db.query(Transaction).filter(
            Transaction.beneficiary_id.in_(my_bens),
            Transaction.account_id != clean_id,
        )
        if as_of_dt:
            q = q.filter(Transaction.timestamp <= as_of_dt)
        for t in q.all():
            if t.account_id not in related:
                related[t.account_id] = RelatedAccountRecord(
                    related_account_id=t.account_id,
                    relationship_type="COMMON_BENEFICIARY",
                    shared_entity_id=t.beneficiary_id,
                    shared_entity_type="beneficiary",
                    supporting_transaction_ids=[t.transaction_id],
                )
            elif t.transaction_id not in related[t.account_id].supporting_transaction_ids:
                related[t.account_id].supporting_transaction_ids.append(t.transaction_id)

    sorted_related = sorted(related.values(), key=lambda r: r.related_account_id)[:bounded_limit]
    records = [r.model_dump() for r in sorted_related]

    # Resolve genuine Stage 9 evidence IDs only
    evidence_ids: List[str] = []
    try:
        ev_engine = EvidenceEngine(db)
        ev_resp = ev_engine.extract_evidence_for_account(clean_id)
        evidence_ids = [
            i.evidence_id for i in ev_resp.items
            if i.evidence_type in (EvidenceType.RELATED_ACCOUNT, EvidenceType.MULTI_HOP_CONNECTION)
        ]
    except Exception:
        evidence_ids = []

    status = (
        ToolExecutionStatus.EMPTY if len(records) == 0
        else (ToolExecutionStatus.LIMITED if len(records) == bounded_limit else ToolExecutionStatus.SUCCESS)
    )

    return ToolExecutionResult(
        tool_name="find_related_accounts",
        status=status,
        target=clean_id,
        as_of=as_of,
        result=records,
        result_count=len(records),
        source="database.transactions",
        evidence_ids=evidence_ids,
        limitations=f"Bounded to max {bounded_limit} related accounts.",
    )


# ==============================================================================
# TOOL 4: find_shared_devices
# ==============================================================================

def find_shared_devices(
    db: Session,
    account_id: str,
    as_of: Optional[str] = None,
) -> ToolExecutionResult:
    """Discover hardware devices co-used by the account and other accounts."""
    PermissionGuard.check_permission("INVESTIGATION_READ")
    clean_id = account_id.strip()

    acc = db.query(Account).filter(Account.account_id == clean_id).first()
    if not acc:
        return ToolExecutionResult(
            tool_name="find_shared_devices",
            status=ToolExecutionStatus.NOT_FOUND,
            target=clean_id,
            as_of=as_of,
            result=[],
            result_count=0,
            source="database.devices",
            evidence_ids=[],
            error_details=f"Account '{clean_id}' not found in database.",
        )

    as_of_dt = _parse_as_of(as_of)
    tx_query = db.query(Transaction).filter(Transaction.account_id == clean_id)
    if as_of_dt:
        tx_query = tx_query.filter(Transaction.timestamp <= as_of_dt)
    my_devs = {t.device_id for t in tx_query.all()}

    shared_records: List[SharedDeviceRecord] = []
    if my_devs:
        for did in sorted(list(my_devs)):
            dev_obj = db.query(Device).filter(Device.device_id == did).first()
            if not dev_obj:
                continue

            q = db.query(Transaction).filter(
                Transaction.device_id == did,
                Transaction.account_id != clean_id,
            )
            if as_of_dt:
                q = q.filter(Transaction.timestamp <= as_of_dt)
            other_txs = q.all()
            if other_txs:
                co_accs = sorted(list({t.account_id for t in other_txs}))
                supp_txs = sorted(list({t.transaction_id for t in other_txs}))
                shared_records.append(
                    SharedDeviceRecord(
                        device_id=did,
                        device_type=dev_obj.device_type,
                        device_os=dev_obj.device_os,
                        co_using_accounts=co_accs,
                        supporting_transaction_ids=supp_txs,
                    )
                )

    # Resolve genuine Stage 9 evidence IDs only
    evidence_ids: List[str] = []
    try:
        ev_engine = EvidenceEngine(db)
        ev_resp = ev_engine.extract_evidence_for_account(clean_id)
        evidence_ids = [
            i.evidence_id for i in ev_resp.items
            if i.evidence_type == EvidenceType.SHARED_DEVICE
        ]
    except Exception:
        evidence_ids = []

    status = ToolExecutionStatus.SUCCESS if shared_records else ToolExecutionStatus.EMPTY

    return ToolExecutionResult(
        tool_name="find_shared_devices",
        status=status,
        target=clean_id,
        as_of=as_of,
        result=[r.model_dump() for r in shared_records],
        result_count=len(shared_records),
        source="database.devices",
        evidence_ids=evidence_ids,
        limitations="Filtered strictly to transactions occurring at t <= as_of.",
    )


# ==============================================================================
# TOOL 5: find_shared_ips
# ==============================================================================

def find_shared_ips(
    db: Session,
    account_id: str,
    as_of: Optional[str] = None,
) -> ToolExecutionResult:
    """Discover IP addresses co-used by the account and other accounts."""
    PermissionGuard.check_permission("INVESTIGATION_READ")
    clean_id = account_id.strip()

    acc = db.query(Account).filter(Account.account_id == clean_id).first()
    if not acc:
        return ToolExecutionResult(
            tool_name="find_shared_ips",
            status=ToolExecutionStatus.NOT_FOUND,
            target=clean_id,
            as_of=as_of,
            result=[],
            result_count=0,
            source="database.ips",
            evidence_ids=[],
            error_details=f"Account '{clean_id}' not found in database.",
        )

    as_of_dt = _parse_as_of(as_of)
    tx_query = db.query(Transaction).filter(Transaction.account_id == clean_id)
    if as_of_dt:
        tx_query = tx_query.filter(Transaction.timestamp <= as_of_dt)
    my_ips = {t.ip_id for t in tx_query.all()}

    shared_records: List[SharedIPRecord] = []
    if my_ips:
        for ipid in sorted(list(my_ips)):
            ip_obj = db.query(IPAddress).filter(IPAddress.ip_id == ipid).first()
            if not ip_obj:
                continue

            q = db.query(Transaction).filter(
                Transaction.ip_id == ipid,
                Transaction.account_id != clean_id,
            )
            if as_of_dt:
                q = q.filter(Transaction.timestamp <= as_of_dt)
            other_txs = q.all()
            if other_txs:
                co_accs = sorted(list({t.account_id for t in other_txs}))
                supp_txs = sorted(list({t.transaction_id for t in other_txs}))
                shared_records.append(
                    SharedIPRecord(
                        ip_id=ipid,
                        ip_address=ip_obj.ip_address,
                        ip_type=ip_obj.ip_type,
                        asn_org=ip_obj.asn_org,
                        country=ip_obj.country,
                        co_using_accounts=co_accs,
                        supporting_transaction_ids=supp_txs,
                    )
                )

    # Resolve genuine Stage 9 evidence IDs only
    evidence_ids: List[str] = []
    try:
        ev_engine = EvidenceEngine(db)
        ev_resp = ev_engine.extract_evidence_for_account(clean_id)
        evidence_ids = [
            i.evidence_id for i in ev_resp.items
            if i.evidence_type == EvidenceType.SHARED_IP
        ]
    except Exception:
        evidence_ids = []

    status = ToolExecutionStatus.SUCCESS if shared_records else ToolExecutionStatus.EMPTY

    return ToolExecutionResult(
        tool_name="find_shared_ips",
        status=status,
        target=clean_id,
        as_of=as_of,
        result=[r.model_dump() for r in shared_records],
        result_count=len(shared_records),
        source="database.ips",
        evidence_ids=evidence_ids,
        limitations="Filtered strictly to transactions occurring at t <= as_of.",
    )


# ==============================================================================
# TOOL 6: find_common_beneficiaries
# ==============================================================================

def find_common_beneficiaries(
    db: Session,
    account_id: str,
    as_of: Optional[str] = None,
) -> ToolExecutionResult:
    """Discover beneficiaries receiving funds from the investigated account and other accounts."""
    PermissionGuard.check_permission("INVESTIGATION_READ")
    clean_id = account_id.strip()

    acc = db.query(Account).filter(Account.account_id == clean_id).first()
    if not acc:
        return ToolExecutionResult(
            tool_name="find_common_beneficiaries",
            status=ToolExecutionStatus.NOT_FOUND,
            target=clean_id,
            as_of=as_of,
            result=[],
            result_count=0,
            source="database.beneficiaries",
            evidence_ids=[],
            error_details=f"Account '{clean_id}' not found in database.",
        )

    as_of_dt = _parse_as_of(as_of)
    tx_query = db.query(Transaction).filter(
        Transaction.account_id == clean_id,
        Transaction.beneficiary_id.isnot(None),
    )
    if as_of_dt:
        tx_query = tx_query.filter(Transaction.timestamp <= as_of_dt)
    my_bens = {t.beneficiary_id for t in tx_query.all() if t.beneficiary_id}

    shared_records: List[CommonBeneficiaryRecord] = []
    if my_bens:
        for bid in sorted(list(my_bens)):
            ben_obj = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == bid).first()
            if not ben_obj:
                continue

            q = db.query(Transaction).filter(
                Transaction.beneficiary_id == bid,
                Transaction.account_id != clean_id,
            )
            if as_of_dt:
                q = q.filter(Transaction.timestamp <= as_of_dt)
            other_txs = q.all()
            if other_txs:
                co_accs = sorted(list({t.account_id for t in other_txs}))
                supp_txs = sorted(list({t.transaction_id for t in other_txs}))
                shared_records.append(
                    CommonBeneficiaryRecord(
                        beneficiary_id=bid,
                        beneficiary_type=ben_obj.beneficiary_type,
                        bank_ifsc_prefix=ben_obj.bank_ifsc_prefix,
                        co_sending_accounts=co_accs,
                        supporting_transaction_ids=supp_txs,
                    )
                )

    # Resolve genuine Stage 9 evidence IDs only
    evidence_ids: List[str] = []
    try:
        ev_engine = EvidenceEngine(db)
        ev_resp = ev_engine.extract_evidence_for_account(clean_id)
        evidence_ids = [
            i.evidence_id for i in ev_resp.items
            if i.evidence_type == EvidenceType.COMMON_BENEFICIARY
        ]
    except Exception:
        evidence_ids = []

    status = ToolExecutionStatus.SUCCESS if shared_records else ToolExecutionStatus.EMPTY

    return ToolExecutionResult(
        tool_name="find_common_beneficiaries",
        status=status,
        target=clean_id,
        as_of=as_of,
        result=[r.model_dump() for r in shared_records],
        result_count=len(shared_records),
        source="database.beneficiaries",
        evidence_ids=evidence_ids,
        limitations="Filtered strictly to transactions occurring at t <= as_of.",
    )


# ==============================================================================
# TOOL 7: trace_fund_flow
# ==============================================================================

def trace_fund_flow(
    db: Session,
    target_id: str,
    as_of: Optional[str] = None,
    max_depth: int = 2,
    max_results: int = 50,
) -> ToolExecutionResult:
    """Trace verified financial fund flows grounded in actual Transaction records.
    
    CRITICAL GUARDRAIL: Only describes an actual transfer when an underlying Transaction record supports it.
    Does NOT convert graph co-membership or shared attributes into unsupported fund movement claims.
    """
    PermissionGuard.check_permission("INVESTIGATION_READ")
    clean_id = target_id.strip()
    bounded_depth = min(max(1, max_depth), 3)
    bounded_results = min(max(1, max_results), 100)
    as_of_dt = _parse_as_of(as_of)

    # Resolve whether target is a transaction or an account
    initial_tx: Optional[Transaction] = None
    account_id: Optional[str] = None

    if clean_id.startswith("TXN_"):
        initial_tx = db.query(Transaction).filter(Transaction.transaction_id == clean_id).first()
        if not initial_tx:
            return ToolExecutionResult(
                tool_name="trace_fund_flow",
                status=ToolExecutionStatus.NOT_FOUND,
                target=clean_id,
                as_of=as_of,
                result=[],
                result_count=0,
                source="database.transactions",
                evidence_ids=[],
                error_details=f"Transaction '{clean_id}' not found in database.",
            )
        account_id = initial_tx.account_id
        if not as_of_dt:
            as_of_dt = initial_tx.timestamp
    else:
        acc = db.query(Account).filter(Account.account_id == clean_id).first()
        if not acc:
            return ToolExecutionResult(
                tool_name="trace_fund_flow",
                status=ToolExecutionStatus.NOT_FOUND,
                target=clean_id,
                as_of=as_of,
                result=[],
                result_count=0,
                source="database.transactions",
                evidence_ids=[],
                error_details=f"Account '{clean_id}' not found in database.",
            )
        account_id = clean_id

    hops: List[FundFlowHop] = []
    seen_tx_ids: Set[str] = set()

    # Hop 1: Direct outbound transactions from the account
    q1 = db.query(Transaction).filter(Transaction.account_id == account_id)
    if as_of_dt:
        q1 = q1.filter(Transaction.timestamp <= as_of_dt)
    hop1_txs = q1.order_by(Transaction.timestamp.asc()).limit(bounded_results).all()

    for t in hop1_txs:
        seen_tx_ids.add(t.transaction_id)
        hops.append(
            FundFlowHop(
                hop_number=1,
                transaction_id=t.transaction_id,
                timestamp=t.timestamp.isoformat(),
                amount=float(t.amount),
                source_account_id=t.account_id,
                beneficiary_id=t.beneficiary_id,
                merchant_id=t.merchant_id,
                channel=t.channel,
                status=t.status,
            )
        )

    # Hop 2 (if max_depth >= 2): Check if beneficiaries received funds from downstream transactions
    if bounded_depth >= 2 and len(hops) < bounded_results:
        touched_bens = {h.beneficiary_id for h in hops if h.beneficiary_id}
        if touched_bens:
            q2 = db.query(Transaction).filter(
                Transaction.beneficiary_id.in_(touched_bens),
                Transaction.account_id != account_id,
            )
            if as_of_dt:
                q2 = q2.filter(Transaction.timestamp <= as_of_dt)
            hop2_txs = q2.order_by(Transaction.timestamp.asc()).limit(bounded_results - len(hops)).all()
            for t in hop2_txs:
                if t.transaction_id not in seen_tx_ids:
                    seen_tx_ids.add(t.transaction_id)
                    hops.append(
                        FundFlowHop(
                            hop_number=2,
                            transaction_id=t.transaction_id,
                            timestamp=t.timestamp.isoformat(),
                            amount=float(t.amount),
                            source_account_id=t.account_id,
                            beneficiary_id=t.beneficiary_id,
                            merchant_id=t.merchant_id,
                            channel=t.channel,
                            status=t.status,
                        )
                    )

    # Resolve genuine Stage 9 evidence IDs ONLY if they exist in Stage 9
    evidence_ids: List[str] = []
    try:
        ev_engine = EvidenceEngine(db)
        if clean_id.startswith("TXN_"):
            ev_resp = ev_engine.extract_evidence_for_transaction(clean_id)
        else:
            ev_resp = ev_engine.extract_evidence_for_account(clean_id)
        evidence_ids = [
            i.evidence_id for i in ev_resp.items
            if i.evidence_type in (EvidenceType.RAPID_FUND_FLOW, EvidenceType.LARGE_INCOMING_TRANSACTION, EvidenceType.COMMON_BENEFICIARY)
        ]
    except Exception:
        evidence_ids = []

    status = (
        ToolExecutionStatus.EMPTY if len(hops) == 0
        else (ToolExecutionStatus.LIMITED if len(hops) >= bounded_results else ToolExecutionStatus.SUCCESS)
    )

    return ToolExecutionResult(
        tool_name="trace_fund_flow",
        status=status,
        target=clean_id,
        as_of=as_of_dt.isoformat() if as_of_dt else as_of,
        result=[h.model_dump() for h in hops],
        result_count=len(hops),
        source="database.transactions",
        evidence_ids=evidence_ids,
        limitations=f"Bounded to max_depth={bounded_depth} and max_results={bounded_results}. Real transactions only.",
    )


# ==============================================================================
# TOOL 8: reconstruct_timeline
# ==============================================================================

def reconstruct_timeline(
    db: Session,
    target_id: str,
    as_of: Optional[str] = None,
) -> ToolExecutionResult:
    """Reconstruct chronological timeline events by delegating to Stage 9 TimelineEngine."""
    PermissionGuard.check_permission("INVESTIGATION_READ")
    clean_id = target_id.strip()

    timeline_engine = TimelineEngine(db)
    try:
        if clean_id.startswith("TXN_"):
            timeline_resp = timeline_engine.reconstruct_timeline_for_transaction(clean_id)
        else:
            timeline_resp = timeline_engine.reconstruct_timeline_for_account(clean_id)
    except KeyError as e:
        return ToolExecutionResult(
            tool_name="reconstruct_timeline",
            status=ToolExecutionStatus.NOT_FOUND,
            target=clean_id,
            as_of=as_of,
            result=None,
            result_count=0,
            source="stage9.timeline_engine",
            evidence_ids=[],
            error_details=str(e),
        )

    # Filter events if an explicit earlier as_of was requested
    events = timeline_resp.events
    as_of_dt = _parse_as_of(as_of)
    if as_of_dt:
        events = [e for e in events if datetime.fromisoformat(e.timestamp) <= as_of_dt]

    # Resolve genuine Stage 9 evidence IDs
    evidence_ids: List[str] = []
    try:
        ev_engine = EvidenceEngine(db)
        if clean_id.startswith("TXN_"):
            ev_resp = ev_engine.extract_evidence_for_transaction(clean_id)
        else:
            ev_resp = ev_engine.extract_evidence_for_account(clean_id)
        evidence_ids = [i.evidence_id for i in ev_resp.items]
    except Exception:
        evidence_ids = []

    payload = {
        "target_id": timeline_resp.target_id,
        "target_type": timeline_resp.target_type,
        "total_events": len(events),
        "events": [e.model_dump() for e in events],
        "risk_context": timeline_resp.risk_context,
    }

    return ToolExecutionResult(
        tool_name="reconstruct_timeline",
        status=ToolExecutionStatus.SUCCESS if events else ToolExecutionStatus.EMPTY,
        target=clean_id,
        as_of=as_of or timeline_resp.timestamp_context,
        result=payload,
        result_count=len(events),
        source="stage9.timeline_engine",
        evidence_ids=evidence_ids,
        limitations="Chronological historical records only. RISK_EVALUATION strictly excluded from event list.",
    )


# ==============================================================================
# TOOL 9: get_risk_features
# ==============================================================================

def get_risk_features(
    db: Session,
    transaction_id: str,
    model_type: str = "graph",
) -> ToolExecutionResult:
    """Retrieve verified Stage 8 feature values and model-derived risk evaluation."""
    PermissionGuard.check_permission("INVESTIGATION_READ")
    clean_id = transaction_id.strip()

    tx = db.query(Transaction).filter(Transaction.transaction_id == clean_id).first()
    if not tx:
        return ToolExecutionResult(
            tool_name="get_risk_features",
            status=ToolExecutionStatus.NOT_FOUND,
            target=clean_id,
            as_of=None,
            result=None,
            result_count=0,
            source="stage8.feature_service",
            evidence_ids=[],
            error_details=f"Transaction '{clean_id}' not found in database.",
        )

    model_service = get_model_service()
    feature_service = get_feature_service()

    target_model_type = "baseline" if model_type.lower() == "baseline" else "graph"

    try:
        feats_df, _ = feature_service.get_features(db, clean_id, model_type=target_model_type)
        if target_model_type == "baseline":
            prob = model_service.predict_baseline(feats_df)
            m_name = "ringguard_baseline_xgb_v1"
            f_count = 37
            g_count = 0
        else:
            prob = model_service.predict_graph(feats_df)
            m_name = "ringguard_graph_xgb_v1"
            f_count = 58
            g_count = 21

        risk_band = "HIGH" if prob >= 0.50 else ("MEDIUM" if prob >= 0.20 else "LOW")
        feature_dict = {col: float(feats_df[col].iloc[0]) for col in feats_df.columns}

        payload = RiskFeaturesResult(
            transaction_id=clean_id,
            model_name=m_name,
            model_version="v1",
            feature_count=f_count,
            graph_feature_count=g_count,
            features=feature_dict,
            predicted_ring_probability=round(prob, 6),
            decision_threshold=0.50,
            risk_band=risk_band,
        )

        # Resolve Stage 9 MODEL_RISK_CONTEXT evidence ID
        evidence_ids: List[str] = []
        try:
            ev_engine = EvidenceEngine(db)
            ev_resp = ev_engine.extract_evidence_for_transaction(clean_id)
            evidence_ids = [
                i.evidence_id for i in ev_resp.items
                if i.evidence_type == EvidenceType.MODEL_RISK_CONTEXT
            ]
        except Exception:
            evidence_ids = []

        return ToolExecutionResult(
            tool_name="get_risk_features",
            status=ToolExecutionStatus.SUCCESS,
            target=clean_id,
            as_of=tx.timestamp.isoformat(),
            result=payload.model_dump(),
            result_count=f_count,
            source="stage8.model_service",
            evidence_ids=evidence_ids,
            limitations=f"Delegates to Stage 8 {m_name}. Strictly read-only feature extraction.",
        )
    except Exception as e:
        return ToolExecutionResult(
            tool_name="get_risk_features",
            status=ToolExecutionStatus.UNAVAILABLE,
            target=clean_id,
            as_of=tx.timestamp.isoformat(),
            result=None,
            result_count=0,
            source="stage8.model_service",
            evidence_ids=[],
            error_details=f"Feature extraction failed: {str(e)}",
        )
