/**
 * RingGuard AI — Timeline Engine Type Definitions.
 *
 * Strictly matches Stage 9 Pydantic schemas in backend/app/timeline/schemas.py.
 */

export type TimelineEventType =
  | "ACCOUNT_CREATED"
  | "TRANSACTION"
  | "LARGE_INCOMING_TRANSACTION"
  | "RAPID_TRANSFER"
  | "CONNECTED_ACCOUNT_ACTIVITY";

export type TimelineSeverity = "HIGH" | "MEDIUM" | "LOW" | "INFO";

export interface TimelineEvent {
  event_id: string;
  event_type: TimelineEventType;
  timestamp: string;
  timestamp_source: string;
  title: string;
  description: string;
  related_entities: string[];
  supporting_record_ids: string[];
  source: string;
  severity: TimelineSeverity;
}

export interface TimelineResponse {
  target_id: string;
  target_type: "transaction" | "account";
  timestamp_context: string | null;
  total_events: number;
  events: TimelineEvent[];
  risk_context?: Record<string, unknown> | null;
  disclaimer: string;
}
