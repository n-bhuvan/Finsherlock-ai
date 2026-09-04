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
