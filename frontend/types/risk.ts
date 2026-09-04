/**
 * RingGuard AI — Risk API Type Definitions.
 *
 * Strictly matches Stage 8 Pydantic schemas in backend/app/schemas/risk.py.
 */

export type RiskBand = "LOW" | "MEDIUM" | "HIGH";

export interface ModelHealthDetail {
  model_name: string;
  model_version: string;
  loaded: boolean;
  feature_count: number;
  graph_features_count: number;
}

export interface RiskHealthResponse {
  status: string;
  service: string;
  baseline_model_loaded: boolean;
  graph_model_loaded: boolean;
  database_connected: boolean;
  models: {
    baseline?: ModelHealthDetail;
    graph?: ModelHealthDetail;
    [key: string]: ModelHealthDetail | undefined;
  };
}

export interface BaseRiskAssessmentResponse {
  transaction_id: string;
  prediction_unit: string;
  model: string;
  model_version: string;
  predicted_ring_probability: number;
  decision_threshold: number;
  risk_band: RiskBand;
  feature_count: number;
  graph_features_count: number;
  graph_context_available: boolean;
  disclaimer: string;
}

export interface BaselineRiskResponse extends BaseRiskAssessmentResponse {
  model: "ringguard_baseline_xgb_v1";
  model_version: "v1";
  feature_count: 37;
  graph_features_count: 0;
  graph_context_available: false;
}

export interface NetworkRiskResponse extends BaseRiskAssessmentResponse {
  model: "ringguard_graph_xgb_v1";
  model_version: "v1";
  feature_count: 58;
  graph_features_count: 21;
  graph_context_available: true;
}

export type RiskResponse = NetworkRiskResponse;

export interface GraphAttributionItem {
  feature_name: string;
  feature_group: string;
  importance_rank_in_model_b: number;
  original_value: number;
  isolated_value: number;
  corroborating_evidence_id?: string | null;
  corroborating_evidence_type?: string | null;
  provenance_status: "VERIFIED" | "FEATURE_ONLY";
}

export interface FeatureIsolationResponse {
  transaction_id: string;
  original_probability: number;
  isolated_probability: number;
  delta: number;
  percentage_point_delta: number;
  risk_band_original: RiskBand;
  risk_band_isolated: RiskBand;
  isolated_features_count: number;
  isolated_features: string[];
  baseline_values_used: Record<string, number>;
  attributions: GraphAttributionItem[];
  methodology: string;
  limitations: string[];
  disclaimer: string;
}

