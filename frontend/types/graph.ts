/**
 * RingGuard AI — Entity Graph Type Definitions.
 */

export type EntityNodeType =
  | "account"
  | "device"
  | "ip"
  | "beneficiary"
  | "merchant"
  | "transaction";

export interface GraphNodeData {
  id: string;
  label: string;
  type: EntityNodeType;
  sublabel?: string;
  isFocus?: boolean;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface GraphEdgeData {
  id: string;
  source: string;
  target: string;
  label?: string;
  relType?: string;
  supportingTransactions?: string[];
  [key: string]: unknown;
}
