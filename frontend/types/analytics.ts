/**
 * RingGuard AI — Analytics Type Definitions.
 */

export interface MetricComparison {
  metric_label: string;
  model_a_baseline: number;
  model_b_graph: number;
  delta: number;
}

export interface SplitMetrics {
  pr_auc: MetricComparison;
  roc_auc: MetricComparison;
  precision: MetricComparison;
  recall: MetricComparison;
  f1: MetricComparison;
  false_positive_rate: MetricComparison;
  confusion_matrix: {
    model_a: {
      true_negatives: number;
      false_positives: number;
      false_negatives: number;
      true_positives: number;
    };
    model_b: {
      true_negatives: number;
      false_positives: number;
      false_negatives: number;
      true_positives: number;
    };
  };
}

export interface ModelComparisonData {
  train: SplitMetrics;
  validation: SplitMetrics;
  test: SplitMetrics;
}

export interface ObservedBenchmarkValues {
  dataset_name: string;
  total_evaluated_transactions: number;
  total_evaluated_accounts: number;
  total_transaction_volume_inr: number;
  total_ring_fraud_transactions: number;
  total_ring_fraud_accounts: number;
  total_ring_fraud_exposure_inr: number;
  mean_ring_transaction_amount_inr: number;
  mean_legitimate_transaction_amount_inr: number;
  synthetic_held_out_false_positive_rate: number;
  synthetic_held_out_false_positives_count: number;
}

export interface OperationalModelingAssumptions {
  interception_rate: number;
  cost_per_investigation_inr: number;
  friction_cost_per_false_positive_inr: number;
  tier2_analyst_hourly_rate_inr: number;
  investigation_time_minutes_per_case: number;
}

export interface DerivedEconomicEstimates {
  estimated_fraud_loss_avoided_inr: number;
  total_investigation_cost_inr: number;
  total_friction_cost_inr: number;
  net_value_saved_inr: number;
  roi_multiple: number;
}

export interface BusinessEconomicsResponse {
  observed_benchmark_values: ObservedBenchmarkValues;
  operational_modeling_assumptions: OperationalModelingAssumptions;
  derived_economic_estimates: DerivedEconomicEstimates;
  disclaimers: string[];
}

export interface EconomicsParams {
  interception_rate?: number;
  cost_per_investigation?: number;
  friction_cost_per_fp?: number;
}

export interface ChallengeMetricSet {
  pr_auc: number;
  roc_auc: number;
  precision: number;
  recall: number;
  f1: number;
  false_positive_rate: number;
  threshold: number;
  confusion_matrix: {
    true_negatives: number;
    false_positives: number;
    false_negatives: number;
    true_positives: number;
  };
  support: {
    total: number;
    positive_count: number;
    negative_count: number;
    positive_rate: number;
  };
}

export interface ChallengeMetricDeltas {
  pr_auc_delta: number;
  roc_auc_delta: number;
  precision_delta: number;
  recall_delta: number;
  f1_delta: number;
  fpr_delta: number;
  fp_delta: number;
  tp_delta: number;
}

export interface ChallengeCategorySlice {
  challenge_category: string;
  category_name: string;
  description: string;
  total_transactions: number;
  num_legitimate: number;
  num_ring: number;
  threshold: number;
  model_a: {
    fp_count: number;
    fpr: number;
    tp_count: number;
    mean_probability: number;
  };
  model_b: {
    fp_count: number;
    fpr: number;
    tp_count: number;
    mean_probability: number;
  };
  deltas: {
    fp_delta: number;
    fpr_delta: number;
    mean_prob_delta: number;
  };
}

export interface ThresholdSweepStep {
  threshold: number;
  model_a: {
    precision: number;
    recall: number;
    f1: number;
    fpr: number;
    fp_count: number;
    tp_count: number;
  };
  model_b: {
    precision: number;
    recall: number;
    f1: number;
    fpr: number;
    fp_count: number;
    tp_count: number;
  };
  deltas: {
    precision_delta: number;
    recall_delta: number;
    f1_delta: number;
    fpr_delta: number;
    fp_delta: number;
  };
}

export interface ChallengeEvaluationResponse {
  status: string;
  message?: string;
  dataset_summary?: {
    name: string;
    seed: number;
    total_transactions: number;
    legitimate_hard_negatives: number;
    ring_fraud_controls: number;
    category_count: number;
  };
  overall_metrics_t_0_70?: {
    model_a: ChallengeMetricSet;
    model_b: ChallengeMetricSet;
    deltas: ChallengeMetricDeltas;
  };
  overall_metrics_t_0_50?: {
    model_a: ChallengeMetricSet;
    model_b: ChallengeMetricSet;
    deltas: ChallengeMetricDeltas;
  };
  category_slices?: ChallengeCategorySlice[];
  threshold_sweep?: ThresholdSweepStep[];
  disclaimer?: string;
}

// ==========================================
// STAGE 14: CALIBRATION TYPES
// ==========================================

export interface ReliabilityBin {
  bin_index: number;
  bin_lower: number;
  bin_upper: number;
  bin_midpoint: number;
  sample_count: number;
  mean_predicted_prob: number;
  empirical_fraud_rate: number;
}

export interface CalibrationEvaluationPoint {
  brier_score: number;
  ece: number;
  reliability_curve: ReliabilityBin[];
}

export interface ModelCalibrationDetails {
  selected_calibrator: string;
  selection_reason: string;
  val_calib: {
    raw: CalibrationEvaluationPoint;
    platt: CalibrationEvaluationPoint;
    isotonic: CalibrationEvaluationPoint;
  };
  held_out_test: {
    raw: CalibrationEvaluationPoint;
    selected_calibrated: {
      method: string;
      brier_score: number;
      ece: number;
      reliability_curve: ReliabilityBin[];
    };
  };
}

export interface CalibrationResponse {
  status: string;
  message?: string;
  metadata?: {
    stage: number;
    title: string;
    val_calib_sample_count: number;
    val_calib_positive_count: number;
    val_calib_negative_count: number;
    held_out_test_sample_count: number;
    held_out_test_positive_count: number;
    held_out_test_negative_count: number;
    selection_algorithm: string;
  };
  model_a?: ModelCalibrationDetails;
  model_b?: ModelCalibrationDetails;
}

// ==========================================
// STAGE 14: THRESHOLD OPTIMIZATION TYPES
// ==========================================

export interface PolicyScenario {
  scenario_name: string;
  threshold: number | null;
  status: "FEASIBLE" | "INFEASIBLE_ON_VALIDATION";
  primary_metric: string;
  primary_value: number;
  description: string;
  is_recommended?: boolean;
}

export interface SensitivityTier {
  interception_tier_label: string;
  interception_rate: number;
  optimal_threshold: number;
  is_stable_with_baseline: boolean;
  modeled_loss_avoided: number;
  modeled_friction_cost: number;
  modeled_investigation_cost: number;
  modeled_net_value_saved: number;
}

export interface PolicyEvaluationTestResult {
  policy_name: string;
  status: string;
  threshold_applied: number | null;
  metrics?: {
    precision: number;
    recall: number;
    f1: number;
    false_positive_rate: number;
    confusion_matrix: {
      true_negatives: number;
      false_positives: number;
      false_negatives: number;
      true_positives: number;
    };
  };
  modeled_economics?: {
    interception_rate_assumed: number;
    tp_count?: number;
    fp_count?: number;
    flagged_case_count?: number;
    tp_exposure_amount: number;
    modeled_loss_avoided: number;
    modeled_friction_cost: number;
    modeled_investigation_cost: number;
    modeled_net_value_saved: number;
  };
  is_recommended?: boolean;
}

export interface ThresholdOptimizationResponse {
  status: string;
  message?: string;
  metadata?: {
    stage: number;
    title: string;
    model_evaluated: string;
    validation_partition: string;
    test_partition: string;
    modeling_assumptions: {
      default_interception_rate: number;
      fp_friction_cost_inr: number;
      investigation_case_cost_inr: number;
      exposure_formula: string;
      disclosure: string;
    };
  };
  validation_derived_policies?: Record<string, PolicyScenario>;
  economic_sensitivity_analysis?: SensitivityTier[];
  held_out_test_sensitivity_analysis?: SensitivityTier[];
  held_out_test_evaluation?: Record<string, PolicyEvaluationTestResult>;
  standard_threshold_benchmarks?: {
    threshold_0_70_production_baseline: {
      threshold: number;
      metrics: any;
      modeled_economics: any;
    };
    threshold_0_50_default: {
      threshold: number;
      metrics: any;
      modeled_economics: any;
    };
  };
}

// ==========================================
// STAGE 14: COLD-START TYPES
// ==========================================

export interface RuleAuditItem {
  rule_id: string;
  rule_name: string;
  description: string;
  sample_count: number;
  positive_count: number;
  negative_count: number;
  status: string;
  sufficiency: "SUFFICIENT" | "INSUFFICIENT";
}

export interface ColdStartSliceDetail {
  sample_count: number;
  positive_count: number;
  negative_count: number;
  threshold: number;
  model_a: any;
  model_b: any;
  deltas: any;
}

export interface ColdStartResponse {
  status: string;
  message?: string;
  metadata?: {
    stage: number;
    title: string;
    evaluation_rule: string;
    advisory_policy: string;
  };
  rule_sufficiency_audit?: RuleAuditItem[];
  full_dataset_evaluation?: {
    total_samples: number;
    confidence_distribution: {
      UNAVAILABLE: number;
      LIMITED: number;
      VERIFIED: number;
    };
    slices: Record<string, ColdStartSliceDetail>;
  };
  held_out_test_evaluation?: {
    total_samples: number;
    confidence_distribution: {
      UNAVAILABLE: number;
      LIMITED: number;
      VERIFIED: number;
    };
    slices: Record<string, ColdStartSliceDetail>;
  };
}


