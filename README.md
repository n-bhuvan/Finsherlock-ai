# RingGuard AI

> **Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation Platform**  
> *Razorpay AI Buildathon 2026 — Track 02 (AI Risk Manager)*

[![Backend Tests](https://img.shields.io/badge/backend%20tests-120%20passed-emerald.svg)](backend/tests)
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

#### 3. Automated Test Execution
```bash
# Run all backend unit & regression tests (120 tests):
backend\venv\Scripts\pytest backend\tests\ -v

# Run frontend TypeScript validation:
npm --prefix frontend run build
```
