"""RingGuard AI — Threshold Policy Optimizer & Economic Sensitivity Engine.

Stage 14: Cold Start + Calibration + Thresholding.
Optimizes operational threshold policy scenarios on validation data,
evaluates economic sensitivity under stated operational assumptions,
and measures post-freeze generalization on the untouched held-out test set.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from ml.evaluation.metrics import evaluate_binary_predictions


class ThresholdPolicyOptimizer:
    """Optimizes discrete threshold scenarios on validation data with economic sensitivity."""

    def __init__(
        self,
        interception_rate: float = 0.85,
        fp_friction_cost: float = 1200.0,
        investigation_cost: float = 350.0,
    ):
        # Explicit configurable operational modeling assumptions
        self.interception_rate = interception_rate
        self.fp_friction_cost = fp_friction_cost
        self.investigation_cost = investigation_cost

        self.threshold_sweep: List[Dict[str, Any]] = []
        self.policy_scenarios: Dict[str, Any] = {}
        self.sensitivity_analysis: List[Dict[str, Any]] = []
        self.is_optimized: bool = False

    def _compute_economic_value(
        self,
        amounts: np.ndarray,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        interception: float,
        cm: Optional[Dict[str, int]] = None,
    ) -> Dict[str, float]:
        """Compute modeled financial metrics directly from confusion-matrix counts under stated assumptions.

        Formula:
            Modeled Net Value Saved = Modeled Loss Avoided - (FP * CFP) - ((TP + FP) * Cinv)
            where Modeled Loss Avoided = (TP Exposure * Interception Rate)
        """
        tp_mask = (y_true == 1) & (y_pred == 1)
        fp_mask = (y_true == 0) & (y_pred == 1)

        if cm is not None:
            tp_count = int(cm.get("true_positives", int(np.sum(tp_mask))))
            fp_count = int(cm.get("false_positives", int(np.sum(fp_mask))))
        else:
            tp_count = int(np.sum(tp_mask))
            fp_count = int(np.sum(fp_mask))

        # Flagged cases strictly equal (TP + FP)
        case_count = tp_count + fp_count

        tp_amount = float(np.sum(amounts[tp_mask]))
        modeled_loss_avoided = round(tp_amount * interception, 2)
        modeled_friction_cost = round(float(fp_count * self.fp_friction_cost), 2)
        modeled_investigation_cost = round(float(case_count * self.investigation_cost), 2)
        modeled_net_value_saved = round(
            modeled_loss_avoided - modeled_friction_cost - modeled_investigation_cost, 2
        )

        return {
            "interception_rate_assumed": interception,
            "tp_count": tp_count,
            "fp_count": fp_count,
            "flagged_case_count": case_count,
            "tp_exposure_amount": tp_amount,
            "modeled_loss_avoided": modeled_loss_avoided,
            "modeled_friction_cost": modeled_friction_cost,
            "modeled_investigation_cost": modeled_investigation_cost,
            "modeled_net_value_saved": modeled_net_value_saved,
        }

    def run_validation_sweep(
        self,
        y_val: np.ndarray,
        p_val: np.ndarray,
        amounts_val: np.ndarray,
    ) -> "ThresholdPolicyOptimizer":
        """Sweep thresholds T in [0.01, 0.99] strictly on Val-Thresh (N=150)."""
        thresholds = [round(t, 2) for t in np.arange(0.01, 1.00, 0.01)]
        self.threshold_sweep = []

        best_f1 = -1.0
        best_t_f1 = 0.50

        best_net_val = -float("inf")
        best_t_econ = 0.50

        # Sweep all thresholds
        for t in thresholds:
            m = evaluate_binary_predictions(y_val, p_val, threshold=t)
            econ = self._compute_economic_value(
                amounts_val, y_val, (p_val >= t).astype(int), self.interception_rate, cm=m["confusion_matrix"]
            )

            point = {
                "threshold": t,
                "precision": m["precision"],
                "recall": m["recall"],
                "f1": m["f1"],
                "fpr": m["false_positive_rate"],
                "tp": m["confusion_matrix"]["true_positives"],
                "fp": m["confusion_matrix"]["false_positives"],
                "tn": m["confusion_matrix"]["true_negatives"],
                "fn": m["confusion_matrix"]["false_negatives"],
                "modeled_net_value_saved": econ["modeled_net_value_saved"],
                "modeled_loss_avoided": econ["modeled_loss_avoided"],
            }
            self.threshold_sweep.append(point)

            if m["f1"] >= best_f1:
                best_f1 = m["f1"]
                best_t_f1 = t

            if econ["modeled_net_value_saved"] >= best_net_val:
                best_net_val = econ["modeled_net_value_saved"]
                best_t_econ = t

        # Derive 4 Distinct Policy Scenarios:
        # Scenario 1: Max F1
        scen_f1 = {
            "scenario_name": "Maximum F1 Policy",
            "threshold": best_t_f1,
            "status": "FEASIBLE",
            "primary_metric": "f1",
            "primary_value": best_f1,
            "description": "Standard balance between precision and recall",
        }

        # Scenario 2: Strict FPR Control (FPR <= 0.02)
        eligible_fpr = [p for p in self.threshold_sweep if p["fpr"] <= 0.02]
        if eligible_fpr:
            # Pick highest recall, tie-break highest threshold
            best_fpr_point = max(eligible_fpr, key=lambda x: (x["recall"], x["threshold"]))
            scen_fpr = {
                "scenario_name": "Strict False-Positive Control (FPR <= 0.02)",
                "threshold": best_fpr_point["threshold"],
                "status": "FEASIBLE",
                "primary_metric": "recall",
                "primary_value": best_fpr_point["recall"],
                "description": "Regulated low-friction policy bounding false positive rate at or below 2%",
            }
        else:
            scen_fpr = {
                "scenario_name": "Strict False-Positive Control (FPR <= 0.02)",
                "threshold": None,
                "status": "INFEASIBLE_ON_VALIDATION",
                "primary_metric": "recall",
                "primary_value": 0.0,
                "description": "No threshold on validation set satisfied the constraint FPR <= 0.02",
            }

        # Scenario 3: High Precision / Low Friction (Precision >= 0.85)
        eligible_prec = [p for p in self.threshold_sweep if p["precision"] >= 0.85]
        if eligible_prec:
            best_prec_point = max(eligible_prec, key=lambda x: (x["recall"], x["threshold"]))
            scen_prec = {
                "scenario_name": "High Precision / Low Friction (Precision >= 0.85)",
                "threshold": best_prec_point["threshold"],
                "status": "FEASIBLE",
                "primary_metric": "recall",
                "primary_value": best_prec_point["recall"],
                "description": "High-confidence investigation queue targeting at least 85% precision",
            }
        else:
            scen_prec = {
                "scenario_name": "High Precision / Low Friction (Precision >= 0.85)",
                "threshold": None,
                "status": "INFEASIBLE_ON_VALIDATION",
                "primary_metric": "recall",
                "primary_value": 0.0,
                "description": "No threshold on validation set satisfied the constraint Precision >= 0.85",
            }

        # Scenario 4: Economic Value Maximization (RECOMMENDED OPERATIONAL THRESHOLD)
        scen_econ = {
            "scenario_name": "Economic Value Maximization Policy (RECOMMENDED OPERATIONAL THRESHOLD)",
            "threshold": best_t_econ,
            "status": "FEASIBLE",
            "primary_metric": "modeled_net_value_saved",
            "primary_value": best_net_val,
            "description": "Primary recommended operational threshold maximizing modeled net value saved under stated assumptions",
            "is_recommended": True,
        }

        self.policy_scenarios = {
            "T_star_f1": scen_f1,
            "T_star_fpr": scen_fpr,
            "T_star_precision": scen_prec,
            "T_star_economic": scen_econ,
        }

        # Economic Sensitivity Analysis across 4 interception tiers
        self.sensitivity_analysis = []
        tiers = [0.50, 0.70, 0.85, 1.00]
        for rate in tiers:
            tier_best_val = -float("inf")
            tier_best_t = 0.50
            for t in thresholds:
                m_t = evaluate_binary_predictions(y_val, p_val, threshold=t)
                econ_tier = self._compute_economic_value(
                    amounts_val, y_val, (p_val >= t).astype(int), rate, cm=m_t["confusion_matrix"]
                )
                if econ_tier["modeled_net_value_saved"] >= tier_best_val:
                    tier_best_val = econ_tier["modeled_net_value_saved"]
                    tier_best_t = t

            tier_m = evaluate_binary_predictions(y_val, p_val, threshold=tier_best_t)
            tier_econ = self._compute_economic_value(
                amounts_val, y_val, (p_val >= tier_best_t).astype(int), rate, cm=tier_m["confusion_matrix"]
            )
            self.sensitivity_analysis.append({
                "interception_tier_label": f"{int(rate * 100)}% Interception",
                "interception_rate": rate,
                "optimal_threshold": tier_best_t,
                "is_stable_with_baseline": tier_best_t == best_t_econ,
                "modeled_loss_avoided": tier_econ["modeled_loss_avoided"],
                "modeled_friction_cost": tier_econ["modeled_friction_cost"],
                "modeled_investigation_cost": tier_econ["modeled_investigation_cost"],
                "modeled_net_value_saved": tier_econ["modeled_net_value_saved"],
            })

        self.is_optimized = True
        return self

    def evaluate_held_out_test(
        self,
        y_test: np.ndarray,
        p_test: np.ndarray,
        amounts_test: np.ndarray,
    ) -> Dict[str, Any]:
        """Evaluate each policy on the held-out test set strictly at its OWN frozen threshold."""
        if not self.is_optimized:
            raise RuntimeError("Must run validation sweep and freeze thresholds before evaluating test set!")

        test_results = {}

        for key, policy in self.policy_scenarios.items():
            t = policy["threshold"]
            if policy["status"] == "INFEASIBLE_ON_VALIDATION" or t is None:
                test_results[key] = {
                    "policy_name": policy["scenario_name"],
                    "status": "NOT_EVALUATED_INFEASIBLE_POLICY",
                    "threshold_applied": None,
                    "metrics": None,
                }
                continue

            m = evaluate_binary_predictions(y_test, p_test, threshold=t)
            econ = self._compute_economic_value(
                amounts_test, y_test, (p_test >= t).astype(int), self.interception_rate, cm=m["confusion_matrix"]
            )

            test_results[key] = {
                "policy_name": policy["scenario_name"],
                "status": "EVALUATED",
                "threshold_applied": t,
                "metrics": {
                    "precision": m["precision"],
                    "recall": m["recall"],
                    "f1": m["f1"],
                    "false_positive_rate": m["false_positive_rate"],
                    "confusion_matrix": m["confusion_matrix"],
                },
                "modeled_economics": econ,
                "is_recommended": policy.get("is_recommended", False),
            }

        return test_results

    def compute_held_out_sensitivity(
        self,
        y_test: np.ndarray,
        p_test: np.ndarray,
        amounts_test: np.ndarray,
        threshold: float = 0.99,
    ) -> List[Dict[str, Any]]:
        """Compute economic sensitivity on the held-out test set at the recommended threshold."""
        tiers = [0.50, 0.70, 0.85, 1.00]
        m = evaluate_binary_predictions(y_test, p_test, threshold=threshold)
        test_sensitivity = []
        for rate in tiers:
            econ = self._compute_economic_value(
                amounts_test, y_test, (p_test >= threshold).astype(int), rate, cm=m["confusion_matrix"]
            )
            test_sensitivity.append({
                "interception_tier_label": f"{int(rate * 100)}% Interception",
                "interception_rate": rate,
                "threshold_applied": threshold,
                "tp_count": econ["tp_count"],
                "fp_count": econ["fp_count"],
                "flagged_case_count": econ["flagged_case_count"],
                "tp_exposure_amount": econ["tp_exposure_amount"],
                "modeled_loss_avoided": econ["modeled_loss_avoided"],
                "modeled_friction_cost": econ["modeled_friction_cost"],
                "modeled_investigation_cost": econ["modeled_investigation_cost"],
                "modeled_net_value_saved": econ["modeled_net_value_saved"],
            })
        return test_sensitivity
