/**
 * RingGuard AI — In-Memory Session Audit Log Types.
 */

export interface SessionAuditEntry {
  id: string;
  timestamp: string;
  tool_name: string;
  target: string;
  status: string;
  result_count: number;
  source: string;
  evidence_ids: string[];
  latency_ms: number;
}
