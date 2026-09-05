/**
 * RingGuard AI — Deterministic Risk Policy Engine & Next-Best-Action TypeScript Contracts.
 *
 * Stage 19: Deterministic Risk Policy Engine + Next-Best-Action.
 * Defines typed models for human decision-support, policy rules, and auditability.
 */

export type PolicyAction =
  | "ALLOW"
  | "MONITOR"
  | "REQUEST_VERIFICATION"
  | "HOLD_FOR_REVIEW"
  | "ESCALATE"
  | "FALLBACK_REVIEW";

export type ActionPriority =
  | "CRITICAL"
  | "HIGH"
  | "MEDIUM_HIGH"
  | "MEDIUM"
  | "LOW_MEDIUM"
  | "LOW";

export type HumanReviewRole =
  | "SENIOR_RISK_ANALYST"
  | "RISK_ANALYST"
  | "FRAUD_INVESTIGATOR"
  | "AUTOMATED_TELEMETRY_ANALYST"
  | "NONE";

export interface PolicyRuleDefinition {
  rule_id: string;
  precedence: number;
  recommended_action: PolicyAction;
  title: string;
  condition_description: string;
  rationale_template: string;
  required_human_role: HumanReviewRole;
  action_priority: ActionPriority;
}

export interface PolicyDecision {
  transaction_id: string;
  account_id: string;
  timestamp: string;

  // Core Decision Signals
  calibrated_risk_score: number;
  expected_value: number;
  priority_score: number;
  systemic_anomaly_score: number;
  investigative_uncertainty: number;
  evidence_domains: string[];
  evidence_count: number;
  corroborated_structural_domains: number;
  has_conflicting_evidence: boolean;

  // Next-Best-Action Recommendation
  recommended_action: PolicyAction;
  action_priority: ActionPriority;
  policy_rule_id: string;
  policy_version: string;
  policy_reason: string;
  required_human_role: HumanReviewRole;
  required_verification: string;

  // Contextual Evidence and Auditability
  supporting_evidence_ids: string[];
  blocking_conditions: string[];
  confidence: number;

  // Absolute Safety & Governance Boundaries
  human_approval_required: boolean;
  execution_status: string;
  autonomous_action_taken: boolean;
  disclaimer: string;

  // Stage 18 Counterfactual Context
  counterfactual_context?: {
    strongest_driver?: string;
    driver_contribution?: number;
    driver_direction?: string;
    largest_reduction_delta?: number;
  } | null;
}

export interface PolicyRulesCatalogResponse {
  policy_version: string;
  rule_count: number;
  precedence_order: string[];
  rules: PolicyRuleDefinition[];
}
