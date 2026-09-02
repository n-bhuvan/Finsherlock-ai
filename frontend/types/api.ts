/**
 * API Types for RingGuard AI.
 */

export interface HealthResponse {
  status: string;
  service: string;
}

export type ConnectionState = "checking" | "connected" | "not_connected";

export interface BackendStatus {
  state: ConnectionState;
  data: HealthResponse | null;
  error: string | null;
  latencyMs: number | null;
  lastChecked: Date | null;
}
