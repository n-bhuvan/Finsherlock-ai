"""RingGuard AI — Deterministic Synthesized Investigator Dossier Service.

Stage 12: Final Packaging & Submission Readiness.
Deterministically synthesizes structured case briefs, corroborating evidence chains,
potential benign explanations (hypotheses), and non-autonomous recommended inquiries.
Zero external LLM dependencies, 100% offline and deterministic.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.services.model_service import get_model_service, ModelService
from app.services.feature_service import get_feature_service, FeatureService
from app.evidence.engine import EvidenceEngine
from app.evidence.schemas import EvidenceType
from app.investigation.schemas import (
    InvestigatorDossierResponse,
    DossierEvidenceItem,
    BenignHypothesisItem,
    RecommendedInquiryItem,
)


class DossierService:
    """Service to construct deterministic, structured case briefs for human analysts."""

    def __init__(
        self,
        model_service: Optional[ModelService] = None,
        feature_service: Optional[FeatureService] = None,
    ):
        self.model_service = model_service or get_model_service()
        self.feature_service = feature_service or get_feature_service()

    def generate_dossier(self, db: Session, transaction_id: str) -> InvestigatorDossierResponse:
        """Generate structured investigation dossier for a verified transaction.
        
        Args:
            db: Active SQLAlchemy database session.
            transaction_id: Transaction identifier.
            
        Returns:
            InvestigatorDossierResponse schema with all structured sections and markdown.
        """
        # 1. Fetch verified transaction and feature vectors
        feats_a, txn = self.feature_service.get_features(db, transaction_id, model_type="baseline")
        feats_b, _ = self.feature_service.get_features(db, transaction_id, model_type="graph")

        model_a_prob = self.model_service.predict_baseline(feats_a)
        model_b_prob = self.model_service.predict_graph(feats_b)
        risk_band = self.model_service.determine_risk_band(model_b_prob).value

        # 2. Extract verified Stage 9 evidence
        evidence_engine = EvidenceEngine(db)
        try:
            ev_list = evidence_engine.extract_evidence_for_transaction(transaction_id)
            raw_evidence = ev_list.items
        except Exception:
            raw_evidence = []

        # 3. Transform top evidence items
        evidence_chain: List[DossierEvidenceItem] = []
        observed_evidence_types = set()
        for ev in raw_evidence[:5]:
            observed_evidence_types.add(ev.evidence_type)
            evidence_chain.append(
                DossierEvidenceItem(
                    evidence_id=ev.evidence_id,
                    evidence_type=ev.evidence_type.value,
                    severity=ev.severity.value,
                    title=ev.title,
                    description=ev.description,
                    related_entities=ev.related_entities,
                    supporting_transaction_ids=ev.supporting_transaction_ids,
                    provenance_status=ev.status,
                )
            )

        # 4. Formulate Potential Benign Explanations (strictly classified as hypotheses)
        benign_hypotheses: List[BenignHypothesisItem] = []
        hypo_idx = 1

        if EvidenceType.SHARED_IP in observed_evidence_types:
            benign_hypotheses.append(
                BenignHypothesisItem(
                    hypothesis_id=f"HYPO_{transaction_id}_{hypo_idx}",
                    title="Corporate Proxy or Cellular CGNAT Network Range",
                    description=(
                        "The observed IP co-usage may reflect legitimate multi-user routing via an enterprise "
                        "VPN concentrator, university campus egress, or mobile network Carrier-Grade NAT (CGNAT)."
                    ),
                    triggering_signal="Co-used IP address identified across multiple account identifiers.",
                )
            )
            hypo_idx += 1

        if EvidenceType.SHARED_DEVICE in observed_evidence_types:
            benign_hypotheses.append(
                BenignHypothesisItem(
                    hypothesis_id=f"HYPO_{transaction_id}_{hypo_idx}",
                    title="Household or Family Shared Hardware Terminal",
                    description=(
                        "Multiple family or household members may legitimately share a common tablet, home workstation, "
                        "or public kiosk for independent banking activities."
                    ),
                    triggering_signal="Hardware device fingerprint linked to more than one active account.",
                )
            )
            hypo_idx += 1

        if EvidenceType.COMMON_BENEFICIARY in observed_evidence_types:
            benign_hypotheses.append(
                BenignHypothesisItem(
                    hypothesis_id=f"HYPO_{transaction_id}_{hypo_idx}",
                    title="Commercial Aggregator, Utility, or Marketplace Seller",
                    description=(
                        "The recipient account may be an authorized corporate biller, housing society payment hub, "
                        "or high-volume marketplace merchant receiving funds from diverse independent payers."
                    ),
                    triggering_signal="Common beneficiary receiving inbound transfers from multiple accounts.",
                )
            )
            hypo_idx += 1

        if not benign_hypotheses:
            benign_hypotheses.append(
                BenignHypothesisItem(
                    hypothesis_id=f"HYPO_{transaction_id}_{hypo_idx}",
                    title="Standard Autonomous Consumer Transaction",
                    description=(
                        "Transaction parameters, behavioral history, and endpoint relationships exhibit no "
                        "anomalous cluster sharing; activity is consistent with normal consumer payment behavior."
                    ),
                    triggering_signal="Baseline transaction attributes within typical user velocity boundaries.",
                )
            )

        # 5. Formulate Recommended Follow-up Inquiries (Strictly Human Investigation)
        inquiries: List[RecommendedInquiryItem] = []
        inq_idx = 1

        if EvidenceType.SHARED_DEVICE in observed_evidence_types:
            inquiries.append(
                RecommendedInquiryItem(
                    inquiry_id=f"INQ_{transaction_id}_{inq_idx}",
                    priority="HIGH",
                    recommended_action="Request hardware confirmation or biometrics-backed step-up authentication.",
                    target_entity_or_attribute="Device Hardware ID",
                    verification_purpose="Confirm whether distinct account holders share physical possession of device.",
                )
            )
            inq_idx += 1

        if EvidenceType.COMMON_BENEFICIARY in observed_evidence_types:
            inquiries.append(
                RecommendedInquiryItem(
                    inquiry_id=f"INQ_{transaction_id}_{inq_idx}",
                    priority="HIGH",
                    recommended_action="Audit recipient account KYC level and review counterparty volume history.",
                    target_entity_or_attribute="Beneficiary Account",
                    verification_purpose="Assess if recipient operates as a legitimate aggregator or centralized mule node.",
                )
            )
            inq_idx += 1

        if EvidenceType.SHARED_IP in observed_evidence_types:
            inquiries.append(
                RecommendedInquiryItem(
                    inquiry_id=f"INQ_{transaction_id}_{inq_idx}",
                    priority="MEDIUM",
                    recommended_action="Inspect IP ASN and subnet classification against commercial VPN rosters.",
                    target_entity_or_attribute="IP Address & Autonomous System",
                    verification_purpose="Distinguish commercial hosting/proxy centers from legitimate residential connections.",
                )
            )
            inq_idx += 1

        inquiries.append(
            RecommendedInquiryItem(
                inquiry_id=f"INQ_{transaction_id}_{inq_idx}",
                priority="LOW",
                recommended_action="Review customer outbound notification delivery logs and recent credential changes.",
                target_entity_or_attribute="Account Security History",
                verification_purpose="Rule out account takeover (ATO) preceding large value transfer.",
            )
        )

        # 6. Formulate Executive Summary
        tx_amt_formatted = f"₹{float(txn.amount):,.2f}"
        summary_ev_titles = ", ".join([e.title for e in evidence_chain[:2]]) if evidence_chain else "none observed"
        exec_summary = (
            f"Transaction {transaction_id} transferred {tx_amt_formatted} via {txn.channel} "
            f"from account {txn.account_id} at {txn.timestamp}. "
            f"Evaluated with Model A (Baseline: {model_a_prob*100:.2f}%) and Model B (Network-Enhanced: {model_b_prob*100:.2f}%), "
            f"resulting in a {risk_band} risk band. Observed topological indicators include {summary_ev_titles}. "
            f"Human review recommended to verify endpoint co-usage against potential benign explanations."
        )

        # 7. Formulate Pre-formatted Markdown Dossier
        case_id = f"CASE_{transaction_id}"
        md_lines = [
            f"# RingGuard AI — Investigator Dossier: {case_id}",
            "",
            "## 1. Case Metadata & Risk Assessment",
            f"- **Transaction ID:** `{transaction_id}`",
            f"- **Target Account:** `{txn.account_id}`",
            f"- **Amount:** `{tx_amt_formatted}`",
            f"- **Payment Channel:** `{txn.channel}`",
            f"- **Timestamp:** `{txn.timestamp}`",
            f"- **Model A Probability:** `{model_a_prob*100:.2f}%`",
            f"- **Model B Probability:** `{model_b_prob*100:.2f}%`",
            f"- **Risk Classification:** **{risk_band}**",
            "",
            "## 2. Executive Summary",
            f"{exec_summary}",
            "",
            "## 3. Corroborating Evidence Chain (Stage 9 Verified)",
        ]

        if evidence_chain:
            for ev in evidence_chain:
                md_lines.append(f"### [{ev.severity}] {ev.title}")
                md_lines.append(f"- **Evidence ID:** `{ev.evidence_id}`")
                md_lines.append(f"- **Description:** {ev.description}")
                if ev.related_entities:
                    md_lines.append(f"- **Related Entities:** {', '.join([f'`{ent}`' for ent in ev.related_entities])}")
                if ev.supporting_transaction_ids:
                    md_lines.append(f"- **Supporting Transactions:** {', '.join([f'`{t}`' for t in ev.supporting_transaction_ids])}")
                md_lines.append("")
        else:
            md_lines.append("*No high-severity structural evidence items identified for this transaction.*")
            md_lines.append("")

        md_lines.extend([
            "## 4. Potential Benign Explanations (Hypotheses)",
            "> [!NOTE]",
            "> **Hypothesis Classification Notice:** The following scenarios represent potential benign explanations "
            "for observed patterns. Additional human verification is strictly required before reaching conclusions.",
            "",
        ])

        for h in benign_hypotheses:
            md_lines.append(f"### {h.title}")
            md_lines.append(f"- **Hypothesis ID:** `{h.hypothesis_id}`")
            md_lines.append(f"- **Triggering Signal:** {h.triggering_signal}")
            md_lines.append(f"- **Evaluation:** {h.description}")
            md_lines.append("")

        md_lines.extend([
            "## 5. Recommended Follow-up Verification (Human-in-the-Loop)",
        ])

        for inq in inquiries:
            md_lines.append(f"- **[{inq.priority}] {inq.recommended_action}**")
            md_lines.append(f"  - *Target:* {inq.target_entity_or_attribute}")
            md_lines.append(f"  - *Purpose:* {inq.verification_purpose}")

        md_lines.extend([
            "",
            "---",
            "> [!IMPORTANT]",
            "> **Defense-Only Compliance Boundary:** This dossier is synthesized deterministically for human risk investigators. "
            "RingGuard AI does not perform automated payment blocking, fund freezing, or autonomous account enforcement.",
        ])

        markdown_dossier = "\n".join(md_lines)

        return InvestigatorDossierResponse(
            case_id=case_id,
            transaction_id=transaction_id,
            target_account_id=txn.account_id,
            amount=float(txn.amount),
            timestamp=str(txn.timestamp),
            channel=txn.channel,
            status=txn.status,
            model_a_probability=model_a_prob,
            model_b_probability=model_b_prob,
            risk_band=risk_band,
            executive_summary=exec_summary,
            corroborating_evidence_chain=evidence_chain,
            potential_benign_explanations=benign_hypotheses,
            recommended_follow_up_inquiries=inquiries,
            markdown_dossier=markdown_dossier,
        )


_dossier_service_instance: Optional[DossierService] = None


def get_dossier_service() -> DossierService:
    """Retrieve or initialize global DossierService singleton."""
    global _dossier_service_instance
    if _dossier_service_instance is None:
        _dossier_service_instance = DossierService()
    return _dossier_service_instance
