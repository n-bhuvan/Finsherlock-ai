"""RingGuard AI — Systemic Risk Anomaly Detection Service.

V2 Stage 15: Systemic Risk Anomaly Detection.
Provides deterministic, multi-scope anomaly detection across:
1. Customer / Account-Level Anomaly (ACCOUNT)
2. Merchant-Level Anomaly (MERCHANT)
3. Ring / Network-Level Anomaly (RING_NETWORK)
4. Possible Systemic / Infrastructure-Level Anomaly (SYSTEMIC_INFRASTRUCTURE)

Strictly enforces:
- Non-causal evidence-based wording (no blaming of banks, ISPs, or PSPs)
- Availability status tracking for every empirical signal (no fabrication)
- Human-in-the-loop governance (human_approval_required = True)
- Defense-only non-enforcement boundaries
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.merchant import Merchant
from app.models.ip import IPAddress
from app.models.beneficiary import Beneficiary
from app.services.graph_service import GraphService
from app.evidence.engine import EvidenceEngine
from app.anomaly.schemas import (
    AnomalyScope,
    SignalStatus,
    AnomalySignal,
    ScopeAnomalyResult,
    SystemicAnomalyResponse,
)


class SystemicAnomalyService:
    """Deterministic multi-scope anomaly detection engine operating on verified data."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self._owns_session = db is None
        self.evidence_engine = EvidenceEngine(self.db)
        self.graph_service = GraphService.get_instance()

    def close(self):
        """Close database session if self-owned."""
        if self._owns_session:
            self.db.close()

    def analyze_transaction(self, transaction_id: str) -> SystemicAnomalyResponse:
        """Perform comprehensive, deterministic multi-scope anomaly analysis for a transaction."""
        clean_tx_id = transaction_id.strip().upper()
        tx: Optional[Transaction] = (
            self.db.query(Transaction)
            .filter(Transaction.transaction_id == clean_tx_id)
            .first()
        )
        if not tx:
            raise KeyError(f"Transaction '{transaction_id}' not found in database.")

        T: datetime = tx.timestamp
        
        # Extract verified Stage 9 point-in-time evidence items
        evidence_resp = self.evidence_engine.extract_evidence_for_transaction(clean_tx_id)
        evidence_items = evidence_resp.items

        # 1. Evaluate individual scopes
        account_scope = self._evaluate_account_scope(tx, T, evidence_items)
        merchant_scope = self._evaluate_merchant_scope(tx, T, evidence_items)
        ring_scope = self._evaluate_ring_network_scope(tx, T, evidence_items)
        infra_scope = self._evaluate_systemic_infrastructure_scope(tx, T, evidence_items)

        scopes: Dict[str, ScopeAnomalyResult] = {
            "account": account_scope,
            "merchant": merchant_scope,
            "ring_network": ring_scope,
            "systemic_infrastructure": infra_scope,
        }

        # 2. Determine composite systemic anomaly score (heuristic combination)
        active_scores = [
            s.anomaly_score
            for s in scopes.values()
            if s.status != "NOT_APPLICABLE"
        ]
        
        # Max-dominant blend: primarily driven by strongest active anomaly scope
        if active_scores:
            max_score = max(active_scores)
            avg_score = sum(active_scores) / len(active_scores)
            systemic_anomaly_score = round(0.75 * max_score + 0.25 * avg_score, 4)
        else:
            systemic_anomaly_score = 0.0

        anomaly_detected = any(s.anomaly_detected for s in scopes.values())

        # Determine primary contributing scope
        primary_scope: Optional[AnomalyScope] = None
        if anomaly_detected:
            candidates = [
                s for s in scopes.values()
                if s.anomaly_detected and s.status != "NOT_APPLICABLE"
            ]
            if candidates:
                candidates.sort(key=lambda s: s.anomaly_score, reverse=True)
                primary_scope = candidates[0].scope

        # Collect de-duplicated evidence IDs across scopes
        all_ev_ids: List[str] = []
        for s in scopes.values():
            for eid in s.evidence_ids:
                if eid not in all_ev_ids:
                    all_ev_ids.append(eid)

        return SystemicAnomalyResponse(
            transaction_id=clean_tx_id,
            account_id=tx.account_id,
            timestamp=T.isoformat(),
            systemic_anomaly_score=systemic_anomaly_score,
            overall_systemic_risk_score=systemic_anomaly_score,
            score_interpretation="DETERMINISTIC_HEURISTIC_ANOMALY_SCORE",
            anomaly_detected=anomaly_detected,
            primary_contributing_scope=primary_scope,
            scopes=scopes,
            all_evidence_ids=all_ev_ids,
            requires_verification=anomaly_detected,
            human_approval_required=True,
            defense_only_disclaimer=(
                "Defense-only decision support. Systemic anomaly is an empirical correlation heuristic, "
                "NOT calibrated fraud probability, and NOT proof of fraud or causal fault. "
                "Human verification is strictly required."
            ),
        )

    def _evaluate_account_scope(
        self, tx: Transaction, T: datetime, evidence_items: List[Any]
    ) -> ScopeAnomalyResult:
        """Evaluate customer / account-level behavioral anomaly."""
        one_hour_ago = T - timedelta(hours=1)
        twenty_four_hours_ago = T - timedelta(hours=24)

        # Query point-in-time transaction frequency for this account
        tx_count_1h = (
            self.db.query(Transaction)
            .filter(
                Transaction.account_id == tx.account_id,
                Transaction.timestamp >= one_hour_ago,
                Transaction.timestamp <= T,
            )
            .count()
        )

        tx_count_24h = (
            self.db.query(Transaction)
            .filter(
                Transaction.account_id == tx.account_id,
                Transaction.timestamp >= twenty_four_hours_ago,
                Transaction.timestamp <= T,
            )
            .count()
        )

        # Historical transactions strictly prior to T
        prior_txs = (
            self.db.query(Transaction)
            .filter(
                Transaction.account_id == tx.account_id,
                Transaction.timestamp < T,
            )
            .all()
        )

        prior_amounts = [float(p.amount) for p in prior_txs]
        avg_prior_amt = (
            sum(prior_amounts) / len(prior_amounts) if prior_amounts else float(tx.amount)
        )
        amount_ratio = (
            float(tx.amount) / avg_prior_amt if avg_prior_amt > 0 else 1.0
        )

        prior_devices = {p.device_id for p in prior_txs}
        prior_ips = {p.ip_id for p in prior_txs}
        is_new_device = tx.device_id not in prior_devices if prior_devices else False
        is_new_ip = tx.ip_id not in prior_ips if prior_ips else False
        is_new_endpoint = is_new_device or is_new_ip

        # Build signals
        signals: List[AnomalySignal] = [
            AnomalySignal(
                name="velocity_burst_1h",
                status=SignalStatus.AVAILABLE,
                value=tx_count_1h,
                threshold=3,
                is_anomalous=tx_count_1h >= 3,
                description=f"Account executed {tx_count_1h} transactions in the trailing 1-hour window.",
                source_field="transactions.timestamp",
            ),
            AnomalySignal(
                name="velocity_burst_24h",
                status=SignalStatus.AVAILABLE,
                value=tx_count_24h,
                threshold=5,
                is_anomalous=tx_count_24h >= 5,
                description=f"Account executed {tx_count_24h} transactions in the trailing 24-hour window.",
                source_field="transactions.timestamp",
            ),
            AnomalySignal(
                name="transaction_amount_spike",
                status=SignalStatus.AVAILABLE,
                value=round(amount_ratio, 2),
                threshold=2.0,
                is_anomalous=amount_ratio >= 2.0 and len(prior_amounts) >= 1,
                description=(
                    f"Transaction amount (INR {float(tx.amount):,.2f}) is {amount_ratio:.2f}x "
                    f"the historical average (INR {avg_prior_amt:,.2f})."
                ),
                source_field="transactions.amount",
            ),
            AnomalySignal(
                name="new_hardware_or_network_endpoint",
                status=SignalStatus.AVAILABLE,
                value=is_new_endpoint,
                threshold=True,
                is_anomalous=is_new_endpoint,
                description=(
                    f"First-time endpoint usage: device={is_new_device}, IP={is_new_ip} "
                    f"relative to account history prior to transaction."
                ),
                source_field="transactions.device_id, transactions.ip_id",
            ),
            AnomalySignal(
                name="transaction_failure_rate",
                status=SignalStatus.UNAVAILABLE,
                value=None,
                threshold=None,
                is_anomalous=False,
                description="Zero transaction failures recorded in synthetic dataset (all transactions SUCCESS).",
                source_field="transactions.status",
            ),
        ]

        # Scope scoring
        active_anomalies = sum(1 for s in signals if s.status == SignalStatus.AVAILABLE and s.is_anomalous)
        if tx_count_1h >= 3 or (amount_ratio >= 2.0 and tx_count_24h >= 3):
            anomaly_score = min(1.0, 0.50 + 0.20 * active_anomalies)
            anomaly_detected = True
            status = "ANOMALOUS"
            reason = (
                f"Elevated account-level velocity and transaction value spike observed "
                f"({tx_count_1h} tx/1h, {amount_ratio:.2f}x baseline amount)."
            )
        elif active_anomalies > 0:
            anomaly_score = round(0.20 * active_anomalies, 2)
            anomaly_detected = False
            status = "NORMAL"
            reason = "Minor isolated deviation within normative consumer account variance."
        else:
            anomaly_score = 0.05
            anomaly_detected = False
            status = "NORMAL"
            reason = "Account transaction velocity and amount align with normative baseline profile."

        # Relevant evidence IDs
        ev_ids = [
            e.evidence_id for e in evidence_items
            if e.evidence_type.value in ["RAPID_FUND_FLOW", "LARGE_INCOMING_TRANSACTION", "TRANSACTION_ACTIVITY"]
        ]

        return ScopeAnomalyResult(
            scope=AnomalyScope.ACCOUNT,
            anomaly_detected=anomaly_detected,
            anomaly_score=anomaly_score,
            status=status,
            confidence="HIGH",
            reason=reason,
            signals=signals,
            evidence_ids=ev_ids,
            requires_verification=anomaly_detected,
        )

    def _evaluate_merchant_scope(
        self, tx: Transaction, T: datetime, evidence_items: List[Any]
    ) -> ScopeAnomalyResult:
        """Evaluate commercial recipient / merchant-level anomaly (P2M only)."""
        if tx.transaction_type == "TRANSFER_P2P" or tx.merchant_id is None:
            return ScopeAnomalyResult(
                scope=AnomalyScope.MERCHANT,
                anomaly_detected=False,
                anomaly_score=0.0,
                status="NOT_APPLICABLE",
                confidence="UNAVAILABLE",
                reason="Transaction is P2P transfer; no commercial merchant entity involved.",
                signals=[
                    AnomalySignal(
                        name="merchant_scope_status",
                        status=SignalStatus.NOT_APPLICABLE,
                        value="P2P_TRANSFER",
                        threshold=None,
                        is_anomalous=False,
                        description="Transaction is peer-to-peer; merchant analytics not applicable.",
                        source_field="transactions.transaction_type",
                    )
                ],
                evidence_ids=[],
                requires_verification=False,
            )

        # P2M Transaction with actual merchant
        merchant: Optional[Merchant] = (
            self.db.query(Merchant)
            .filter(Merchant.merchant_id == tx.merchant_id)
            .first()
        )
        if not merchant:
            return ScopeAnomalyResult(
                scope=AnomalyScope.MERCHANT,
                anomaly_detected=False,
                anomaly_score=0.0,
                status="INCONCLUSIVE",
                confidence="LOW",
                reason=f"Referenced merchant_id '{tx.merchant_id}' not found in merchants table.",
                signals=[],
                evidence_ids=[],
                requires_verification=True,
            )

        twenty_four_hours_ago = T - timedelta(hours=24)
        m_txs_24h = (
            self.db.query(Transaction)
            .filter(
                Transaction.merchant_id == tx.merchant_id,
                Transaction.timestamp >= twenty_four_hours_ago,
                Transaction.timestamp <= T,
            )
            .all()
        )

        distinct_buyers = len({t.account_id for t in m_txs_24h})
        tx_count_24h = len(m_txs_24h)
        is_elevated_risk_rating = merchant.merchant_risk_rating == "ELEVATED"

        signals: List[AnomalySignal] = [
            AnomalySignal(
                name="merchant_volume_burst_24h",
                status=SignalStatus.AVAILABLE,
                value=tx_count_24h,
                threshold=10,
                is_anomalous=tx_count_24h >= 10,
                description=f"Merchant received {tx_count_24h} transactions in trailing 24 hours.",
                source_field="transactions.merchant_id",
            ),
            AnomalySignal(
                name="merchant_buyer_entropy_24h",
                status=SignalStatus.AVAILABLE,
                value=distinct_buyers,
                threshold=8,
                is_anomalous=distinct_buyers >= 8,
                description=f"Transactions originated from {distinct_buyers} distinct customer accounts in 24 hours.",
                source_field="transactions.account_id",
            ),
            AnomalySignal(
                name="merchant_category_risk_rating",
                status=SignalStatus.AVAILABLE,
                value=merchant.merchant_risk_rating,
                threshold="ELEVATED",
                is_anomalous=is_elevated_risk_rating,
                description=f"Merchant risk profile rated '{merchant.merchant_risk_rating}' (Category: {merchant.merchant_category}).",
                source_field="merchants.merchant_risk_rating",
            ),
            AnomalySignal(
                name="merchant_failure_rate",
                status=SignalStatus.UNAVAILABLE,
                value=None,
                threshold=None,
                is_anomalous=False,
                description="Zero transaction failures recorded in synthetic dataset.",
                source_field="transactions.status",
            ),
        ]

        active_anomalies = sum(1 for s in signals if s.status == SignalStatus.AVAILABLE and s.is_anomalous)
        if tx_count_24h >= 10 and is_elevated_risk_rating:
            anomaly_score = 0.75
            anomaly_detected = True
            status = "ANOMALOUS"
            reason = (
                f"Elevated merchant-level influx detected: {tx_count_24h} incoming transactions "
                f"across {distinct_buyers} buyers at ELEVATED-rated merchant ({merchant.merchant_name})."
            )
        elif active_anomalies > 0:
            anomaly_score = round(0.25 * active_anomalies, 2)
            anomaly_detected = False
            status = "NORMAL"
            reason = f"Merchant processing within nominal operational parameters ({merchant.merchant_name})."
        else:
            anomaly_score = 0.05
            anomaly_detected = False
            status = "NORMAL"
            reason = "Standard commercial settlement with normative customer volume."

        return ScopeAnomalyResult(
            scope=AnomalyScope.MERCHANT,
            anomaly_detected=anomaly_detected,
            anomaly_score=anomaly_score,
            status=status,
            confidence="HIGH",
            reason=reason,
            signals=signals,
            evidence_ids=[],
            requires_verification=anomaly_detected,
        )

    def _evaluate_ring_network_scope(
        self, tx: Transaction, T: datetime, evidence_items: List[Any]
    ) -> ScopeAnomalyResult:
        """Evaluate ring / network-level topological anomaly within 2-hop boundary."""
        connected = self.graph_service.find_connected_accounts(tx.account_id)
        connected_account_ids = {c["account_id"] for c in connected if "account_id" in c}

        # Check evidence engine for multi-hop or shared infrastructure evidence
        multihop_ev = [
            e for e in evidence_items
            if e.evidence_type.value in ["MULTI_HOP_CONNECTION", "SHARED_DEVICE", "SHARED_IP", "COMMON_BENEFICIARY"]
        ]

        connected_count = len(connected_account_ids)
        twenty_four_hours_ago = T - timedelta(hours=24)

        # Measure cluster transaction activity in trailing 24h
        if connected_account_ids:
            cluster_accounts = list(connected_account_ids | {tx.account_id})
            cluster_tx_count = (
                self.db.query(Transaction)
                .filter(
                    Transaction.account_id.in_(cluster_accounts),
                    Transaction.timestamp >= twenty_four_hours_ago,
                    Transaction.timestamp <= T,
                )
                .count()
            )
        else:
            cluster_tx_count = 1

        signals: List[AnomalySignal] = [
            AnomalySignal(
                name="connected_account_cluster_size",
                status=SignalStatus.AVAILABLE,
                value=connected_count,
                threshold=3,
                is_anomalous=connected_count >= 3 and len(multihop_ev) > 0,
                description=f"Account links to {connected_count} other accounts within the 2-hop graph boundary.",
                source_field="graph.connected_accounts",
            ),
            AnomalySignal(
                name="cluster_transaction_burst_24h",
                status=SignalStatus.AVAILABLE,
                value=cluster_tx_count,
                threshold=5,
                is_anomalous=cluster_tx_count >= 5 and connected_count >= 2,
                description=f"Connected account cluster executed {cluster_tx_count} transactions in trailing 24 hours.",
                source_field="transactions.timestamp",
            ),
            AnomalySignal(
                name="multi_hop_syndicate_linkage",
                status=SignalStatus.AVAILABLE,
                value=len(multihop_ev),
                threshold=1,
                is_anomalous=len(multihop_ev) > 0,
                description=f"Verified {len(multihop_ev)} structural graph relationship evidence records.",
                source_field="evidence.multi_hop",
            ),
        ]

        ev_ids = [e.evidence_id for e in multihop_ev]

        if len(multihop_ev) > 0 and (connected_count >= 3 or cluster_tx_count >= 4):
            anomaly_score = min(1.0, 0.60 + 0.10 * min(connected_count, 4))
            anomaly_detected = True
            status = "ANOMALOUS"
            reason = (
                f"Network-level coordination anomaly: account operates within a cluster of "
                f"{connected_count} connected accounts exhibiting {len(multihop_ev)} structural co-usage links."
            )
        elif connected_count > 0:
            anomaly_score = 0.20
            anomaly_detected = False
            status = "NORMAL"
            reason = "Account exhibits incidental graph connectivity without high-velocity coordinated burst."
        else:
            anomaly_score = 0.0
            anomaly_detected = False
            status = "NORMAL"
            reason = "Account operates as an isolated singleton in the entity graph; no multi-hop connections detected."

        return ScopeAnomalyResult(
            scope=AnomalyScope.RING_NETWORK,
            anomaly_detected=anomaly_detected,
            anomaly_score=anomaly_score,
            status=status,
            confidence="HIGH",
            reason=reason,
            signals=signals,
            evidence_ids=ev_ids,
            requires_verification=anomaly_detected,
        )

    def _evaluate_systemic_infrastructure_scope(
        self, tx: Transaction, T: datetime, evidence_items: List[Any]
    ) -> ScopeAnomalyResult:
        """Evaluate possible systemic / infrastructure-level anomaly with strict non-causal safety wording."""
        ip: Optional[IPAddress] = (
            self.db.query(IPAddress)
            .filter(IPAddress.ip_id == tx.ip_id)
            .first()
        )

        beneficiary: Optional[Beneficiary] = None
        if tx.beneficiary_id:
            beneficiary = (
                self.db.query(Beneficiary)
                .filter(Beneficiary.beneficiary_id == tx.beneficiary_id)
                .first()
            )

        twenty_four_hours_ago = T - timedelta(hours=24)

        # 1. ASN / Hosting Concentration across entire platform up to T
        asn_account_count = 0
        is_hosting_asn = False
        asn_name = "UNKNOWN"
        ip_type = "UNKNOWN"
        country = "UNKNOWN"

        if ip:
            asn_name = ip.asn_org
            ip_type = ip.ip_type
            country = ip.country

            # Hosting/Datacenter/VPN classification based on empirical ip_type and ASN text
            is_hosting_asn = (
                ip_type in ["DATACENTER", "VPN"]
                or any(k in asn_name.lower() for k in ["datacenter", "droplets", "hosting", "cloud", "warp", "aws"])
            )

            asn_txs = (
                self.db.query(Transaction.account_id)
                .join(IPAddress, Transaction.ip_id == IPAddress.ip_id)
                .filter(
                    IPAddress.asn_org == ip.asn_org,
                    Transaction.timestamp >= twenty_four_hours_ago,
                    Transaction.timestamp <= T,
                )
                .distinct()
                .all()
            )
            asn_account_count = len(asn_txs)

        # 2. Beneficiary Bank Routing Concentration in trailing 24h
        bank_routing_count = 0
        if beneficiary and beneficiary.bank_ifsc_prefix:
            bank_txs = (
                self.db.query(Transaction.account_id)
                .join(Beneficiary, Transaction.beneficiary_id == Beneficiary.beneficiary_id)
                .filter(
                    Beneficiary.bank_ifsc_prefix == beneficiary.bank_ifsc_prefix,
                    Transaction.timestamp >= twenty_four_hours_ago,
                    Transaction.timestamp <= T,
                )
                .distinct()
                .all()
            )
            bank_routing_count = len(bank_txs)

        # 3. Country concentration (domestic vs cross-border)
        is_cross_border = country != "IN" if country != "UNKNOWN" else False

        signals: List[AnomalySignal] = [
            AnomalySignal(
                name="asn_infrastructure_concentration",
                status=SignalStatus.AVAILABLE if ip else SignalStatus.UNAVAILABLE,
                value=f"{asn_name} ({asn_account_count} accounts/24h)",
                threshold=">= 3 accounts on hosting ASN",
                is_anomalous=is_hosting_asn and asn_account_count >= 1,
                description=f"IP originates from {asn_name} with {asn_account_count} distinct transacting accounts in 24h.",
                source_field="ips.asn_org",
            ),
            AnomalySignal(
                name="ip_type_infrastructure",
                status=SignalStatus.AVAILABLE if ip else SignalStatus.UNAVAILABLE,
                value=ip_type,
                threshold="RESIDENTIAL / CELLULAR",
                is_anomalous=ip_type in ["DATACENTER", "VPN"],
                description=f"Endpoint network classified as '{ip_type}'.",
                source_field="ips.ip_type",
            ),
            AnomalySignal(
                name="country_origin_distribution",
                status=SignalStatus.AVAILABLE if ip else SignalStatus.UNAVAILABLE,
                value=country,
                threshold="IN",
                is_anomalous=is_cross_border,
                description=f"Transaction routed via country code '{country}'.",
                source_field="ips.country",
            ),
            AnomalySignal(
                name="beneficiary_bank_routing_concentration",
                status=SignalStatus.AVAILABLE if beneficiary else SignalStatus.NOT_APPLICABLE,
                value=(
                    f"IFSC Prefix {beneficiary.bank_ifsc_prefix} ({bank_routing_count} accounts/24h)"
                    if beneficiary else "NO_BENEFICIARY"
                ),
                threshold=">= 5 routing accounts",
                is_anomalous=bank_routing_count >= 5,
                description=(
                    f"Beneficiary bank IFSC prefix '{beneficiary.bank_ifsc_prefix}' received funds "
                    f"from {bank_routing_count} distinct accounts in 24h."
                    if beneficiary else "No beneficiary entity associated with transaction."
                ),
                source_field="beneficiaries.bank_ifsc_prefix",
            ),
            AnomalySignal(
                name="geographic_coordinates",
                status=SignalStatus.UNAVAILABLE,
                value=None,
                threshold=None,
                is_anomalous=False,
                description="No GPS coordinates or latitude/longitude fields present in dataset.",
                source_field=None,
            ),
            AnomalySignal(
                name="psp_gateway_entity",
                status=SignalStatus.UNAVAILABLE,
                value=None,
                threshold=None,
                is_anomalous=False,
                description="No specific PSP gateway entity recorded; transaction channel used.",
                source_field="transactions.channel",
            ),
        ]

        # Scoring & non-causal safety wording
        # Detect anomaly if datacenter/VPN IP used OR cross-border IP OR heavy bank IFSC convergence
        is_anomalous_infra = (is_hosting_asn or is_cross_border) or (bank_routing_count >= 5)

        if is_anomalous_infra:
            anomaly_score = 0.70
            anomaly_detected = True
            status = "ANOMALOUS"
            # STRICT SAFETY WORDING RULE: Non-causal phrasing
            reason = (
                f"Possible systemic anomaly: Elevated infrastructure-level correlation detected "
                f"across shared network routing (ASN: {asn_name}, IP Type: {ip_type}, Country: {country}). "
                f"Requires verification. Not proof of causal fault or fraud."
            )
        else:
            anomaly_score = 0.05
            anomaly_detected = False
            status = "NORMAL"
            reason = (
                f"Infrastructure routing within normative parameters ({asn_name}, {ip_type}, Country: {country}). "
                f"No anomalous infrastructure concentration detected."
            )

        ev_ids = [
            e.evidence_id for e in evidence_items
            if e.evidence_type.value in ["SHARED_IP", "COMMON_BENEFICIARY"]
        ]

        return ScopeAnomalyResult(
            scope=AnomalyScope.SYSTEMIC_INFRASTRUCTURE,
            anomaly_detected=anomaly_detected,
            anomaly_score=anomaly_score,
            status=status,
            confidence="HIGH",
            reason=reason,
            signals=signals,
            evidence_ids=ev_ids,
            requires_verification=anomaly_detected,
        )
