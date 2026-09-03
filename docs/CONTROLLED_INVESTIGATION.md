# RingGuard AI — Stage 10: Controlled Investigation Tools

## 1. Overview & Architecture

Stage 10 builds the **Controlled Investigation Tool Layer** of RingGuard AI. It provides a future investigation workflow or human fraud analyst with a deterministic, bounded, strictly read-only suite of investigation tools.

The tools retrieve and connect factual information from:
1. **PostgreSQL Relational Database** (operational tables: `transactions`, `accounts`, `customers`, `devices`, `ips`, `beneficiaries`, `merchants`).
2. **Stage 4 NetworkX Entity Graph** (relational topology and multi-hop connectivity).
3. **Stage 8 Risk APIs & Model Services** (Model A 37 features, Model B 58 features, risk probability, threshold 0.50).
4. **Stage 9 Evidence Engine** (verified evidence extraction, point-in-time enforcement, evidence provenance).
5. **Stage 9 Timeline Engine** (chronological transaction/account timeline reconstruction with separated `risk_context`).

```
┌────────────────────────────────────────────────────────────────────────┐
│               STAGE 10: CONTROLLED INVESTIGATION TOOLS                 │
├────────────────────────────────────────────────────────────────────────┤
│  get_account()              find_shared_devices()      trace_fund_flow() │
│  get_transactions()         find_shared_ips()          reconstruct_timeline() │
│  find_related_accounts()    find_common_beneficiaries() get_risk_features() │
└───────────────────▲────────────────────────────────────▲───────────────┘
                    │                                    │
    ┌───────────────┴───────────────┐    ┌───────────────┴───────────────┐
    │       Stage 9 Engine Layer    │    │      Stage 8 Model Layer      │
    │  - EvidenceEngine (t <= T)    │    │  - FeatureService (37 & 58)   │
    │  - TimelineEngine (no fake ev)│    │  - ModelService (XGBoost v1)  │
    └───────────────▲───────────────┘    └───────────────────────────────┘
                    │
    ┌───────────────┴────────────────────────────────────────────────────┐
    │     PostgreSQL Relational DB (Read-Only) & NetworkX Graph Engine   │
    └────────────────────────────────────────────────────────────────────┘
```

---

## 2. Strict Safety & Defense-Only Boundaries

1. **Strictly Read-Only:** All queries use parameterized SQLAlchemy statements. Zero mutations (`INSERT`, `UPDATE`, `DELETE`) and zero session commits occur.
2. **Zero Automated Enforcement:** Investigation tools do not block accounts, stop payments, modify risk tiers, or alter database flags.
3. **No LLM / No Autonomous Agent:** The tool layer contains zero generative models, prompt orchestration, chatbots, RAG pipelines, or vector databases.
4. **Point-in-Time Safety:** Every tool accepting an `as_of` timestamp enforces $t \le \text{as\_of}$. Future events and relationships formed after `as_of` are strictly excluded.
5. **Non-Fabrication of Evidence IDs:** Evidence IDs in tool results are never generated via naming conventions or template formatting. They are obtained exclusively from the Stage 9 `EvidenceEngine`. When no corresponding Stage 9 evidence exists, `evidence_ids = []`.
6. **No Scenario/Ground-Truth Leakage:** Synthetic ground-truth metadata (`scenario_type`, `scenario_id`, `ground_truth_label`) is strictly excluded from all schemas and responses.
7. **Legitimate Look-Alike Truthfulness:** Shared devices or IP addresses are reported factually without asserting fraud guilt.
8. **Fund Flow Guardrail:** `trace_fund_flow` only describes money movement when an underlying `Transaction` record physically supports the transfer.

---

## 3. The 9 Controlled Investigation Tools

| Tool Name | Scope / Target | Description | Source |
| :--- | :--- | :--- | :--- |
| `get_account` | `account_id` | Retrieves factual operational account metadata. Stripped of scenario metadata. | `database.accounts` |
| `get_transactions` | `account_id` | Retrieves bounded historical transactions sorted chronologically ($t \le \text{end\_time}$). | `database.transactions` |
| `find_related_accounts` | `account_id` | Discovers accounts linked via shared devices, IPs, or common beneficiaries up to `as_of`. | `database.transactions` |
| `find_shared_devices` | `account_id` | Discovers hardware endpoints co-used by this account and other accounts. | `database.devices` |
| `find_shared_ips` | `account_id` | Discovers network IPs co-used by this account and other accounts. | `database.ips` |
| `find_common_beneficiaries` | `account_id` | Discovers beneficiaries receiving funds from this account and other accounts. | `database.beneficiaries` |
| `trace_fund_flow` | `account_id` / `transaction_id` | Traces verified transaction transfers up to `max_depth` (1-3 hops). Real transactions only. | `database.transactions` |
| `reconstruct_timeline` | `account_id` / `transaction_id` | Chronological event sequence delegating to Stage 9 `TimelineEngine`. Zero fake events. | `stage9.timeline_engine` |
| `get_risk_features` | `transaction_id` | Retrieves 37 or 58 features, probability, and risk band from Stage 8 `ModelService`. | `stage8.model_service` |

---

## 4. Standardized Response Contract

Every tool execution returns a standardized `ToolExecutionResult` envelope:

```json
{
  "tool_name": "find_shared_devices",
  "status": "SUCCESS",
  "target": "ACC_000001",
  "as_of": "2026-01-26T18:11:07+05:30",
  "result": [
    {
      "device_id": "DEV_000001",
      "device_type": "mobile",
      "device_os": "iOS",
      "co_using_accounts": ["ACC_000002", "ACC_000003"],
      "supporting_transaction_ids": ["TXN_00000646", "TXN_00000679"]
    }
  ],
  "result_count": 1,
  "source": "database.devices",
  "evidence_ids": [
    "EVD_DEV_ACC_000001_DEV_000001_TXN_00000646"
  ],
  "limitations": "Filtered strictly to transactions occurring at t <= as_of.",
  "error_details": null,
  "disclaimer": "Controlled read-only investigation tool output. Analytical facts only. Does not constitute an automated fraud determination or enforcement decision."
}
```

---

## 5. API Endpoints

Mounted on `api_router` under prefix `/api/investigation`:

- `GET /api/investigation/account/{account_id}`
- `GET /api/investigation/account/{account_id}/transactions`
- `GET /api/investigation/account/{account_id}/related`
- `GET /api/investigation/account/{account_id}/devices`
- `GET /api/investigation/account/{account_id}/ips`
- `GET /api/investigation/account/{account_id}/beneficiaries`
- `GET /api/investigation/account/{account_id}/fund-flow`
- `GET /api/investigation/account/{account_id}/timeline`
- `GET /api/investigation/transaction/{transaction_id}/fund-flow`
- `GET /api/investigation/transaction/{transaction_id}/timeline`
- `GET /api/investigation/transaction/{transaction_id}/risk-features`

---

## 6. Verification & Test Metrics

- **Stage 10 Test Suite:** 31 tests passed in `backend/tests/test_investigation_tools.py`.
- **Full Backend Regression:** 110 tests passed in `backend/tests/`.
- **Full ML Regression:** 62 tests passed in `ml/tests/`.
- **Total Test Suite:** 172 passed, 0 failed.
- **Latency Benchmarks:**
  - Minimum: 30.27 ms
  - Average: 55.27 ms
  - Maximum: 195.11 ms
- **Read-Only Invariant:** 0 mutations across all operational tables.
- **Model Artifact Bitwise Integrity:**
  - `ringguard_baseline_xgb_v1.joblib`: 263,745 bytes (exact match)
  - `ringguard_graph_xgb_v1.joblib`: 266,061 bytes (exact match)
