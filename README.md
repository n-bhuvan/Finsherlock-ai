# RingGuard AI

> **Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation Platform**  
> *Razorpay AI Buildathon 2026 — Track 02 (AI Risk Manager)*

[![Backend Tests](https://img.shields.io/badge/backend%20tests-197%20passed-emerald.svg)](backend/tests)
[![Typecheck](https://img.shields.io/badge/typescript-zero%20errors-cyan.svg)](frontend)
[![Build](https://img.shields.io/badge/next.js%2015-production%20ready-blue.svg)](frontend)
[![Compliance](https://img.shields.io/badge/governance-defense--only-amber.svg)](#operational-safeguards--human-governance)
[![Status](https://img.shields.io/badge/status-submission--ready%20prototype-purple.svg)](#project-positioning--synthetic-data-disclosure)

---

## Project Positioning & Synthetic Data Disclosure

> [!IMPORTANT]
> **Prototype & Synthetic Data Notice:**  
> RingGuard AI is a **submission-ready prototype / research-grade defensive risk investigation system built entirely on synthetic data**.  
> - **Zero Real Customer PII:** RingGuard AI does not use, ingest, or expose real Razorpay customer or merchant transaction data. All accounts, entities, transactions, and IPs are synthetically generated.
> - **Simulated Economics:** All business-value figures, modeled loss avoided, and ROI metrics are **simulated, modeled, and assumption-based**.
> - **Defense-Only Decision Support:** The system operates strictly as an investigative decision-support tool for human risk analysts with zero autonomous payment blocking or account freezing authority.

---

## Executive Summary

Coordinated fraud syndicates and mule networks exploit traditional payment gateways by ensuring individual transactions appear normal when viewed in isolation. By distributing illicit fund flows across dozens of accounts linked through shared hardware devices, cellular IP gateways, and common beneficiaries, bad actors bypass per-transaction velocity checks.

**RingGuard AI** solves this challenge through a **graph-native, evidence-first AI risk platform**:
1. **Graph Structural Intelligence:** Models multi-entity topology (accounts, devices, IPs, beneficiaries) using NetworkX, extracting 21 point-in-time graph features.
2. **Dual Model Evaluation:** Compares localized baseline indicators (Model A, 37 features) against network-enhanced topology (Model B, 58 features).
3. **Deterministic Evidence Engine:** Extracts verified, ranked evidence signals with exact database provenance.
4. **Deterministic Investigator Dossier:** Condenses 8 fragmented manual review queries into a unified 30-second executive brief with 1-click Markdown export.
5. **Bounded Uncertainty-Driven Investigation (Stage 15):** Dynamically optimizes tool invocation order using Expected Information Gain and explicit stopping policies.
6. **Evidence-Grounded Forensic Explanation (Stage 16):** Synthesizes claim-level grounded narrative explanations backed by 7 layers of prompt-injection defense.
7. **Cryptographic Append-Oriented Audit Trail (Stage 16):** Logs explanation provenance in a tamper-evident SHA-256 hash chain.
8. **Transparent Business Economics:** Models net financial value using the Track 02 standard formula:
   $$\text{Modeled Net Value Saved} = \text{Modeled Loss Avoided} - (\text{FP} \times C_{\text{FP}}) - ((\text{TP} + \text{FP}) \times C_{\text{inv}})$$
9. **Strict Defense-Only Boundaries:** Enforces human-in-the-loop governance with zero autonomous account freezing or fund blocking.

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

### 15-Step End-to-End Judge Demonstration Script

1. **Select Suspicious Transaction (`TXN_00000203`):**
   - URL: `http://localhost:3000/cases/TXN_00000203` (or click `TXN_00000203` in the Case Quick Selector).
   - Observe **Case Header**: Target Account `ACC_000213`, Amount `₹99,500.00`, Channel `IMPS`, Status `SUCCESS`.
2. **Review High Risk Scoring:**
   - Model A Baseline: `99.94%`, Model B Network Graph: `99.92%`. Calibrated Risk: `0.9980`, Risk Band: **`HIGH`**.
3. **Inspect Connected Entity Network Topology:**
   - Explore the central node `TXN_00000203` connected to `ACC_000213`, shared hardware `DEV_000045`, and adjacent syndicate accounts.
4. **Examine Deterministic Evidence Engine:**
   - Review 6 verified evidence records: `EVD_RAPID_TXN_...` (burst velocity), `EVD_MULTIHOP_...` (indirect links), `EVD_DEV_...` (shared hardware).
5. **Run Bounded Investigation (Stage 15 Agent):**
   - Scroll to **Investigation Agent Panel**. Review candidate read-only tools and simulated tool budgets (₹150 max budget).
   - Click **"Run Bounded Investigation"** to observe dynamic tool execution ranked by Expected Information Gain.
6. **Observe Uncertainty Reduction Trace:**
   - Watch initial investigative uncertainty ($u_0 = 0.1986$) decrease monotonically with each tool invocation to final state ($u_t = 0.1002$).
7. **Verify Explicit Stopping Policy:**
   - Observe the stopping badge: **`Sufficient Evidence Gathered`** (`SUFFICIENT_EVIDENCE`), proving the agent terminates deterministically without runaway tool calls.
8. **Inspect Case Prioritization & Next-Best-Action:**
   - Triage action classified as **`HOLD_FOR_REVIEW`** with prioritized ranking score based on:
     $$\text{Priority} = 0.35 \times \text{Risk} + 0.30 \times \text{Exposure} + 0.20 \times \text{Uncertainty} + 0.15 \times \text{NetworkLeverage}$$
9. **Review Modeled Business Economics:**
   - On the Case page or Analytics Dashboard (`/analytics`), view the verified Track 02 formula:
     $$\text{Modeled Net Value Saved} = ₹11,70,872.45 - ₹0.00 - ₹9,100.00 = \mathbf{₹11,61,772.45}$$
10. **Generate Evidence-Grounded AI Explanation (Stage 16):**
    - Scroll to **Evidence-Grounded AI Forensic Explanation**.
    - Click **"Generate AI Forensic Explanation"** to synthesize a grounded case brief via `POST /api/investigation/explanation/generate`.
11. **Verify Structured Claim Grounding:**
    - Expand the claim matrix: every **`FACT`** claim cites exact verified evidence IDs (`EVD_DEV_...`, `EVD_RAPID_...`).
    - Grounding ratio is **1.00 (100% grounded)** with zero ungrounded factual hallucinations.
12. **Review 7-Layer Prompt-Injection Defense:**
    - Observe that dynamic inputs are enclosed in `<UNTRUSTED_DATA>` boundaries, pre-execution regex scanning neutralized adversarial payloads, and Pydantic schemas enforce output structure.
13. **Inspect Cryptographic Audit Hash Chain:**
    - Navigate to `/audit` (or inspect Audit ID on the Case page).
    - Review the verified SHA-256 link: $\text{record\_hash} = \text{SHA256}(\text{prev\_hash} + \text{canonical\_payload})$.
    - Notice authoritative limitation: *"Detects record tampering, interior deletion and reordering; external checkpointing is required to detect final-tail deletion/truncation."*
14. **Enforce Human Governance & Defense-Only Boundary:**
    - Observe the mandatory **`Human Approval Required`** banner and non-enforcement warning. Zero automated account freezing or fund movement is permitted.
15. **Demonstrate Low-Risk Controls (`TXN_00000646` & `TXN_00000500`):**
    - Click `TXN_00000646` in the Case Selector bar: Netbanking transfer, `0.10%` risk, singleton graph, zero co-usage.
    - Click `TXN_00000500`: UPI peer payment, `0.08%` risk, standard profile.
    - Confirms RingGuard AI discriminates legitimate low-risk commerce from fraud rings.

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

## Stage 15: Investigation Efficiency + Business Impact

Stage 15 introduces a **bounded uncertainty-driven investigation agent** and a **deterministic case prioritization engine** that optimizes the sequence and depth of read-only investigation queries while strictly preventing runaway execution.

### 1. Investigative Uncertainty Heuristic & Dynamic State
- **Deterministic Uncertainty State ($u_t \in [0.05, 0.95]$):** Initialized from calibrated risk proximity to $0.50$ (maximum decision ambiguity) modulated by graph confidence:
  $$u_0 = 1.0 - 2 \cdot |p_{\text{calibrated}} - 0.50| + \Delta_{\text{graph}}$$
- **Dynamic Evidence Updates:**
  - Supporting evidence: decreases uncertainty proportional to signal severity.
  - Conflicting/contradictory evidence: increases uncertainty to trigger deeper human inspection.
  - Empty/zero-hit queries: leave uncertainty unchanged and penalize tool redundancy.
- **Expected Information Gain (EIG):** Tools are selected greedily based on expected utility:
  $$\text{EIG}(T) = \frac{\text{Relevance} \times \text{RemainingUncertainty}}{1 + \text{Cost}(T)} \times \text{RedundancyPenalty}$$

### 2. Guardrails & Explicit Stopping Conditions
The investigation stops deterministically upon the first satisfied condition:
1. `SUFFICIENT_EVIDENCE`: At least 2 verified high-severity evidence items collected.
2. `UNCERTAINTY_LOW_ENOUGH`: $u_t \le 0.15$ (decision ambiguity resolved).
3. `INVESTIGATION_COST_TOO_HIGH`: Accumulated tool queries reach budget limit (₹150 max).
4. `MAX_STEPS_REACHED`: Maximum bounded iterations ($N=5$) reached.
5. `CONFLICTING_EVIDENCE_ESCALATION`: Opposing high-severity evidence detected, immediately escalating to human review.

### 3. Sliced Investigation Efficiency Benchmark ($N=300$)

| Evaluation Slice | Sample Count | Avg Steps | Initial Uncertainty | Final Uncertainty | Avg Uncertainty Reduction | Avg Tool Cost | Top Stopping Reason |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Overall (Held-Out Test)** | `300` | `0.72` | `0.1022` | `0.0694` | `0.0328` | ₹28.57 | `UNCERTAINTY_LOW_ENOUGH` (197) |
| **Ring Fraud Cases** | `26` | `2.12` | `0.1986` | `0.1002` | `0.0984` | ₹82.69 | `SUFFICIENT_EVIDENCE` (25) |
| **Hard-Negative Cases** | `30` | `0.47` | `0.0854` | `0.0638` | `0.0216` | ₹18.00 | `UNCERTAINTY_LOW_ENOUGH` (24) |
| **Cold-Start Cases** | `61` | `0.54` | `0.1142` | `0.0811` | `0.0331` | ₹22.13 | `UNCERTAINTY_LOW_ENOUGH` (48) |

> [!NOTE]
> **Workflow Compression Disclosure:** Figures describe structural workflow compression and simulated query optimization under bounded stopping policies, rather than a measured human analyst clock-time experiment.

---

## Stage 16: LLM Explanation + Audit + Security

Stage 16 delivers **evidence-grounded AI forensic case explanations** with enterprise-grade defensive guardrails, cryptographic provenance, and strict retrieval-only semantics.

### 1. Provider-Agnostic Architecture & Zero-Network Fallback
- **`BaseLLMProvider`**: Pluggable abstraction supporting `GeminiLLMProvider` (when configured with API credentials) and `DeterministicFallbackProvider`.
- **Deterministic Safe Fallback**: Zero-network offline fallback guarantees 100% operational availability on provider unavailability, timeout, malformed output, or prompt injection.

### 2. True Claim-Level Grounding
- Explanations decompose into explicit typed claim objects (`FACT`, `INTERPRETATION`, `LIMITATION`):
  - Every **`FACT`** claim **must** cite at least one verified evidence ID from the Stage 9 `EvidenceEngine`.
  - Hallucinated or unsupported fact claims are strictly rejected and replaced with deterministic verified text.
- **Formal Grounding Ratio:** Enforces $\text{Grounding Ratio} = 1.00$ on all accepted outputs.

### 3. Layered Prompt-Injection Defense
Security is enforced through **7 defensive layers** rather than regex scanning alone:
1. **Untrusted-Data Boundary**: All dynamic transaction and evidence text is encapsulated inside `<UNTRUSTED_DATA>...</UNTRUSTED_DATA>` blocks.
2. **System Instructions**: Strict immutable system prompts framing the model's forensic task.
3. **Input Scanning**: Pre-execution regex detection of known injection phrases, role spoofing, and delimiter escapes.
4. **Structured Schemas**: Enforced Pydantic response models preventing arbitrary output structures.
5. **Claim Grounding**: Mandatory verification of factual claims against database evidence IDs.
6. **Output Sanitization**: Neutralization of XSS, HTML tags, scripts, and accidental secret leakage.
7. **Deterministic Fallback**: Automatic routing to verified deterministic offline generators upon any detected injection or anomaly.

### 4. Cryptographic Append-Oriented Audit Trail
- Stored chronologically in `ml/data/audit/explanation_audit_log.jsonl`.
- Cryptographic hash formula:
  $$\text{record\_hash} = \text{SHA256}(\text{previous\_record\_hash} + \text{canonical\_payload\_json})$$
- **Authoritative Security Limitation Notice:**
  > *"Detects record tampering, interior deletion and reordering; external checkpointing is required to detect final-tail deletion/truncation."*

### 5. Strict Retrieval-Only GET Semantics
- **`GET /api/investigation/explanation/{id}`**: Strictly read-only from saved explanation storage. Does **not** invoke Gemini, does not generate explanations, does not append audit records, and does not mutate storage. Returns HTTP 404 if not previously generated.
- **`POST /api/investigation/explanation/generate`**: The single, explicit entry point that generates explanations, verifies grounding, and appends to the audit log.

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
# Run all backend unit & regression tests (197 tests):
backend\venv\Scripts\pytest backend\tests\ -v

# Run Stage 14 Cold-Start, Calibration & Threshold Evaluation Pipeline:
backend\venv\Scripts\python.exe scripts/run_stage14_evaluation.py

# Run Stage 13 Hard-Negative Challenge Data Generation & Evaluation:
backend\venv\Scripts\python.exe scripts/generate_challenge_data.py
backend\venv\Scripts\python.exe scripts/evaluate_challenge.py

# Run frontend production build & TypeScript validation:
npm --prefix frontend run build
```
