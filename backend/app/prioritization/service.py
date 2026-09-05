"""RingGuard AI — Portfolio Prioritization Service.

V2 Stage 16: Portfolio Risk Prioritization + Expected Value.
Provides deterministic, decision-theoretic case ordering and expected-value
calculations across transactions and portfolios.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.prioritization.schemas import (
    EconomicAssumptions,
    PrioritizedCaseItem,
    PortfolioPrioritizationResponse,
)
from app.services.model_service import get_model_service
from app.services.feature_service import get_feature_service
from app.investigation.agent import InvestigationAgent
from app.anomaly.service import SystemicAnomalyService
from ml.calibration.calibrator import RiskCalibrator
from ml.evaluation.cold_start import determine_graph_confidence


class PortfolioPrioritizationService:
    """Deterministic portfolio prioritization and expected-value reasoning service."""

    def __init__(self, db: Optional[Session] = None, models_dir: Optional[Path] = None):
        self.db = db or SessionLocal()
        self._owns_session = db is None
        self.model_service = get_model_service()
        self.feature_service = get_feature_service()
        self.anomaly_service = SystemicAnomalyService(self.db)
        self.economic_assumptions = EconomicAssumptions()

        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]
            self.models_dir = repo_root / "models"

        self._calibrator_b: Optional[RiskCalibrator] = None
        self._load_calibrator()

    def close(self):
        """Close database session if self-owned."""
        if self._owns_session:
            self.db.close()

    def _load_calibrator(self) -> None:
        """Load frozen post-hoc Model B calibrator if available."""
        calib_b_path = self.models_dir / "calibrator_model_b.joblib"
        if calib_b_path.exists():
            try:
                self._calibrator_b = RiskCalibrator.load(calib_b_path)
            except Exception:
                self._calibrator_b = None

    def prioritize_transaction(
        self, transaction_id: str, priority_rank: int = 1
    ) -> PrioritizedCaseItem:
        """Compute deterministic expected value and priority score for a single transaction."""
        clean_id = transaction_id.strip().upper()
        tx: Optional[Transaction] = (
            self.db.query(Transaction)
            .filter(Transaction.transaction_id == clean_id)
            .first()
        )
        if not tx:
            raise KeyError(f"Transaction '{transaction_id}' not found in database.")

        account_id = tx.account_id
        exposure = float(tx.amount)
        ts_iso = tx.timestamp.isoformat()

        # 1. Model B Platt-calibrated risk probability
        try:
            feats_df_b, _ = self.feature_service.get_features(self.db, clean_id, model_type="graph")
            p_raw_b = self.model_service.predict_graph(feats_df_b)

            if self._calibrator_b is not None:
                p_calibrated = float(self._calibrator_b.predict_calibrated_proba([p_raw_b])[0])
            else:
                p_calibrated = p_raw_b
            p_calibrated = round(max(0.0, min(1.0, p_calibrated)), 4)

            graph_conf = determine_graph_confidence(feats_df_b.iloc[0])
            u0 = round(InvestigationAgent.compute_initial_uncertainty(p_calibrated, graph_conf), 4)

            connected_accs = (
                float(feats_df_b["g_connected_accounts_count"].iloc[0])
                if "g_connected_accounts_count" in feats_df_b
                else 0.0
            )
            network_leverage = round(min(1.0, connected_accs / 10.0), 4)

        except Exception:
            # Deterministic fallback if point-in-time graph lookup is unavailable
            p_calibrated = 0.50
            u0 = 0.50
            network_leverage = 0.0

        # 2. Stage 15 Systemic Anomaly Score
        try:
            sys_res = self.anomaly_service.analyze_transaction(clean_id)
            systemic_anomaly = round(sys_res.systemic_anomaly_score, 4)
        except Exception:
            systemic_anomaly = 0.0

        # 3. Decision-Theoretic Expected Value Formulation
        # Expected Loss Avoided = p_calibrated * Exposure * InterceptionRate
        interception_rate = self.economic_assumptions.interception_rate
        expected_loss_avoided = round(p_calibrated * exposure * interception_rate, 2)

        # Expected Friction Cost = (1 - p_calibrated) * CFP
        cfp = self.economic_assumptions.friction_cost_per_false_positive_cfp
        friction_cost = round((1.0 - p_calibrated) * cfp, 2)

        # Expected Investigation Cost = Cinv
        cinv = self.economic_assumptions.cost_per_investigation_cinv
        investigation_cost = round(cinv, 2)

        # Expected Value = Expected Loss Avoided - Expected Friction Cost - Expected Investigation Cost
        expected_value = round(expected_loss_avoided - friction_cost - investigation_cost, 2)

        # Global deterministic EV normalization cap (100000 max exposure * 0.85 interception rate = 85000)
        # EVnorm = clip(ExpectedValue / 85000.0, 0.0, 1.0)
        ev_cap = self.economic_assumptions.ev_cap
        ev_norm = round(max(0.0, min(1.0, expected_value / ev_cap)), 4)

        # Exposure normalization (bounded by 100,000 INR)
        exp_norm = round(min(exposure, 100000.0) / 100000.0, 4)

        # 4. Deterministic Weighted Priority Formula (All components strictly in [0.0, 1.0])
        priority_score = round(
            0.25 * p_calibrated
            + 0.25 * ev_norm
            + 0.15 * exp_norm
            + 0.15 * network_leverage
            + 0.10 * systemic_anomaly
            + 0.10 * u0,
            4,
        )

        # Investigation Queue Priority Recommendation (NOT financial/risk policy)
        if priority_score >= 0.70 or (expected_value > 0 and p_calibrated >= 0.70):
            rec_action = "PRIORITIZE_INVESTIGATION"
        elif priority_score >= 0.50 or expected_value > 0:
            rec_action = "HIGH_PRIORITY_REVIEW"
        elif u0 > 0.40 or priority_score >= 0.30:
            rec_action = "REVIEW_NEXT"
        elif priority_score >= 0.10:
            rec_action = "LOW_PRIORITY"
        else:
            rec_action = "NO_IMMEDIATE_INVESTIGATION"

        # Interpretable Priority Reason: "Why should an analyst investigate this case before another?"
        if expected_value > 0:
            priority_reason = (
                f"High expected value of investigation (₹{expected_value:,.2f} net saved) driven by "
                f"{p_calibrated * 100:.1f}% calibrated risk, ₹{exposure:,.2f} exposure, "
                f"network leverage ({network_leverage:.2f}), and systemic anomaly ({systemic_anomaly:.2f})."
            )
        else:
            priority_reason = (
                f"Negative expected value (₹{expected_value:,.2f}); investigation friction (₹{friction_cost:,.2f}) "
                f"and operational review cost (₹{investigation_cost:,.2f}) outweigh nominal loss avoided "
                f"(₹{expected_loss_avoided:,.2f}) for low risk ({p_calibrated * 100:.2f}%)."
            )

        return PrioritizedCaseItem(
            transaction_id=clean_id,
            account_id=account_id,
            timestamp=ts_iso,
            risk_score=p_calibrated,
            exposure=exposure,
            network_leverage=network_leverage,
            systemic_anomaly_score=systemic_anomaly,
            investigative_uncertainty=u0,
            expected_loss_avoided=expected_loss_avoided,
            friction_cost=friction_cost,
            investigation_cost=investigation_cost,
            expected_value=expected_value,
            ev_normalized=ev_norm,
            priority_score=priority_score,
            priority_rank=priority_rank,
            recommended_action=rec_action,
            priority_reason=priority_reason,
            economic_assumptions=self.economic_assumptions,
            synthetic_monetary_value_disclaimer=(
                "SIMULATED / SYNTHETIC ESTIMATE: Monetary values reflect risk modeling heuristics on "
                "synthetic benchmark data and do not represent real Razorpay customer data, "
                "merchant balances, or actual financial recovery."
            ),
            human_approval_required=True,
        )

    def prioritize_portfolio(
        self,
        transaction_ids: Optional[List[str]] = None,
        limit: int = 20,
    ) -> PortfolioPrioritizationResponse:
        """Score and sort portfolio cases descending by deterministic priority score."""
        # 1. Resolve transaction set
        if transaction_ids:
            txs = (
                self.db.query(Transaction)
                .filter(Transaction.transaction_id.in_(transaction_ids))
                .all()
            )
        else:
            primary_candidates = ["TXN_00000203", "TXN_00000001", "TXN_00000646", "TXN_00000500"]
            primary_txs = (
                self.db.query(Transaction)
                .filter(Transaction.transaction_id.in_(primary_candidates))
                .all()
            )
            existing_ids = {t.transaction_id for t in primary_txs}

            extra_txs = (
                self.db.query(Transaction)
                .filter(~Transaction.transaction_id.in_(existing_ids))
                .order_by(Transaction.amount.desc())
                .limit(max(0, limit - len(primary_txs)))
                .all()
            )
            txs = primary_txs + extra_txs

        # 2. Score each transaction independently
        items: List[PrioritizedCaseItem] = []
        for tx in txs:
            item = self.prioritize_transaction(tx.transaction_id, priority_rank=1)
            items.append(item)

        # 3. Sort descending by deterministic priority_score, tie-breaker by exposure
        items.sort(key=lambda x: (x.priority_score, x.exposure), reverse=True)

        # 4. Assign 1-indexed ranks based on global ordering
        for rank, item in enumerate(items, start=1):
            item.priority_rank = rank

        # 5. Compute portfolio totals
        total_ev = round(sum(i.expected_value for i in items), 2)
        total_exp = round(sum(i.exposure for i in items), 2)

        return PortfolioPrioritizationResponse(
            total_cases_evaluated=len(items),
            portfolio_expected_value_sum=total_ev,
            portfolio_total_exposure=total_exp,
            cases=items,
            economic_assumptions=self.economic_assumptions,
            scoring_formula=(
                "Priority Score = 0.25 * p_calibrated + 0.25 * EVnorm + 0.15 * Expnorm + "
                "0.15 * NetworkLeverage + 0.10 * SystemicAnomaly + 0.10 * u0"
            ),
            economic_formula=(
                "Expected Value = Expected Loss Avoided - Expected Friction Cost - Expected Investigation Cost"
            ),
            synthetic_monetary_value_disclaimer=(
                "SIMULATED / SYNTHETIC ESTIMATE: Monetary values reflect risk modeling heuristics on "
                "synthetic benchmark data and do not represent real Razorpay customer data, "
                "merchant balances, or actual financial recovery."
            ),
            human_approval_required=True,
        )
