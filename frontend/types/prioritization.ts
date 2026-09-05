// RingGuard AI V2 Stage 16: Portfolio Risk Prioritization & Expected Value Types

export interface EconomicAssumptions {
  interception_rate: number;
  cost_per_investigation_cinv: number;
  friction_cost_per_false_positive_cfp: number;
  ev_cap: number;
  monetary_unit: string;
  simulated_estimate: boolean;
}

export interface PrioritizedCaseItem {
  transaction_id: string;
  account_id: string;
  timestamp: string;
  risk_score: number;
  exposure: number;
  network_leverage: number;
  systemic_anomaly_score: number;
  investigative_uncertainty: number;
  expected_loss_avoided: number;
  friction_cost: number;
  investigation_cost: number;
  expected_value: number;
  ev_normalized: number;
  priority_score: number;
  priority_rank: number;
  recommended_action:
    | "PRIORITIZE_INVESTIGATION"
    | "HIGH_PRIORITY_REVIEW"
    | "REVIEW_NEXT"
    | "LOW_PRIORITY"
    | "NO_IMMEDIATE_INVESTIGATION"
    | string;
  priority_reason: string;
  economic_assumptions: EconomicAssumptions;
  synthetic_monetary_value_disclaimer: string;
  human_approval_required: boolean;
}

export interface PortfolioPrioritizationResponse {
  total_cases_evaluated: number;
  portfolio_expected_value_sum: number;
  portfolio_total_exposure: number;
  cases: PrioritizedCaseItem[];
  scoring_formula: string;
  economic_formula: string;
  economic_assumptions: EconomicAssumptions;
  synthetic_monetary_value_disclaimer: string;
  human_approval_required: boolean;
}
