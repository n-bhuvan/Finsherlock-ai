# RingGuard AI — Risk API Specification

> **Stage 8: FastAPI Risk APIs**  
> *Controlled, Read-Only Analytical Risk Scoring Service for Payment Ring Detection*

---

## 1. Objective & Architectural Scope

Stage 8 provides the HTTP backend interface for RingGuard AI. It exposes the trained Machine Learning models—**Model A** (Stage 6 Baseline) and **Model B** (Stage 7 Graph-Enhanced)—through strictly validated, read-only REST endpoints.

> [!IMPORTANT]
> **Mandatory Analytical Boundary:**  
> *"Stage 8 exposes the existing RingGuard ML models through a controlled, read-only FastAPI risk service. It does not perform payment approval, rejection, blocking, or other autonomous enforcement."*

The service transforms incoming transaction lookups into structured, verifiable risk probabilities while maintaining absolute isolation from automated payment intervention.

---

## 2. Model Inventory & Feature Contracts

The API exposes two trained, audited models:

| Model | ID | Features | Feature Breakdown | Graph Features | Purpose |
|---|---|---|---|---|---|
| **Model A** | `ringguard_baseline_xgb_v1` | **37** | 15 Transaction + 22 Behavioral | 0 | Baseline control (non-network) |
| **Model B** | `ringguard_graph_xgb_v1` | **58** | 15 Transaction + 22 Behavioral + 21 Graph | 21 | Primary network-aware model |

- **Prediction Unit:** Always `transaction` (each prediction corresponds to exactly one payment instant).
- **Target Variable:** Ring / suspicious syndicate collusion probability in $[0.0, 1.0]$.
- **Baseline Threshold:** Fixed baseline threshold = $0.5$ (uncalibrated).

---

## 3. API Endpoints

All risk endpoints are mounted under `/api/risk/`. The root application health endpoint (`GET /health`) remains completely separate and intact.

### 1. `GET /api/risk/health`
- **Description:** Reports the operational status of the risk service, ML artifact loading, feature counts, and PostgreSQL database connectivity.
- **Response Schema:** `RiskHealthResponse`
- **Example Response:**
  ```json
  {
    "status": "ok",
    "service": "ringguard-risk-engine",
    "baseline_model_loaded": true,
    "graph_model_loaded": true,
    "database_connected": true,
    "models": {
      "baseline": {
        "model_name": "ringguard_baseline_xgb_v1",
        "model_version": "v1",
        "loaded": true,
        "feature_count": 37,
        "graph_features_count": 0
      },
      "graph": {
        "model_name": "ringguard_graph_xgb_v1",
        "model_version": "v1",
        "loaded": true,
        "feature_count": 58,
        "graph_features_count": 21
      }
    }
  }
  ```

---

### 2. `GET /api/risk/transaction/{transaction_id}`
- **Description:** Primary risk assessment endpoint. Evaluates the transaction using the primary network-aware model (Model B).
- **Path Parameter:** `transaction_id` (string, e.g. `TXN_00000646`)
- **Response Schema:** `RiskResponse`
- **Example Response:**
  ```json
  {
    "transaction_id": "TXN_00000646",
    "prediction_unit": "transaction",
    "model": "ringguard_graph_xgb_v1",
    "model_version": "v1",
    "predicted_ring_probability": 0.000300,
    "decision_threshold": 0.5,
    "risk_band": "LOW",
    "feature_count": 58,
    "graph_features_count": 21,
    "graph_context_available": true,
    "disclaimer": "Analytical risk assessment output only. Does not constitute an automated payment action or enforcement decision."
  }
  ```

---

### 3. `GET /api/risk/transaction/{transaction_id}/baseline`
- **Description:** Evaluates the transaction using baseline Model A (Transaction + Behavior only, 37 features, 0 graph features).
- **Path Parameter:** `transaction_id` (string)
- **Response Schema:** `BaselineRiskResponse`
- **Example Response:**
  ```json
  {
    "transaction_id": "TXN_00000646",
    "prediction_unit": "transaction",
    "model": "ringguard_baseline_xgb_v1",
    "model_version": "v1",
    "predicted_ring_probability": 0.000299,
    "decision_threshold": 0.5,
    "risk_band": "LOW",
    "feature_count": 37,
    "graph_features_count": 0,
    "graph_context_available": false,
    "disclaimer": "Analytical risk assessment output only. Does not constitute an automated payment action or enforcement decision."
  }
  ```

---

### 4. `GET /api/risk/transaction/{transaction_id}/network`
- **Description:** Evaluates the transaction using network Model B (Transaction + Behavior + Point-in-Time Graph, 58 features).
- **Path Parameter:** `transaction_id` (string)
- **Response Schema:** `NetworkRiskResponse`
- **Example Response:**
  ```json
  {
    "transaction_id": "TXN_00000646",
    "prediction_unit": "transaction",
    "model": "ringguard_graph_xgb_v1",
    "model_version": "v1",
    "predicted_ring_probability": 0.000300,
    "decision_threshold": 0.5,
    "risk_band": "LOW",
    "feature_count": 58,
    "graph_features_count": 21,
    "graph_context_available": true,
    "disclaimer": "Analytical risk assessment output only. Does not constitute an automated payment action or enforcement decision."
  }
  ```

---

## 4. Deterministic Risk Presentation Bands

Risk bands provide an exploratory visual classification for human risk operators:
- **`LOW`**: $\text{Probability} < 0.20$
- **`MEDIUM`**: $0.20 \le \text{Probability} < 0.50$
- **`HIGH`**: $\text{Probability} \ge 0.50$ (At or above baseline decision threshold)

> [!NOTE]
> Risk bands are exploratory presentation categories. Threshold optimization and calibrated decision boundaries are deferred to a dedicated calibration stage.

---

## 5. Point-in-Time Feature Semantics & Safety

To prevent future network information or retrospective statistics from contaminating predictions:
- Behavioral history features strictly observe $t < T$.
- Graph topological state strictly observes $t \le T$.
- `FeatureService` verifies transaction existence in PostgreSQL, then retrieves the point-in-time feature vector verified in Stage 5, ensuring $0.0000$ drift from the trained models.

---

## 6. Read-Only Safety Guarantees

The risk API is strictly read-only:
- **Zero Database Mutations:** Requests do not perform SQL `INSERT`, `UPDATE`, or `DELETE`.
- **Zero Enforcement Actions:** The API cannot approve, deny, freeze, block, or reverse funds.
- **Zero Side Effects:** State remains invariant before and after request handling.

---

## 7. Error Handling & Security

- **404 Not Found:** Returned when `transaction_id` does not exist in PostgreSQL.
- **422 Unprocessable Entity:** Returned when input parameters fail Pydantic validation (e.g. whitespace-only IDs).
- **Information Redaction:** Database credentials (`DATABASE_URL`), system secrets, and raw internal tracebacks are never exposed to clients.
