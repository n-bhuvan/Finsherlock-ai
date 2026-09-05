/**
 * RingGuard AI — Stage 20: Monitoring & Outcome Verification Types
 */

export type DriftStatus = "NORMAL" | "WATCH" | "SIGNIFICANT_DRIFT" | "UNAVAILABLE";

export type OutcomeStatus =
  | "OUTCOME_CONFIRMED"
  | "OUTCOME_UNAVAILABLE"
  | "OUTCOME_PENDING"
  | "OUTCOME_INCONCLUSIVE";

export interface DriftMetric {
  feature_name: string;
  metric_name: string;
  metric_value: number;
  threshold_watch: number;
  threshold_significant: number;
  status: DriftStatus;
  reference_window: string;
  comparison_window: string;
  sample_size_reference: number;
  sample_size_comparison: number;
  limitations?: string | null;
}

export interface OutcomePerformanceMetric {
  window_name: string;
  sample_size: number;
  positive_label_rate: number;
  precision?: number | null;
  recall?: number | null;
  false_positive_rate?: number | null;
  false_negative_rate?: number | null;
  brier_score?: number | null;
  status: OutcomeStatus;
}

export interface DriftMonitoringResponse {
  evaluation_timestamp: string;
  reference_window: string;
  comparison_window: string;
  overall_status: DriftStatus;
  metrics: DriftMetric[];
  significant_features: string[];
  watch_features: string[];
  performance_comparison?: Record<string, OutcomePerformanceMetric> | null;
  human_review_required: boolean;
  disclaimer: string;
}

export interface OutcomeVerificationResponse {
  transaction_id: string;
  evaluation_context: string;
  prediction_at_decision?: number | null;
  policy_action_at_decision?: string | null;
  observed_outcome?: string | null;
  outcome_status: OutcomeStatus;
  outcome_match?: boolean | null;
  verification_timestamp: string;
  verification_source: string;
  limitations: string;
  human_review_required: boolean;
  disclaimer: string;
}

export interface MonitoringSummaryResponse {
  overall_drift_status: DriftStatus;
  total_features_monitored: number;
  significant_features_count: number;
  watch_features_count: number;
  reference_window: string;
  comparison_window: string;
  outcome_verification_coverage_rate: number;
  human_review_required: boolean;
  disclaimer: string;
}
