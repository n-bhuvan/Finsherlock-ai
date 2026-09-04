/**
 * RingGuard AI — Evidence Engine Type Definitions.
 *
 * Strictly matches Stage 9 Pydantic schemas in backend/app/evidence/schemas.py.
 */

export type EvidenceType =
  | "SHARED_DEVICE"
  | "SHARED_IP"
  | "COMMON_BENEFICIARY"
  | "RELATED_ACCOUNT"
  | "MULTI_HOP_CONNECTION"
  | "RAPID_FUND_FLOW"
  | "TRANSACTION_ACTIVITY"
  | "LARGE_INCOMING_TRANSACTION"
  | "ACCOUNT_AGE_CONTEXT"
  | "COORDINATED_TIMING"
  | "NETWORK_CONTEXT"
  | "MODEL_RISK_CONTEXT";

export type EvidenceSeverity = "HIGH" | "MEDIUM" | "LOW" | "INFO";

export interface EvidenceItem {
  evidence_id: string;
  evidence_type: EvidenceType;
  severity: EvidenceSeverity;
  title: string;
  description: string;
  related_entities: string[];
  supporting_transaction_ids: string[];
  timestamp_range: { [key: string]: string } | null;
  timestamp_source: string;
  source: string;
  status: string;
  relevant_values: Record<string, unknown>;
  rank: number;
}

export interface EvidenceListResponse {
  target_id: string;
  target_type: "transaction" | "account";
  timestamp_context: string | null;
  total_evidence_items: number;
  items: EvidenceItem[];
  disclaimer: string;
}
