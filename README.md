# RingGuard AI

> **Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation Platform**  
> *Razorpay AI Buildathon 2026 — Track 02 (AI Risk Manager)*

[![Backend Tests](https://img.shields.io/badge/backend%20tests-129%20passed-emerald.svg)](backend/tests)
[![Typecheck](https://img.shields.io/badge/typescript-zero%20errors-cyan.svg)](frontend)
[![Build](https://img.shields.io/badge/next.js%2015-production%20ready-blue.svg)](frontend)
[![Compliance](https://img.shields.io/badge/governance-defense--only-amber.svg)](#operational-safeguards--human-governance)

---

## Executive Summary

Coordinated fraud syndicates and mule networks exploit traditional payment gateways by ensuring individual transactions appear normal when viewed in isolation. By distributing illicit fund flows across dozens of accounts linked through shared hardware devices, cellular IP gateways, and common beneficiaries, bad actors bypass per-transaction velocity checks.

**RingGuard AI** solves this challenge through a **graph-native, evidence-first AI risk platform**:
1. **Graph Structural Intelligence:** Models multi-entity topology (accounts, devices, IPs, beneficiaries) using NetworkX, extracting 21 point-in-time graph features.
2. **Dual Model Evaluation:** Compares localized baseline indicators (Model A, 37 features) against network-enhanced topology (Model B, 58 features).
3. **Deterministic Evidence Engine:** Extracts verified, ranked evidence signals with exact database provenance.
4. **Deterministic Investigator Dossier:** Condenses 8 fragmented manual review queries into a unified 30-second executive brief with 1-click Markdown export.
5. **Transparent Business Economics:** Models net financial value using the Track 02 standard formula:
   $$\text{Net Value Saved} = \text{Estimated Fraud Loss Avoided} - \text{Customer Friction Cost} - \text{Investigation Cost}$$
6. **Strict Defense-Only Boundaries:** Enforces human-in-the-loop governance with zero autonomous account freezing or fund blocking.

---

## Architecture Blueprint

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 RingGuard AI Architecture                              │
└────────────────────────────────────────────────────────────────────────────────────────┘

    [ PostgreSQL Relational Core ]
    ├── Customers, Accounts, Transactions, Devices, IPs, Beneficiaries, Merchants
    │
    ├──► [ NetworkX Multi-Directed Graph Engine ]
    │    └── Point-in-time topological feature extraction (21 graph features)
    │
    ├──► [ Dual XGBoost ML Classifier Engine ]
    │    ├── Model A (Baseline): 37 transaction & behavioral features
    │    └── Model B (Network-Enhanced): 58 features (37 baseline + 21 graph features)
    │
    ├──► [ Stage 8: FastAPI Risk APIs ] (/api/risk)
    │    ├── GET /api/risk/transaction/{id} (Model B prediction)
    │    ├── GET /api/risk/transaction/{id}/baseline (Model A prediction)
    │    └── GET /api/risk/transaction/{id}/feature-isolation (In-silico sensitivity)
    │
    ├──► [ Stage 9: Evidence & Timeline Engine ] (/api/evidence, /api/timeline)
    │    ├── Deterministic evidence ranking (EVD_DEV_*, EVD_IP_*, EVD_BEN_*)
    │    └── Chronological point-in-time transaction event reconstruction
    │
    ├──► [ Stage 10: Controlled Investigation Tools ] (/api/investigation)
    │    ├── 9 read-only endpoints (find_shared_devices, find_shared_ips, trace_fund_flow)
    │    └── GET /api/investigation/transaction/{id}/dossier (Deterministic case brief)
    │
    ├──► [ Stage 12: Business Economics & Analytics ] (/api/analytics)
    │    └── GET /api/analytics/economics (Observed vs Assumed vs Derived ROI)
    │
    └──► [ Next.js 15 Dark-Mode Cyber SOC Frontend ]
         ├── Interactive Entity Network Graph (React Flow)
         ├── Dual Model Risk Comparison & Feature-Isolation Slider
         ├── Synthesized Case Dossier with 1-Click Markdown Export
         └── Dynamic Business Economics ROI Calculator
```

---

## 5-Minute Judge Demonstration Walkthrough

To experience the platform during live evaluation, run `start_demo.bat` or follow the steps below:

### Curated Evaluation Cases

| Case | Transaction ID | Target Account | Amount | Ground Truth | Model A | Model B | Role in Demo |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **`TXN_00000203`** | `ACC_000213` | `₹99,500.00` | `ring` | `99.94%` | `99.92%` | **Primary Coordinated-Ring Hero:** Large transaction, high device sharing (`DEV_000045`), multi-account cluster. |
| **2** | **`TXN_00000001`** | `ACC_000002` | `₹14,500.00` | `ring` | `99.96%` | `99.95%` | **Secondary High-Risk Anomaly:** Rapid outgoing velocity, shared hardware endpoint. |
| **3** | **`TXN_00000646`** | `ACC_000054` | `₹1,159.95` | `legitimate` | `0.10%` | `0.10%` | **Low-Risk Control Case:** Legitimate netbanking payment, singleton graph component, zero shared endpoints. |
| **4** | **`TXN_00000500`** | `ACC_000456` | `₹764.87` | `legitimate` | `0.07%` | `0.08%` | **Low-Risk Control Case:** Everyday peer UPI transfer, baseline behavior, low risk. |

### Demonstration Script
1. **Navigate to Hero Case (`TXN_00000203`):**
   - URL: `http://localhost:3000/cases/TXN_00000203`
   - Observe **Case Header**: Target Account `ACC_000213`, Amount `₹99,500.00`, IMPS, Risk Band: **HIGH**.
   - Observe **Risk Comparison**: Model A `99.94%`, Model B `99.92%`.
2. **Inspect Model Feature-Isolation Sensitivity Analysis:**
   - Scroll to **Model Feature-Isolation Sensitivity Analysis**.
   - Observe that neutralizing 21 graph topological features evaluates the model under an isolated-entity baseline ($P_{\text{isolated}} = 99.92\%$, $\Delta = -0.00$ pp).
   - Review the explicit scientific disclosure: *"In-silico model sensitivity analysis, not a causal claim."*
   - Review **Provenance-Grounded Evidence Mapping** linking top graph features (`g_shared_device_accounts_count`) to Stage 9 verified evidence records (`EVD_DEV_ACC_000213_DEV_000045`).
3. **Inspect Entity Network Topology:**
   - Explore the central node `TXN_00000203` connected to `ACC_000213`, hardware endpoint `DEV_000045`, and peer accounts.
4. **Review & Export Synthesized Investigator Dossier:**
   - Scroll to **Synthesized Investigator Dossier**.
   - Review the factual Executive Case Brief, Corroborating Evidence Chain, and Potential Benign Explanations (classified as hypotheses with mandatory notice: *"Additional verification required"*).
   - Click **"Copy Investigator Dossier (Markdown)"** for instant export into ticketing systems.
5. **Explore Business Economics & ROI Modeling:**
   - Navigate to `http://localhost:3000/analytics`.
   - Review **Tier 1 Observed Benchmark Data** (₹78,64,287 fraud exposure, 233 ring transactions, 72 ring accounts).
   - Adjust **Tier 2 Operational Assumptions** (Interception Rate 85%, Cost per Case ₹350, Friction per FP ₹1,200).
   - Observe **Tier 3 Derived Economic Estimates**: **₹66,03,094 Net Value Saved** with an **80.98x ROI Multiple**.
6. **Compare Low-Risk Control Case (`TXN_00000646`):**
   - Click `TXN_00000646` in the Case Selector bar.
   - Observe immediate low risk classification (`0.10%`), singleton graph component, and absence of co-usage alerts.

---

## Machine Learning & Transparent Benchmark Parity

In compliance with scientific honesty standards, RingGuard AI openly documents its offline synthetic held-out evaluation results (Stages 6 & 7):

| Evaluation Metric | Model A (Baseline — 37 Features) | Model B (Graph — 58 Features) | Measured Delta | Status / Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **PR-AUC** | `1.0000` | `1.0000` | `0.0000` | Parity Ceiling |
| **ROC-AUC** | `1.0000` | `1.0000` | `0.0000` | Parity Ceiling |
| **Precision** | `1.0000` | `1.0000` | `0.0000` | Parity Ceiling |
| **Recall** | `1.0000` | `1.0000` | `0.0000` | Parity Ceiling |
| **F1 Score** | `1.0000` | `1.0000` | `0.0000` | Parity Ceiling |
| **False Positive Rate** | `0.0000` | `0.0000` | `0.0000` | Parity Ceiling |

> [!NOTE]
> **Why is the Delta 0.0000 on the Synthetic Test Set?**  
> In the synthetic benchmark dataset, ring fraud scenarios exhibit distinctive transaction amounts and behavioral velocities that allow both Model A and Model B to achieve perfect separability on the held-out split.  
> **Model B's critical contribution is not artificial metric inflation, but topological context**: providing the 21 structural signals that drive the Stage 9 Evidence Engine, graph visualization, and investigator case briefs.

---

## Stage 13: Hard-Negative Challenge Benchmark (Robustness Stress Test)

To stress-test model robustness beyond the pristine held-out test set, Stage 13 introduces an out-of-sample **Hard-Negative Challenge Dataset** (`755 transactions`, `200 accounts`, seed `20260905`). It contains **599 high-difficulty legitimate transactions** that deliberately mimic fraud patterns (shared hardware, shared office IPs, common landlord rent sinks, flash sale bursts) alongside **156 subtle ring controls**.

### Overall Performance on Challenge Set ($T = 0.70$)

| Evaluation Metric | Model A (Baseline — 37 Feat) | Model B (Graph — 58 Feat) | Measured Delta ($B - A$) | Interpretation / Status |
| :--- | :---: | :---: | :---: | :--- |
| **PR-AUC** | `0.2105` | `0.2056` | `-0.0049` | Results are consistent with graph features contributing to the ranking degradation |
| **ROC-AUC** | `0.5245` | `0.5067` | `-0.0178` | Near random baseline when amounts and sharing overlap |
| **Precision** ($T=0.70$) | `0.2020` | `0.2020` | `+0.0000` | Identical threshold classification |
| **Recall** ($T=0.70$) | `0.6803` | `0.6803` | `+0.0000` | 100 out of 147 ring controls detected (testing pings missed) |
| **F1 Score** ($T=0.70$) | `0.3115` | `0.3115` | `+0.0000` | Identical discrete F1 score |
| **False Positive Rate** | `65.07%` | `65.07%` | `+0.00%` | 395 False Positives out of 607 |
| **True Positives (TP)** | `100` | `100` | `+0` | 100 ring cases caught (47 micro-transfers evaded) |

### Category-Level Slice Breakdown (Which Look-Alikes Cause False Alarms?)

| Category Code | Description | Samples | Model A FPs (FPR) | Model B FPs (FPR) | Delta FP |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`A_SHARED_DEVICE`** | Family members sharing household desktop/tablet | `80` | `44 (55.0%)` | `44 (55.0%)` | `+0` |
| **`B_SHARED_IP`** | Co-workers transacting on shared office Wi-Fi | `88` | `42 (47.7%)` | `42 (47.7%)` | `+0` |
| **`C_COMMON_BENEFICIARY`** | Tenants paying monthly rent to common landlord | `85` | `85 (100.0%)` | `85 (100.0%)` | `+0` |
| **`D_HIGH_VOLUME_MERCHANT`** | Consumer purchase surge during flash sales | `88` | `66 (75.0%)` | `66 (75.0%)` | `+0` |
| **`E_COORDINATED_TIMING`** | Payday rush-hour concurrent utility billings | `89` | `38 (42.7%)` | `38 (42.7%)` | `+0` |
| **`F_DENSE_COMMUNITY`** | Colleagues splitting mutual dining/travel expenses | `89` | `42 (47.2%)` | `42 (47.2%)` | `+0` |
| **`G_COMPOUND_INFRA`** | Small business sharing office hardware + vendor | `88` | `78 (88.6%)` | `78 (88.6%)` | `+0` |
| **`H_SUBTLE_RING_FRAUD`** | Coordinated mule syndicates (Control Group) | `147` | `0 (0.0%)` [100 TP] | `0 (0.0%)` [100 TP] | `+0` |

> [!IMPORTANT]
> **Key Scientific Finding & Governance Implication:**  
> On deliberate hard-negative lookalikes with realistic amount and topology overlap (amounts spanning ₹450 to ₹75,000 across legitimate and ring controls; single-feature amount AUC = 0.5634), Model B does not provide an automated classification advantage over Model A (PR-AUC 0.2056 vs 0.2105). Results are consistent with graph features contributing to the ranking degradation when benign infrastructure sharing mimics coordinated fraud topologies.  
> **This demonstrates a concrete in-silico failure mode of uncalibrated graph models.** Relying on raw graph risk scores for autonomous automated enforcement (auto-blocking) creates significant false-positive hazards when legitimate activity exhibits coordinated topology. High-risk graph flags MUST be routed to **controlled human investigation dossiers (Stage 10/12)** to verify whether shared endpoints reflect authentic co-location or coordinated collusion before taking action.


---

## Stage 14: Cold Start + Calibration + Operational Threshold Policies

Stage 14 introduces principled post-hoc probability calibration, operational threshold optimization under explicit economic assumptions, and cold-start graph confidence segmentation with strict non-mutating safety guardrails.

### 1. Post-Hoc Probability Calibration
- **Decoupled Validation Setup:** Validation data ($N=300$) is chronologically bisected 50/50 into **`Val-Calib`** ($N=150$, pos=32, neg=118) for fitting and calibrator selection, and **`Val-Thresh`** ($N=150$, pos=23, neg=127) for threshold policy optimization.
- **Evaluated Methods:** Raw uncalibrated probabilities, Platt Scaling (Sigmoid logistic regression on logits), and Isotonic Regression.
- **Deterministic Selection Algorithm:**
  1. Compute Brier scores on `Val-Calib` ($N=150$).
  2. Degradation Fallback: If both Platt and Isotonic degrade (increase) Brier score relative to raw, fall back to `raw`.
  3. Tie-Breaker Preference: If $|\text{BS}_{\text{platt}} - \text{BS}_{\text{iso}}| \le 0.005$, select Platt scaling for parametric stability on finite validation samples.
  4. Selected Method: **Platt Scaling** for both Model A and Model B.
- **Calibration Metrics Summary:**

| Model Partition | Raw Brier | Platt Brier | Isotonic Brier | Selected Method | Test Brier (Post-Freeze) | Test ECE (Diagnostic) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model A (Baseline)** | `0.000001` | `0.000001` | `0.000000` | **`PLATT`** (Tie-Break) | `0.000001` | `0.000878` |
| **Model B (Graph)** | `0.000001` | `0.000001` | `0.000000` | **`PLATT`** (Tie-Break) | `0.000001` | `0.000903` |

### 2. Operational Threshold Policies & Economic Sensitivity
Thresholds are optimized across discrete policy scenarios strictly on `Val-Thresh` ($N=150$) and frozen before evaluating the held-out test set ($N=300$).

| Scenario Code | Policy Scenario Name | Validation Objective | Frozen Threshold | Val Primary Metric | Held-Out Test F1 | Modeled Loss Avoided | Modeled Net Value Saved |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`T_star_f1`** | Maximum F1 Policy | Maximize F1 score | `T = 0.99` | `F1 = 1.0000` | `1.0000` | ₹11,70,872.45 | ₹11,61,772.45 |
| **`T_star_fpr`** | Strict False-Positive Control | Bound $\text{FPR} \le 0.02$, max recall | `T = 0.99` | `Recall = 1.0000` | `1.0000` | ₹11,70,872.45 | ₹11,61,772.45 |
| **`T_star_precision`** | High Precision / Low Friction | Target $\text{Precision} \ge 0.85$, max recall | `T = 0.99` | `Recall = 1.0000` | `1.0000` | ₹11,70,872.45 | ₹11,61,772.45 |
| **`T_star_economic`** | **Economic Value Maximization** | **Maximize Modeled Net Value Saved** | **`T = 0.99`** | **₹6,28,600.00** | **`1.0000`** | **₹11,70,872.45** | **₹11,61,772.45** |

> [!NOTE]
> **Recommended Operational Threshold & Mathematical Reconciliation:**  
> **`T_star_economic` ($T = 0.99$)** is designated as the primary recommended threshold for operational deployment. On the held-out test set ($N=300$), it captures all 26 ring fraud transactions ($\text{TP}=26, \text{FP}=0, \text{FPR}=0.0$) across ₹13,77,497.00 total fraud exposure. Under stated assumptions ($85\%$ interception rate, $C_{\text{FP}} = ₹1,200$, $C_{\text{inv}} = ₹350$):
> $$\text{Modeled Loss Avoided} = ₹13,77,497.00 \times 0.85 = \mathbf{₹11,70,872.45}$$
> $$\text{Total Review Cost} = (\text{TP} + \text{FP}) \times ₹350 = 26 \times ₹350 = \mathbf{₹9,100.00}$$
> $$\text{Total FP Friction} = 0 \times ₹1,200 = \mathbf{₹0.00}$$
> $$\text{Modeled Net Value Saved} = ₹11,70,872.45 - ₹0.00 - ₹9,100.00 = \mathbf{₹11,61,772.45}$$

#### Multi-Tier Economic Sensitivity Analysis (Model B at $T^* = 0.99$)
- Operational Assumptions: FP Friction Cost = ₹1,200, Investigation Cost = ₹350 per case.
- Metric Labeling: Figures represent **modeled loss avoided** and **modeled net value saved under stated operational assumptions**.

##### Held-Out Test Set Sensitivity ($N=300$, Total Exposure = ₹13,77,497.00, Flagged Cases = 26)

| Interception Tier | Threshold Applied | Flagged Cases ($\text{TP}+\text{FP}$) | Modeled Loss Avoided | FP Friction Cost | Case Review Overhead | Modeled Net Value Saved |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **50% Interception** | `0.99` | `26` | ₹6,88,748.50 | ₹0.00 | ₹9,100.00 | ₹6,79,648.50 |
| **70% Interception** | `0.99` | `26` | ₹9,64,247.90 | ₹0.00 | ₹9,100.00 | ₹9,55,147.90 |
| **85% Interception (Default)** | `0.99` | `26` | ₹11,70,872.45 | ₹0.00 | ₹9,100.00 | ₹11,61,772.45 |
| **100% Interception** | `0.99` | `26` | ₹13,77,497.00 | ₹0.00 | ₹9,100.00 | ₹13,68,397.00 |

##### Validation Partition Sensitivity (`Val-Thresh`, $N=150$, Total Exposure = ₹7,49,000.00, Flagged Cases = 23)

| Interception Tier | Optimal Threshold ($T^*$) | Stability vs Baseline | Modeled Loss Avoided | Friction & Ops Overhead | Modeled Net Value Saved |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **50% Interception** | `0.99` | Stable ($T^* = 0.99$) | ₹3,74,500.00 | ₹8,050.00 | ₹3,66,450.00 |
| **70% Interception** | `0.99` | Stable ($T^* = 0.99$) | ₹5,24,300.00 | ₹8,050.00 | ₹5,16,250.00 |
| **85% Interception (Default)** | `0.99` | Stable ($T^* = 0.99$) | ₹6,36,650.00 | ₹8,050.00 | ₹6,28,600.00 |
| **100% Interception** | `0.99` | Stable ($T^* = 0.99$) | ₹7,49,000.00 | ₹8,050.00 | ₹7,40,950.00 |

### 3. Cold-Start Segmentation & Graph Confidence Hierarchy
- **Confidence Precedence Hierarchy:**
  1. `UNAVAILABLE`: Transaction has zero connected accounts in co-usage graph (`g_connected_accounts_count == 0`). Graph signals are ungrounded.
  2. `LIMITED`: Transaction occurs during early behavioral infancy (`beh_is_first_tx == 1` or `beh_hist_tx_count <= 2`).
  3. `VERIFIED`: Transaction has established historical behavioral and topological co-usage signals.
- **Point-in-Time Distribution across 2,000 Transactions (497 Unique Accounts):**
  - `UNAVAILABLE`: 61 transactions (3.05%)
  - `LIMITED`: 1,295 transactions (64.75%)
  - `VERIFIED`: 644 transactions (32.20%)
- **Rule Sufficiency Audit:**
  - `RULE_1_NEW_ACCOUNT` (Age $\le 3$ days): $N = 0 \to$ Flagged as **`LIMITED / INSUFFICIENT EVIDENCE (N=0)`**.
  - `RULE_2_LOW_VELOCITY` (Tx Count $\le 2$): $N = 1,356 \to$ Evaluated.
  - `RULE_3_FIRST_TRANSACTION` (First Tx): $N = 497 \to$ Evaluated (corresponds to first observed event for each of the 497 unique accounts).
  - `RULE_4_ISOLATED_GRAPH` (Connected Accounts = 0): $N = 61 \to$ Evaluated.
- **Safety Guarantee & Decision Support:**
  - **Zero Input Mutation:** Model B's 58-feature vector is strictly untouched during cold-start evaluation.
  - **Advisory Policy:** When `graph_confidence` is `LIMITED` or `UNAVAILABLE`, human risk analysts are advised to prioritize transactional baseline features and request Tier-1 identity verification. RingGuard AI never executes autonomous blocking or clearing.

---

## Business Value & Economics Formulation

$$\text{Net Value Saved} = \text{Estimated Fraud Loss Avoided} - \text{Customer Friction Cost} - \text{Investigation Cost}$$

### Transparent Separation of Tiers
1. **Tier 1 — Observed Benchmark Values (Verified Database Records):**
   - Total Transactions: `2,000`
   - Ring Fraud Transactions: `233`
   - Ring Fraud Accounts: `72`
   - Total Ring Fraud Exposure: `₹78,64,287.00`
   - Synthetic Test Set False Positive Rate: `0.00%`
2. **Tier 2 — Configurable Operational Modeling Assumptions:**
   - Interception Rate: `85.0%` (configurable `50%`–`100%`)
   - Cost per Investigation: `₹350 / case` (15 min at ₹1,400/hr tier-2 analyst rate)
   - Customer Friction Cost per FP: `₹1,200` (estimated customer support and brand friction)
3. **Tier 3 — Derived Economic Output (Default Parameters):**
   - **Estimated Fraud Loss Avoided:** `₹66,84,643.95` (`₹78,64,287 × 85%`)
   - **Total Investigation Overhead:** `₹81,550.00` (`233 cases × ₹350`)
   - **Total Customer Friction Cost:** `₹0.00` (`0 false positives × ₹1,200`)
   - **Net Economic Value Saved:** `₹66,03,093.95`
   - **Estimated ROI Multiple:** `80.98x`

---

## Operational Safeguards & Human Governance

- **Defense-Only Architecture:** Designed strictly for detection, evidence extraction, and investigation triage. RingGuard AI does not possess API access or credentials to block payments, freeze accounts, or modify banking ledgers.
- **Zero External LLM Dependencies:** Investigator case dossiers are synthesized **100% deterministically and offline** using template-based extraction from verified database records. Zero external API calls, zero token latency, zero hallucinations.
- **Human Authority:** All investigation recommendations (e.g. "Request hardware biometric confirmation", "Verify beneficiary KYC") are structured checklists for human risk analysts.
- **In-Memory Audit Trail:** Session decisions and tool executions are recorded in-memory for auditability without mutating the pristine evaluation database.

---

## Quick Start & Installation

### Option 1: Automated Launcher (Windows)
Double-click `start_demo.bat` in the repository root. It will:
1. Verify Python virtual environment and database connectivity.
2. Launch the FastAPI backend on `http://localhost:8000`.
3. Launch the Next.js production frontend on `http://localhost:3000`.
4. Open your browser directly to `http://localhost:3000/cases/TXN_00000203`.

### Option 2: Manual Terminal Startup

#### 1. Backend Service
```bash
# From repository root:
cd backend
python -m venv venv
# Activate virtual environment:
# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### 2. Frontend Application
```bash
# From repository root:
cd frontend
npm install
npm run build
npm run start
```
- Web Application: `http://localhost:3000/cases/TXN_00000203`
- Analytics Dashboard: `http://localhost:3000/analytics`

#### 3. Automated Test Execution & Stage 14 Verification
```bash
# Run all backend unit & regression tests (146 tests):
backend\venv\Scripts\pytest backend\tests\ -v

# Run Stage 14 Cold-Start, Calibration & Threshold Evaluation Pipeline:
backend\venv\Scripts\python.exe scripts/run_stage14_evaluation.py

# Run Stage 13 Hard-Negative Challenge Data Generation & Evaluation:
backend\venv\Scripts\python.exe scripts/generate_challenge_data.py
backend\venv\Scripts\python.exe scripts/evaluate_challenge.py

# Run frontend production build & TypeScript validation:
npm --prefix frontend run build
```
