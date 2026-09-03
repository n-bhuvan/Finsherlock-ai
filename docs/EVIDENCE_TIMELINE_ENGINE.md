# RingGuard AI — Evidence & Timeline Engine Specification

> **Stage 9: Evidence + Timeline Engine**  
> *Deterministic, Verifiable Investigation Layer for Coordinated Payment-Abuse Detection*

---

## 1. Executive Summary & Architectural Scope

Stage 9 establishes the investigation layer of RingGuard AI. It bridges raw database records, NetworkX graph topology, and Stage 6/7/8 machine learning scores into:
1. **Structured, Traceable Evidence Objects (`EvidenceEngine`)**
2. **Chronological Investigation Timelines (`TimelineEngine`)**

> [!IMPORTANT]
> **Mandatory Data Integrity & Safety Guarantees:**
> - **Truth and Non-Fabrication:** The engine **never fabricates** accounts, transactions, devices, IPs, beneficiaries, timestamps, amounts, or relationships. Every evidence item and timeline event is grounded in verified PostgreSQL records.
> - **Point-in-Time Safety:** When evaluating a transaction at timestamp $T$, all historical queries strictly enforce $t \le T$ (and $t < T$ for behavioral antecedents). Relationships or transactions occurring after $T$ are strictly invisible.
> - **Historical Timeline Purity:** Derived model risk evaluations are **strictly excluded** from historical timeline events (`TimelineEventType.RISK_EVALUATION` is prohibited). Model evaluations are presented strictly as separate analytical metadata (`risk_context`).
> - **Temporal Source Attribution:** Every timeline event and evidence item contains an explicit `timestamp_source` attribute (e.g. `transactions.timestamp`, `accounts.account_created_at`) to ensure total transparency.
> - **Strict Read-Only Boundary:** The service executes zero database mutations (`INSERT`, `UPDATE`, `DELETE`), zero automated payment interventions, and zero enforcement actions.
> - **No LLM / No Autonomous Agents:** All evidence ranking, signal extraction, and event sequencing are deterministic and rule/data-grounded.

---

## 2. Evidence Engine Architecture

The `EvidenceEngine` (`backend/app/evidence/engine.py`) extracts factual observed signals directly from the database and graph:

### Evidence Signal Types (`EvidenceType`)
| Signal Type | Category | Description |
|---|---|---|
| `SHARED_DEVICE` | Factual Infrastructure | Device shared across multiple accounts up to timestamp $T$. |
| `SHARED_IP` | Factual Infrastructure | IP address shared between multiple accounts up to timestamp $T$. |
| `COMMON_BENEFICIARY` | Factual Fund Routing | Recipient receiving funds from multiple independent accounts up to $T$. |
| `RELATED_ACCOUNT` | Factual Cluster | Cluster of directly linked accounts sharing infrastructure up to $T$. |
| `MULTI_HOP_CONNECTION` | Factual Graph | Indirect 2-hop connectivity between accounts via secondary devices/infrastructure. |
| `RAPID_FUND_FLOW` | Factual Behavioral | High-velocity burst transactions occurring within 1h or 24h windows prior to $T$. |
| `LARGE_INCOMING_TRANSACTION` | Factual Financial | High-value payment spike relative to account's historical average. |
| `ACCOUNT_AGE_CONTEXT` | Factual Provenance | Account age at the time of transaction (flagging high activity on newly registered accounts). |
| `MODEL_RISK_CONTEXT` | Derived Analytical | Model B (Stage 7) probability and risk band, clearly marked as derived machine learning output, not proof of fraud. |

### Evidence Object Schema (`EvidenceItem`)
```json
{
  "evidence_id": "EVD_DEV_TXN_00000001_DEV_000001",
  "evidence_type": "SHARED_DEVICE",
  "severity": "HIGH",
  "title": "Shared Device Detected",
  "description": "Device 'DEV_000001' was used by 3 distinct accounts (ACC_000001, ACC_000002, ACC_000003) across 8 transactions up to point-in-time 2026-01-01T00:40:18+00:00.",
  "related_entities": ["ACC_000001", "DEV_000001", "ACC_000002", "ACC_000003"],
  "supporting_transaction_ids": ["TXN_00000001", "TXN_00000002", "TXN_00000003"],
  "timestamp_range": {
    "start": "2026-01-01T00:40:18+00:00",
    "end": "2026-01-01T01:15:22+00:00"
  },
  "timestamp_source": "transactions.timestamp",
  "source": "database.transactions",
  "status": "VERIFIED",
  "relevant_values": {
    "device_id": "DEV_000001",
    "shared_account_count": 3,
    "supporting_transaction_count": 8
  },
  "rank": 1
}
```

### Deterministic Evidence Ranking
Evidence items are sorted by priority to provide human analysts with immediate visibility into the strongest structural signals:
1. `RAPID_FUND_FLOW` (Base Priority: 100)
2. `MULTI_HOP_CONNECTION` (Base Priority: 90)
3. `SHARED_DEVICE` (Base Priority: 80)
4. `COMMON_BENEFICIARY` (Base Priority: 75)
5. `SHARED_IP` (Base Priority: 70)
6. `RELATED_ACCOUNT` (Base Priority: 65)
7. `LARGE_INCOMING_TRANSACTION` (Base Priority: 60)
8. `MODEL_RISK_CONTEXT` (Base Priority: 50)
9. `ACCOUNT_AGE_CONTEXT` (Base Priority: 40)
10. `TRANSACTION_ACTIVITY` (Base Priority: 30)

*Tie-breaking:* Number of supporting transactions descending, then `evidence_id` ascending.

---

## 3. Timeline Engine Architecture

The `TimelineEngine` (`backend/app/timeline/engine.py`) reconstructs chronological event sequences representing the factual history of the investigated target.

### Timeline Event Types (`TimelineEventType`)
| Event Type | Source Column | Description |
|---|---|---|
| `ACCOUNT_CREATED` | `accounts.account_created_at` | True account registration instant. |
| `TRANSACTION` | `transactions.timestamp` | Normal payment execution. |
| `LARGE_INCOMING_TRANSACTION` | `transactions.timestamp` | High-value payment transaction ($\ge \text{INR } 15,000$). |
| `RAPID_TRANSFER` | `transactions.timestamp` | Payment executed within 15 minutes of previous transaction. |
| `CONNECTED_ACCOUNT_ACTIVITY` | `transactions.timestamp` | Transaction on linked accounts sharing infrastructure within 48h prior to $T$. |

*(Note: Derived model evaluations are strictly excluded from `TimelineEvent` to preserve historical event purity).*

### Timeline Response Schema (`TimelineResponse`)
```json
{
  "target_id": "TXN_00000001",
  "target_type": "transaction",
  "timestamp_context": "2026-01-01T00:40:18+00:00",
  "total_events": 5,
  "events": [
    {
      "event_id": "EVT_ACC_CREATED_ACC_000001",
      "event_type": "ACCOUNT_CREATED",
      "timestamp": "2025-12-28T14:20:00+00:00",
      "timestamp_source": "accounts.account_created_at",
      "title": "Account 'ACC_000001' Registered",
      "description": "Account 'ACC_000001' (savings, status: active) was created under customer 'CUST_000001'.",
      "related_entities": ["ACC_000001", "CUST_000001"],
      "supporting_record_ids": ["ACC_000001"],
      "source": "accounts",
      "severity": "INFO"
    },
    {
      "event_id": "EVT_TXN_00000001",
      "event_type": "LARGE_INCOMING_TRANSACTION",
      "timestamp": "2026-01-01T00:40:18+00:00",
      "timestamp_source": "transactions.timestamp",
      "title": "High-Value Transaction: TXN_00000001",
      "description": "Transaction TXN_00000001: INR 48,000.00 via UPI (Type: transfer, Status: completed, Device: DEV_000001, IP: IP_000001).",
      "related_entities": ["ACC_000001", "DEV_000001", "IP_000001", "BEN_000001"],
      "supporting_record_ids": ["TXN_00000001"],
      "source": "transactions",
      "severity": "HIGH"
    }
  ],
  "risk_context": {
    "evaluated_at": "2026-01-01T00:40:18+00:00",
    "model_name": "ringguard_graph_xgb_v1",
    "predicted_ring_probability": 0.999544,
    "decision_threshold": 0.5,
    "risk_band": "HIGH",
    "note": "Derived Machine Learning evaluation. Kept strictly distinct from real-world timeline events."
  },
  "disclaimer": "Chronological timeline reconstruction based on verified database records up to the investigation timestamp. Derived model evaluations are isolated from historical events."
}
```

---

## 4. API Endpoints

All endpoints are mounted on the modular router:

### 1. `GET /api/evidence/transaction/{transaction_id}`
- **Description:** Extracts and deterministically ranks evidence signals for a transaction strictly up to its timestamp ($t \le T$).
- **Response Schema:** `EvidenceListResponse`

### 2. `GET /api/evidence/account/{account_id}`
- **Description:** Extracts and ranks evidence signals for an account across its historical transactions up to its latest activity.
- **Response Schema:** `EvidenceListResponse`

### 3. `GET /api/timeline/transaction/{transaction_id}`
- **Description:** Reconstructs chronological event sequence for a transaction context strictly up to its timestamp ($t \le T$).
- **Response Schema:** `TimelineResponse`

### 4. `GET /api/timeline/account/{account_id}`
- **Description:** Reconstructs chronological event sequence for an account up to its latest transaction.
- **Response Schema:** `TimelineResponse`

---

## 5. Provenance & Point-in-Time Safety Verification

1. **Monotonic Event Sorting:** Timestamps in `events` are strictly non-decreasing ($t_i \le t_{i+1}$).
2. **Point-in-Time Boundary:** For transaction $T$ at time $t_T$, any transaction or relationship created at $t > t_T$ is filtered out.
3. **Database Provenance:** Every ID in `supporting_transaction_ids`, `supporting_record_ids`, and `related_entities` is validated to exist in PostgreSQL.
4. **Read-Only Invariant:** Database transaction/account/customer row counts were verified invariant (zero mutations) across concurrent evidence and timeline requests.
