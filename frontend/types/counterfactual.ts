// RingGuard AI V2 Stage 18: Counterfactual Attribution & Intervention Simulation Types

export type AttributionDirection = "INCREASES_RISK" | "DECREASES_RISK" | "NEUTRAL";

export type InterventionMode =
  | "REMOVE_RISK_SIGNAL"
  | "REDUCE_RISK_SIGNAL"
  | "BASELINE_COMPARISON"
  | "CUSTOM_PERTURBATION";

export type PlausibilityStatus = "PLAUSIBLE" | "HYPOTHETICAL" | "UNAVAILABLE";

export interface CounterfactualAttribution {
  feature_name: string;
  actual_value: number;
  contribution: number;
  direction: AttributionDirection;
  attribution_rank: number;
  explanation: string;
  source: string;
}

export interface CounterfactualIntervention {
  intervention_id: string;
  feature_name: string;
  original_value: any;
  counterfactual_value: any;
  original_risk_score: number;
  counterfactual_risk_score: number;
  risk_delta: number;
  direction: AttributionDirection;
  intervention_mode: InterventionMode;
  plausibility_status: PlausibilityStatus;
  assumption: string;
  disclaimer: string;
}

export interface CounterfactualAnalysisResponse {
  transaction_id: string;
  account_id: string;
  timestamp: string;
  model_name: string;
  model_version: string;
  original_risk_score: number;
  original_probability_raw: number;
  attributions: CounterfactualAttribution[];
  interventions: CounterfactualIntervention[];
  strongest_model_attribution?: CounterfactualAttribution;
  largest_simulated_risk_delta?: CounterfactualIntervention;
  human_approval_required: boolean;
  defense_only: boolean;
  disclaimer: string;
}

export interface CustomInterventionRequest {
  feature_name: string;
  target_value: number;
}
