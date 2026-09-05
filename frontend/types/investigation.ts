/**
 * RingGuard AI — Controlled Investigation Tool Types.
 *
 * Strictly matches Stage 10 Pydantic schemas in backend/app/investigation/schemas.py.
 */

export type ToolExecutionStatus =
  | "SUCCESS"
  | "NOT_FOUND"
  | "EMPTY"
  | "LIMITED"
  | "INVALID_INPUT"
  | "UNAVAILABLE";

export interface AccountInfoResult {
  account_id: string;
  customer_id: string;
  account_created_at: string;
  account_status: string;
  account_type: string;
}

export interface TransactionRecord {
  transaction_id: string;
  account_id: string;
  timestamp: string;
  amount: number;
  transaction_type: string;
  status: string;
  channel: string;
  device_id: string;
  ip_id: string;
  beneficiary_id?: string | null;
  merchant_id?: string | null;
}

export interface RelatedAccountRecord {
  related_account_id: string;
  relationship_type: string;
  shared_entity_id: string;
  shared_entity_type: string;
  supporting_transaction_ids: string[];
}

export interface SharedDeviceRecord {
  device_id: string;
  device_type: string;
  device_os: string;
  co_using_accounts: string[];
  supporting_transaction_ids: string[];
}

export interface SharedIPRecord {
  ip_id: string;
  ip_address: string;
  ip_type: string;
  asn_org: string;
  country: string;
  co_using_accounts: string[];
  supporting_transaction_ids: string[];
}

export interface CommonBeneficiaryRecord {
  beneficiary_id: string;
  beneficiary_type: string;
  bank_ifsc_prefix: string;
  co_sending_accounts: string[];
  supporting_transaction_ids: string[];
}

export interface FundFlowHop {
  hop_number: number;
  transaction_id: string;
  timestamp: string;
  amount: number;
  source_account_id: string;
  beneficiary_id?: string | null;
  merchant_id?: string | null;
  channel: string;
  status: string;
}

export interface RiskFeaturesResult {
  transaction_id: string;
  model_name: string;
  model_version: string;
  feature_count: number;
  graph_feature_count: number;
  features: Record<string, number>;
  predicted_ring_probability: number;
  decision_threshold: number;
  risk_band: string;
  note: string;
}

export interface ToolExecutionResult<T = unknown> {
  tool_name: string;
  status: ToolExecutionStatus;
  target: string;
  as_of?: string | null;
  result: T;
  result_count: number;
  source: string;
  evidence_ids: string[];
  limitations?: string | null;
  error_details?: string | null;
  disclaimer: string;
}

export interface DossierEvidenceItem {
  evidence_id: string;
  evidence_type: string;
  severity: string;
  title: string;
  description: string;
  related_entities: string[];
  supporting_transaction_ids: string[];
  provenance_status: string;
}

export interface BenignHypothesisItem {
  hypothesis_id: string;
  title: string;
  description: string;
  triggering_signal: string;
  status: string;
  disclaimer: string;
}

export interface RecommendedInquiryItem {
  inquiry_id: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  recommended_action: string;
  target_entity_or_attribute: string;
  verification_purpose: string;
}

export interface InvestigatorDossierResponse {
  case_id: string;
  transaction_id: string;
  target_account_id: string;
  amount: number;
  timestamp: string;
  channel: string;
  status: string;
  model_a_probability: number;
  model_b_probability: number;
  risk_band: string;
  executive_summary: string;
  corroborating_evidence_chain: DossierEvidenceItem[];
  potential_benign_explanations: BenignHypothesisItem[];
  recommended_follow_up_inquiries: RecommendedInquiryItem[];
  markdown_dossier: string;
  disclaimer: string;
}

// ==============================================================================
// STAGE 15: BOUNDED UNCERTAINTY INVESTIGATION & EFFICIENCY TYPES
// ==============================================================================

export type StoppingReason =
  | "SUFFICIENT_EVIDENCE"
  | "UNCERTAINTY_LOW_ENOUGH"
  | "INFORMATION_GAIN_TOO_LOW"
  | "INVESTIGATION_COST_TOO_HIGH"
  | "EVIDENCE_EXHAUSTED"
  | "CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW"
  | "MAX_INVESTIGATION_STEPS"
  | "IN_PROGRESS";

export type NextBestActionType =
  | "ALLOW"
  | "MONITOR"
  | "REQUEST_ADDITIONAL_VERIFICATION"
  | "HOLD_FOR_REVIEW"
  | "ESCALATE_TO_ANALYST";

export interface InvestigationTraceStep {
  step_number: number;
  tool_name: string;
  target_id: string;
  simulated_cost: number;
  expected_information_gain: number;
  selection_reason: string;
  uncertainty_before: number;
  uncertainty_after: number;
  uncertainty_reduction: number;
  tool_status: string;
  evidence_count: number;
  evidence_summary: string;
  timestamp: string;
}

export interface NextBestActionResponse {
  recommended_action: NextBestActionType;
  confidence_score: number;
  evidence_sufficiency: "HIGH" | "MODERATE" | "LOW" | string;
  expected_financial_impact: string;
  reason: string;
  policy_relevant_factors: string[];
  human_approval_required: boolean;
}

export interface InvestigationStateResponse {
  transaction_id: string;
  account_id: string;
  exposure_amount: number;
  model_a_probability: number;
  model_b_probability: number;
  calibrated_risk: number;
  graph_confidence: string;
  initial_uncertainty: number;
  current_uncertainty: number;
  total_uncertainty_reduction: number;
  step_count: number;
  max_steps: number;
  total_simulated_tool_cost: number;
  max_tool_budget: number;
  stopping_status: "STOPPED" | "IN_PROGRESS" | string;
  stopping_reason: StoppingReason;
  stopping_rationale: string;
  priority_score: number;
  trace: InvestigationTraceStep[];
  evidence_collected: Record<string, any>[];
  tools_executed: string[];
  candidate_tools_remaining: string[];
  next_best_action: NextBestActionResponse;
  modeled_economics: {
    exposure_amount?: number;
    calibrated_risk?: number;
    assumed_interception_rate?: number;
    modeled_loss_avoided?: number;
    simulated_investigation_tool_cost?: number;
    human_review_cost_benchmark?: number;
    customer_friction_risk?: number;
    modeled_net_value_saved?: number;
    [key: string]: any;
  };
  disclaimer: string;
}

export interface CasePriorityItem {
  transaction_id: string;
  account_id: string;
  timestamp: string;
  amount: number;
  calibrated_risk: number;
  investigative_uncertainty: number;
  network_leverage: number;
  priority_score: number;
  triage_rank: number;
  recommended_action: string;
  priority_reason: string;
}

export interface CasePrioritizationResponse {
  total_pending_cases: number;
  cases: CasePriorityItem[];
  prioritization_formula: string;
  disclaimer: string;
}

export interface InvestigationEfficiencySlice {
  slice_name: string;
  sample_count: number;
  average_steps: number;
  median_steps: number;
  average_initial_uncertainty: number;
  average_final_uncertainty: number;
  average_uncertainty_reduction: number;
  average_tool_cost: number;
  stopping_reason_distribution: Record<string, number>;
  action_distribution: Record<string, number>;
}

export interface InvestigationEfficiencyResponse {
  status: string;
  metadata: Record<string, any>;
  slices: Record<string, InvestigationEfficiencySlice>;
  workflow_compression_summary: {
    total_cases_evaluated?: number;
    maximum_unbounded_tool_calls_possible?: number;
    actual_bounded_tool_calls_executed?: number;
    workflow_compression_percentage?: number;
    average_steps_per_investigation?: number;
    average_simulated_tool_cost_inr?: number;
    human_analyst_cost_benchmark_inr?: number;
    simulated_investigation_cost_savings_percentage?: number;
    average_initial_uncertainty?: number;
    average_uncertainty_reduction?: number;
    relative_uncertainty_reduction_percentage?: number;
    [key: string]: any;
  };
  disclaimer: string;
}

export interface RunInvestigationRequest {
  transaction_id: string;
  max_steps?: number;
  tool_budget?: number;
  interception_rate?: number;
}


