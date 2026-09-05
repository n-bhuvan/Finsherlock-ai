// RingGuard AI V2 Stage 15: Systemic Risk Anomaly Detection Types

export type AnomalyScope = "ACCOUNT" | "MERCHANT" | "RING_NETWORK" | "SYSTEMIC_INFRASTRUCTURE";

export type SignalStatus = "AVAILABLE" | "UNAVAILABLE" | "NOT_APPLICABLE";

export interface AnomalySignal {
  name: string;
  status: SignalStatus;
  value?: string | number | boolean | null;
  threshold?: string | number | null;
  is_anomalous: boolean;
  description: string;
  source_field?: string | null;
}

export interface ScopeAnomalyResult {
  scope: AnomalyScope;
  anomaly_detected: boolean;
  anomaly_score: number;
  status: "ANOMALOUS" | "NORMAL" | "INCONCLUSIVE" | "NOT_APPLICABLE" | string;
  confidence: "HIGH" | "MEDIUM" | "LOW" | "UNAVAILABLE" | string;
  reason: string;
  signals: AnomalySignal[];
  evidence_ids: string[];
  requires_verification: boolean;
}

export interface SystemicAnomalyResponse {
  transaction_id: string;
  account_id: string;
  timestamp: string;
  systemic_anomaly_score: number;
  overall_systemic_risk_score: number;
  score_interpretation: string;
  anomaly_detected: boolean;
  primary_contributing_scope: AnomalyScope | null;
  scopes: {
    account: ScopeAnomalyResult;
    merchant: ScopeAnomalyResult;
    ring_network: ScopeAnomalyResult;
    systemic_infrastructure: ScopeAnomalyResult;
  };
  all_evidence_ids: string[];
  requires_verification: boolean;
  human_approval_required: boolean;
  defense_only_disclaimer: string;
}
