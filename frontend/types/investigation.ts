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

