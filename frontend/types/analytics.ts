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

