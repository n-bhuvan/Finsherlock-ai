/**
 * RingGuard AI — Stage 16: LLM Forensic Explanation & Security Types.
 *
 * Strictly matches backend/app/llm/schemas.py.
 */

export type ClaimType = "FACT" | "INTERPRETATION" | "LIMITATION";

export interface GroundedClaim {
  claim_id: string;
  statement: string;
  evidence_ids: string[];
  claim_type: ClaimType;
  is_grounded: boolean;
  validation_notes?: string | null;
}

export interface GroundedEvidenceItem {
  evidence_id: string;
  evidence_type: string;
  claim_statement: string;
  is_grounded: boolean;
  grounding_source: string;
}

export interface GroundedHypothesisItem {
  hypothesis_id: string;
  title: string;
  rationale: string;
  triggering_evidence_id: string;
  is_grounded: boolean;
}

export interface GroundingValidationReport {
  total_claims: number;
  total_fact_claims: number;
  grounded_fact_claims: number;
  unsupported_claims_rejected: number;
  grounding_ratio: number;
  is_fully_grounded: boolean;
  rejection_reasons: string[];
}

export interface ExplanationMetadata {
  provider: string;
  model: string;
  prompt_version: string;
  temperature: number;
  latency_ms: number;
  is_fallback: boolean;
  fallback_reason?: string | null;
  prompt_sha256: string;
  response_sha256: string;
}

export interface LLMExplanationResponse {
  transaction_id: string;
  account_id: string;
  executive_summary: string;
  risk_assessment_narrative: string;
  model_a_probability: number;
  model_b_probability: number;
  calibrated_risk: number;
  risk_band: string;
  graph_confidence: string;
  structured_claims: GroundedClaim[];
  evidence_summaries: GroundedEvidenceItem[];
  topological_ring_interpretation: string;
  benign_alternative_hypotheses: GroundedHypothesisItem[];
  recommended_human_verification_questions: string[];
  uncertainty_and_limitations: string;
  grounding_validation: GroundingValidationReport;
  metadata: ExplanationMetadata;
  audit_id: string;
  human_approval_required: boolean;
  disclaimer: string;
}

export interface ExplanationAuditRecord {
  previous_record_hash: string;
  record_hash: string;
  audit_id: string;
  timestamp: string;
  transaction_id: string;
  account_id: string;
  provider: string;
  model_name: string;
  prompt_version: string;
  prompt_sha256: string;
  response_sha256: string;
  latency_ms: number;
  status: string;
  grounding_ratio: number;
  is_fallback: boolean;
  fallback_reason?: string | null;
  security_status: string;
  human_approval_required: boolean;
}

export interface ExplanationAuditResponse {
  status: string;
  total_records_in_log: number;
  chain_integrity_valid: boolean;
  chain_verification_error?: string | null;
  returned_count: number;
  records: ExplanationAuditRecord[];
  disclaimer: string;
}

export interface SecurityControlItem {
  name: string;
  status: string;
  description: string;
}

export interface SecurityStatusResponse {
  status: string;
  stage: number;
  controls: SecurityControlItem[];
  disclaimer: string;
}

export type FeedbackCategory =
  | "EXPLANATION_USEFUL"
  | "INSUFFICIENT_EVIDENCE"
  | "MISLEADING_EXPLANATION"
  | "OUTCOME_CONFIRMED"
  | "OUTCOME_CONTRADICTED";

export interface AnalystFeedbackRequest {
  transaction_id: string;
  category: FeedbackCategory;
  analyst_id: string;
  notes: string;
  rating: number;
}

export interface AnalystFeedbackResponse {
  feedback_id: string;
  transaction_id: string;
  category: FeedbackCategory;
  analyst_id: string;
  notes: string;
  rating: number;
  timestamp: string;
  status: string;
  human_review_required: boolean;
  audit_record_hash: string;
  disclaimer: string;
}

export interface FeedbackSummaryResponse {
  status: string;
  summary: {
    total_feedback_count: number;
    category_distribution: Record<string, number>;
    average_rating: number;
    recent_feedback: AnalystFeedbackResponse[];
  };
  disclaimer: string;
}
