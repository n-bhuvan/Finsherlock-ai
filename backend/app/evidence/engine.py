"""RingGuard AI — Deterministic Evidence Engine.

Stage 9: Evidence + Timeline Engine.
Transforms verified PostgreSQL records and NetworkX graph topology into
structured, verifiable, point-in-time safe evidence objects.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.account import Account
from app.models.device import Device
from app.models.ip import IPAddress
from app.models.beneficiary import Beneficiary
from app.evidence.schemas import (
    EvidenceType,
    EvidenceSeverity,
    EvidenceItem,
    EvidenceListResponse,
)
from app.services.model_service import get_model_service
from app.services.feature_service import get_feature_service


# Deterministic priority scoring for MVP evidence ranking
EVIDENCE_TYPE_BASE_PRIORITY = {
    EvidenceType.RAPID_FUND_FLOW: 100,
    EvidenceType.MULTI_HOP_CONNECTION: 90,
    EvidenceType.SHARED_DEVICE: 80,
    EvidenceType.COMMON_BENEFICIARY: 75,
    EvidenceType.SHARED_IP: 70,
    EvidenceType.RELATED_ACCOUNT: 65,
    EvidenceType.LARGE_INCOMING_TRANSACTION: 60,
    EvidenceType.MODEL_RISK_CONTEXT: 50,
    EvidenceType.ACCOUNT_AGE_CONTEXT: 40,
    EvidenceType.COORDINATED_TIMING: 35,
    EvidenceType.TRANSACTION_ACTIVITY: 30,
    EvidenceType.NETWORK_CONTEXT: 20,
}


class EvidenceEngine:
    """Extracts factual, data-grounded evidence objects strictly up to timestamp T."""

    def __init__(self, db: Session):
        self.db = db
        self.model_service = get_model_service()
        self.feature_service = get_feature_service()

    def extract_evidence_for_transaction(self, transaction_id: str) -> EvidenceListResponse:
        """Extract all observed evidence for a specific transaction at point-in-time T."""
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
        device_id = tx.device_id
        ip_id = tx.ip_id
        beneficiary_id = tx.beneficiary_id
        amount = float(tx.amount)

        raw_items: List[EvidenceItem] = []

        # 1. SHARED DEVICE
        other_dev_txs = (
            self.db.query(Transaction)
            .filter(
                Transaction.device_id == device_id,
                Transaction.account_id != account_id,
                Transaction.timestamp <= T,
            )
            .order_by(Transaction.timestamp.asc())
            .all()
        )
        if other_dev_txs:
            shared_accounts = sorted(list({t.account_id for t in other_dev_txs}))
            supporting_tx_ids = sorted(list({tx.transaction_id} | {t.transaction_id for t in other_dev_txs}))
            all_timestamps = [t.timestamp.isoformat() for t in other_dev_txs] + [t_iso]
            severity = EvidenceSeverity.HIGH if len(shared_accounts) >= 2 else EvidenceSeverity.MEDIUM

            raw_items.append(
                EvidenceItem(
                    evidence_id=f"EVD_DEV_{transaction_id}_{device_id}",
                    evidence_type=EvidenceType.SHARED_DEVICE,
                    severity=severity,
                    title="Shared Device Detected",
                    description=(
                        f"Device '{device_id}' was used by {len(shared_accounts) + 1} distinct accounts "
                        f"({account_id} and {', '.join(shared_accounts)}) across {len(supporting_tx_ids)} "
                        f"transactions up to point-in-time {t_iso}."
                    ),
                    related_entities=[account_id, device_id] + shared_accounts,
                    supporting_transaction_ids=supporting_tx_ids,
                    timestamp_range={"start": min(all_timestamps), "end": max(all_timestamps)},
                    timestamp_source="transactions.timestamp",
                    source="database.transactions",
                    status="VERIFIED",
                    relevant_values={
                        "device_id": device_id,
                        "shared_account_count": len(shared_accounts) + 1,
                        "connected_accounts": shared_accounts,
                        "supporting_transaction_count": len(supporting_tx_ids),
                    },
                    rank=0,
                )
            )

        # 2. SHARED IP
        other_ip_txs = (
            self.db.query(Transaction)
            .filter(
                Transaction.ip_id == ip_id,
                Transaction.account_id != account_id,
                Transaction.timestamp <= T,
            )
            .order_by(Transaction.timestamp.asc())
            .all()
        )
        if other_ip_txs:
            shared_ip_accounts = sorted(list({t.account_id for t in other_ip_txs}))
            supporting_ip_txs = sorted(list({tx.transaction_id} | {t.transaction_id for t in other_ip_txs}))
            all_ip_timestamps = [t.timestamp.isoformat() for t in other_ip_txs] + [t_iso]
            severity = EvidenceSeverity.MEDIUM if len(shared_ip_accounts) >= 2 else EvidenceSeverity.LOW

            raw_items.append(
                EvidenceItem(
                    evidence_id=f"EVD_IP_{transaction_id}_{ip_id}",
                    evidence_type=EvidenceType.SHARED_IP,
                    severity=severity,
                    title="Shared IP Address Observed",
                    description=(
                        f"IP infrastructure '{ip_id}' was shared between account '{account_id}' "
                        f"and {len(shared_ip_accounts)} other account(s) ({', '.join(shared_ip_accounts)}) "
                        f"across {len(supporting_ip_txs)} transactions up to {t_iso}."
                    ),
                    related_entities=[account_id, ip_id] + shared_ip_accounts,
                    supporting_transaction_ids=supporting_ip_txs,
                    timestamp_range={"start": min(all_ip_timestamps), "end": max(all_ip_timestamps)},
                    timestamp_source="transactions.timestamp",
                    source="database.transactions",
                    status="VERIFIED",
                    relevant_values={
                        "ip_id": ip_id,
                        "shared_account_count": len(shared_ip_accounts) + 1,
                        "connected_accounts": shared_ip_accounts,
                        "supporting_transaction_count": len(supporting_ip_txs),
                    },
                    rank=0,
                )
            )

        # 3. COMMON BENEFICIARY
        if beneficiary_id:
            other_ben_txs = (
                self.db.query(Transaction)
                .filter(
                    Transaction.beneficiary_id == beneficiary_id,
                    Transaction.account_id != account_id,
                    Transaction.timestamp <= T,
                )
                .order_by(Transaction.timestamp.asc())
                .all()
            )
            if other_ben_txs:
                shared_ben_accounts = sorted(list({t.account_id for t in other_ben_txs}))
                supporting_ben_txs = sorted(list({tx.transaction_id} | {t.transaction_id for t in other_ben_txs}))
                all_ben_timestamps = [t.timestamp.isoformat() for t in other_ben_txs] + [t_iso]
                severity = EvidenceSeverity.HIGH if len(shared_ben_accounts) >= 2 else EvidenceSeverity.MEDIUM

                raw_items.append(
                    EvidenceItem(
                        evidence_id=f"EVD_BEN_{transaction_id}_{beneficiary_id}",
                        evidence_type=EvidenceType.COMMON_BENEFICIARY,
                        severity=severity,
                        title="Common Beneficiary Routing",
                        description=(
                            f"Beneficiary '{beneficiary_id}' received transfers from account '{account_id}' "
                            f"and {len(shared_ben_accounts)} other account(s) ({', '.join(shared_ben_accounts)}) "
                            f"prior to or at {t_iso}."
                        ),
                        related_entities=[account_id, beneficiary_id] + shared_ben_accounts,
                        supporting_transaction_ids=supporting_ben_txs,
                        timestamp_range={"start": min(all_ben_timestamps), "end": max(all_ben_timestamps)},
                        timestamp_source="transactions.timestamp",
                        source="database.transactions",
                        status="VERIFIED",
                        relevant_values={
                            "beneficiary_id": beneficiary_id,
                            "contributing_accounts_count": len(shared_ben_accounts) + 1,
                            "contributing_accounts": shared_ben_accounts,
                            "supporting_transaction_count": len(supporting_ben_txs),
                        },
                        rank=0,
                    )
                )

        # 4. RELATED ACCOUNT (Aggregate Cluster of Directly Linked Accounts)
        direct_connected_accounts = set()
        if other_dev_txs:
            direct_connected_accounts.update({t.account_id for t in other_dev_txs})
        if other_ip_txs:
            direct_connected_accounts.update({t.account_id for t in other_ip_txs})
        if beneficiary_id and 'other_ben_txs' in locals() and other_ben_txs:
            direct_connected_accounts.update({t.account_id for t in other_ben_txs})

        if direct_connected_accounts:
            sorted_conn = sorted(list(direct_connected_accounts))
            raw_items.append(
                EvidenceItem(
                    evidence_id=f"EVD_REL_{transaction_id}_{account_id}",
                    evidence_type=EvidenceType.RELATED_ACCOUNT,
                    severity=EvidenceSeverity.HIGH if len(sorted_conn) >= 3 else EvidenceSeverity.MEDIUM,
                    title="Directly Linked Account Cluster",
                    description=(
                        f"Account '{account_id}' is directly linked to {len(sorted_conn)} other account(s) "
                        f"({', '.join(sorted_conn)}) via shared devices, IP addresses, or common beneficiaries "
                        f"up to point-in-time {t_iso}."
                    ),
                    related_entities=[account_id] + sorted_conn,
                    supporting_transaction_ids=[tx.transaction_id],
                    timestamp_range={"start": t_iso, "end": t_iso},
                    timestamp_source="transactions.timestamp",
                    source="database.transactions",
                    status="VERIFIED",
                    relevant_values={
                        "connected_accounts_count": len(sorted_conn),
                        "connected_accounts": sorted_conn,
                    },
                    rank=0,
                )
            )

        # 5. MULTI-HOP CONNECTION (Indirect 2-Hop Network Connectivity)
        multi_hop_accounts: Set[str] = set()
        if direct_connected_accounts:
            # Query secondary devices used by direct connected accounts up to T
            secondary_txs = (
                self.db.query(Transaction)
                .filter(
                    Transaction.account_id.in_(direct_connected_accounts),
                    Transaction.timestamp <= T,
                )
                .all()
            )
            sec_devs = {t.device_id for t in secondary_txs if t.device_id != device_id}
            if sec_devs:
                tertiary_txs = (
                    self.db.query(Transaction)
                    .filter(
                        Transaction.device_id.in_(sec_devs),
                        Transaction.account_id != account_id,
                        ~Transaction.account_id.in_(direct_connected_accounts),
                        Transaction.timestamp <= T,
                    )
                    .all()
                )
                multi_hop_accounts.update({t.account_id for t in tertiary_txs})

        if multi_hop_accounts:
            sorted_mhop = sorted(list(multi_hop_accounts))
            raw_items.append(
                EvidenceItem(
                    evidence_id=f"EVD_MULTIHOP_{transaction_id}_{account_id}",
                    evidence_type=EvidenceType.MULTI_HOP_CONNECTION,
                    severity=EvidenceSeverity.HIGH,
                    title="Indirect Multi-Hop Syndicate Connection",
                    description=(
                        f"Account '{account_id}' connects indirectly (2 hops) to {len(sorted_mhop)} additional "
                        f"account(s) ({', '.join(sorted_mhop)}) through secondary shared devices or infrastructure up to {t_iso}."
                    ),
                    related_entities=[account_id] + sorted_mhop,
                    supporting_transaction_ids=[tx.transaction_id],
                    timestamp_range={"start": t_iso, "end": t_iso},
                    timestamp_source="transactions.timestamp",
                    source="networkx.graph",
                    status="VERIFIED",
                    relevant_values={
                        "hop_distance": 2,
                        "multi_hop_accounts_count": len(sorted_mhop),
                        "multi_hop_accounts": sorted_mhop,
                    },
                    rank=0,
                )
            )

        # 6. RAPID FUND FLOW / BURST VELOCITY
        # Check transaction count and volume for account_id within 1h and 24h prior to T
        t_1h = T - timedelta(hours=1)
        t_24h = T - timedelta(hours=24)
        txs_24h = (
            self.db.query(Transaction)
            .filter(
                Transaction.account_id == account_id,
                Transaction.timestamp >= t_24h,
                Transaction.timestamp <= T,
            )
            .order_by(Transaction.timestamp.asc())
            .all()
        )
        txs_1h = [t for t in txs_24h if t.timestamp >= t_1h]

        if len(txs_1h) >= 2 or len(txs_24h) >= 4:
            supporting_rapid_ids = [t.transaction_id for t in txs_24h]
            sum_24h = sum(float(t.amount) for t in txs_24h)
            raw_items.append(
                EvidenceItem(
                    evidence_id=f"EVD_RAPID_{transaction_id}_{account_id}",
                    evidence_type=EvidenceType.RAPID_FUND_FLOW,
                    severity=EvidenceSeverity.HIGH if len(txs_1h) >= 3 else EvidenceSeverity.MEDIUM,
                    title="Rapid Transaction Burst Velocity",
                    description=(
                        f"Account '{account_id}' performed {len(txs_1h)} transactions within 1 hour "
                        f"and {len(txs_24h)} transactions (totaling INR {sum_24h:,.2f}) within 24 hours up to {t_iso}."
                    ),
                    related_entities=[account_id],
                    supporting_transaction_ids=supporting_rapid_ids,
                    timestamp_range={"start": txs_24h[0].timestamp.isoformat(), "end": t_iso},
                    timestamp_source="transactions.timestamp",
                    source="database.transactions",
                    status="VERIFIED",
                    relevant_values={
                        "tx_count_1h": len(txs_1h),
                        "tx_count_24h": len(txs_24h),
                        "total_volume_24h": sum_24h,
                    },
                    rank=0,
                )
            )

        # 7. LARGE INCOMING / OUTGOING TRANSACTION
        # Compare current transaction to account's historical average up to T (excluding current)
        prior_txs = (
            self.db.query(Transaction)
            .filter(
                Transaction.account_id == account_id,
                Transaction.timestamp < T,
            )
            .all()
        )
        if prior_txs:
            prior_avg = sum(float(t.amount) for t in prior_txs) / len(prior_txs)
            if amount >= 15000.0 or (prior_avg > 0 and amount >= 3.0 * prior_avg):
                raw_items.append(
                    EvidenceItem(
                        evidence_id=f"EVD_AMT_{transaction_id}",
                        evidence_type=EvidenceType.LARGE_INCOMING_TRANSACTION,
                        severity=EvidenceSeverity.MEDIUM if amount < 25000 else EvidenceSeverity.HIGH,
                        title="High-Value Transaction Spike",
                        description=(
                            f"Transaction amount INR {amount:,.2f} is unusually high compared to the account's "
                            f"historical average of INR {prior_avg:,.2f} ({amount/prior_avg:.1f}x multiplier) prior to {t_iso}."
                        ),
                        related_entities=[account_id, transaction_id],
                        supporting_transaction_ids=[transaction_id],
                        timestamp_range={"start": t_iso, "end": t_iso},
                        timestamp_source="transactions.timestamp",
                        source="database.transactions",
                        status="VERIFIED",
                        relevant_values={
                            "amount": amount,
                            "historical_average": prior_avg,
                            "ratio_to_average": amount / prior_avg if prior_avg > 0 else 0,
                        },
                        rank=0,
                    )
                )
        elif amount >= 10000.0:
            # First transaction is already large
            raw_items.append(
                EvidenceItem(
                    evidence_id=f"EVD_AMT_{transaction_id}",
                    evidence_type=EvidenceType.LARGE_INCOMING_TRANSACTION,
                    severity=EvidenceSeverity.MEDIUM,
                    title="High-Value Initial Transaction",
                    description=(
                        f"Initial transaction on account '{account_id}' exhibits high value of INR {amount:,.2f} "
                        f"with zero prior transaction history."
                    ),
                    related_entities=[account_id, transaction_id],
                    supporting_transaction_ids=[transaction_id],
                    timestamp_range={"start": t_iso, "end": t_iso},
                    timestamp_source="transactions.timestamp",
                    source="database.transactions",
                    status="VERIFIED",
                    relevant_values={"amount": amount, "prior_transactions_count": 0},
                    rank=0,
                )
            )

        # 8. ACCOUNT AGE CONTEXT
        acc: Optional[Account] = (
            self.db.query(Account)
            .filter(Account.account_id == account_id)
            .first()
        )
        if acc:
            acc_created = acc.account_created_at
            age_days = (T - acc_created).total_seconds() / 86400.0
            if age_days < 14.0:
                raw_items.append(
                    EvidenceItem(
                        evidence_id=f"EVD_AGE_{transaction_id}_{account_id}",
                        evidence_type=EvidenceType.ACCOUNT_AGE_CONTEXT,
                        severity=EvidenceSeverity.MEDIUM if age_days < 3.0 else EvidenceSeverity.LOW,
                        title="New Account Activity",
                        description=(
                            f"Account '{account_id}' was created at {acc_created.isoformat()}, "
                            f"making it only {age_days:.1f} days old at the time of transaction {transaction_id}."
                        ),
                        related_entities=[account_id],
                        supporting_transaction_ids=[transaction_id],
                        timestamp_range={"start": acc_created.isoformat(), "end": t_iso},
                        timestamp_source="accounts.account_created_at",
                        source="database.accounts",
                        status="VERIFIED",
                        relevant_values={
                            "account_created_at": acc_created.isoformat(),
                            "account_age_days": round(age_days, 2),
                        },
                        rank=0,
                    )
                )

        # 9. MODEL RISK CONTEXT (Derived Machine Learning Assessment)
        try:
            feats_b, _ = self.feature_service.get_features(self.db, transaction_id, model_type="graph")
            prob_b = self.model_service.predict_graph(feats_b)
            risk_band = (
                "HIGH" if prob_b >= 0.50 else ("MEDIUM" if prob_b >= 0.20 else "LOW")
            )
            raw_items.append(
                EvidenceItem(
                    evidence_id=f"EVD_MODEL_{transaction_id}",
                    evidence_type=EvidenceType.MODEL_RISK_CONTEXT,
                    severity=EvidenceSeverity.HIGH if risk_band == "HIGH" else (
                        EvidenceSeverity.MEDIUM if risk_band == "MEDIUM" else EvidenceSeverity.INFO
                    ),
                    title="Model Risk Assessment Context",
                    description=(
                        f"Derived Stage 7 Graph-Enhanced Model evaluation: estimated ring probability = {prob_b:.4f} "
                        f"(Risk Band: {risk_band}, Decision Threshold: 0.50). "
                        "Contextual model assessment only, not direct proof of fraud."
                    ),
                    related_entities=[transaction_id, account_id],
                    supporting_transaction_ids=[transaction_id],
                    timestamp_range={"start": t_iso, "end": t_iso},
                    timestamp_source="transactions.timestamp",
                    source="ml.graph_model",
                    status="VERIFIED",
                    relevant_values={
                        "model_name": "ringguard_graph_xgb_v1",
                        "predicted_ring_probability": round(prob_b, 6),
                        "risk_band": risk_band,
                        "decision_threshold": 0.50,
                    },
                    rank=0,
                )
            )
        except Exception:
            pass

        # 10. DETERMINISTIC EVIDENCE RANKING
        ranked_items = self._rank_evidence_items(raw_items)

        return EvidenceListResponse(
            target_id=transaction_id,
            target_type="transaction",
            timestamp_context=t_iso,
            total_evidence_items=len(ranked_items),
            items=ranked_items,
        )

    def extract_evidence_for_account(self, account_id: str) -> EvidenceListResponse:
        """Extract evidence for an account using its latest transaction as the point-in-time boundary."""
        acc: Optional[Account] = (
            self.db.query(Account)
            .filter(Account.account_id == account_id)
            .first()
        )
        if not acc:
            raise KeyError(f"Account '{account_id}' not found in database.")

        # Find latest transaction for this account to establish point-in-time context
        latest_tx: Optional[Transaction] = (
            self.db.query(Transaction)
            .filter(Transaction.account_id == account_id)
            .order_by(Transaction.timestamp.desc())
            .first()
        )

        if latest_tx:
            # Delegate to transaction evidence using latest transaction
            resp = self.extract_evidence_for_transaction(latest_tx.transaction_id)
            resp.target_id = account_id
            resp.target_type = "account"
            return resp

        # Account has 0 transactions: return clean account creation evidence
        created_at = acc.account_created_at.isoformat()
        clean_item = EvidenceItem(
            evidence_id=f"EVD_ACC_NEW_{account_id}",
            evidence_type=EvidenceType.ACCOUNT_AGE_CONTEXT,
            severity=EvidenceSeverity.INFO,
            title="Account Registered with Zero Transactions",
            description=f"Account '{account_id}' was registered at {created_at} with zero recorded transactions.",
            related_entities=[account_id],
            supporting_transaction_ids=[],
            timestamp_range={"start": created_at, "end": created_at},
            timestamp_source="accounts.account_created_at",
            source="database.accounts",
            status="VERIFIED",
            relevant_values={"account_created_at": created_at, "transaction_count": 0},
            rank=1,
        )
        return EvidenceListResponse(
            target_id=account_id,
            target_type="account",
            timestamp_context=created_at,
            total_evidence_items=1,
            items=[clean_item],
        )

    def _rank_evidence_items(self, items: List[EvidenceItem]) -> List[EvidenceItem]:
        """Sort evidence deterministically by priority score, supporting transactions count, then ID."""
        def sort_key(item: EvidenceItem):
            base_score = EVIDENCE_TYPE_BASE_PRIORITY.get(item.evidence_type, 10)
            tx_count = len(item.supporting_transaction_ids)
            # Sort descending by base score, descending by tx_count, ascending by ID
            return (-base_score, -tx_count, item.evidence_id)

        sorted_items = sorted(items, key=sort_key)
        for idx, item in enumerate(sorted_items, start=1):
            item.rank = idx
        return sorted_items
