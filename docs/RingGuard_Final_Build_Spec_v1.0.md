RINGGUARD AI

Final Build Specification — v1.0

Razorpay AI Buildathon 2026 | Track 02: AI Risk Manager

Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation

Final hybrid version: rigorous ML/evaluation core + evidence-first investigation layer, with controlled investigation AI, explicit false-positive economics, cold-start handling, threshold methodology, and measurable investigation efficiency.

# 1. Executive Product Definition

RingGuard AI is a network-aware abuse-ring detection and evidence-first risk investigation system for merchant risk/operations analysts. It detects coordinated payment-abuse and mule-account networks that can look legitimate when transactions are examined individually, then builds an evidence-backed investigation for human review.

Core workflow: Detect → Connect → Investigate → Correlate → Explain → Quantify Impact → Human Decision.

The project does not claim that graph fraud detection or AI investigation is inherently new. Its central contribution is to experimentally measure whether network context improves detection over transaction-only risk scoring, while quantifying false-positive cost and investigation effort.

# 2. Razorpay Track 02 Alignment

The implementation must remain aligned with the official Buildathon rules. Where official rules change, those rules take precedence over this specification.

# 3. Core Problem

A transaction may appear normal in isolation while becoming suspicious when its surrounding entities and behavior are considered together.

Multiple accounts may share devices or IP addresses.

Apparently independent accounts may route funds to common beneficiaries.

Funds may be rapidly split across connected accounts.

New accounts may exhibit unusually high-value activity.

Indirect multi-hop relationships may connect current activity to previously suspicious entities.

After an alert, analysts still need to gather evidence, connect entities, reconstruct events and document the case.

RingGuard therefore addresses two linked problems: (1) detecting coordinated abuse that transaction-level analysis can miss, and (2) reducing the effort required to understand and investigate the resulting alert.

# 4. Core Hypothesis

Can network-level evidence improve coordinated abuse detection over transaction-level risk scoring while maintaining an acceptable false-positive cost, and can an evidence-first investigation workflow reduce the human effort required to review those alerts?

# 5. Final Capability Stack

# 6. Abuse-Ring Detection

Primary detection capability. RingGuard outputs a ring-membership probability at the account/cluster level rather than relying only on a per-transaction fraud score.

Shared devices

Shared IP addresses

Common beneficiaries

Connected accounts

Transaction velocity and frequency

Coordinated timing

Rapid fund splitting

Account age at first large transaction

Suspicious-neighbor and network-context features

Multi-hop relationships

Community/cluster structure

A single signal must not automatically imply fraud. The model should combine multiple signals and be evaluated against hard legitimate look-alikes.

# 7. Financial Evidence Graph

Nodes: customers, accounts, transactions, devices, IPs, beneficiaries and merchants where applicable.

Edges: shared-attribute relationships and transaction/fund-flow relationships.

Community detection identifies suspicious clusters.

Multi-hop traversal exposes indirect relationships.

Every displayed relationship should be backed by traceable evidence.

Example evidence: Account A and Account B used the same device during the relevant investigation period.

# 8. Timeline Reconstruction

RingGuard automatically reconstructs the relevant event sequence.

Account creation

Large incoming payment

Rapid transfers

Linked-account discovery

Shared-device/IP discovery

Beneficiary relationship

Historical suspicious connection

Final risk assessment

The timeline should make the investigation understandable at a glance rather than requiring an analyst to manually correlate timestamps.

# 9. Controlled Investigation AI

The original free-form autonomous agent is intentionally not used. RingGuard uses a bounded investigation agent that can select only approved, read-only operations.

get_account()

get_transactions()

find_related_accounts()

find_shared_devices()

find_shared_ips()

find_common_beneficiaries()

trace_fund_flow()

reconstruct_timeline()

get_risk_features()

Every tool call must be permission checked, logged and tied to evidence. The agent cannot alter risk scores, move funds, execute payments, write to financial systems or issue autonomous enforcement.

# 10. LLM Role

The LLM is deliberately post-hoc. It receives structured model and investigation evidence and generates:

Why the case was flagged

The strongest evidence chain

Potential benign explanations

A concise investigator summary

Suggested additional evidence to review

The LLM never calculates the numerical risk score and never makes the final enforcement decision.

Failure fallback: if the LLM call fails, the system displays a template-based evidence summary directly from the ML/graph outputs. Detection and escalation therefore do not depend on the LLM.

# 11. Counterfactual Risk Explanation

RingGuard should explicitly show which evidence changes the decision.

These states are illustrative for the demo; final claims must come from actual model/test results.

# 12. Legitimate-Network / False-Positive Handling

Families sharing a device

Employees sharing an office IP

Small businesses sharing a supplier or beneficiary

Legitimate high-volume merchants

Normal recurring beneficiary relationships

The model should use contextual behavioral and transaction evidence before escalating. These hard negatives must appear in evaluation data.

Create a dedicated Legitimate Network Challenge Set to measure false escalations on legitimate shared-infrastructure cases.

# 13. Dataset Strategy

Synthetic data must be openly disclosed as synthetic. The generator and detection logic must be developed independently so that the model is not simply learning hand-coded generation rules.

The currently published official Buildathon information does not establish that an online/public dataset is mandatory or that synthetic data is prohibited. If future official rules specify otherwise, those rules take precedence.

# 14. Synthetic Data Entities

Customers

Accounts

Transactions

Devices

IP addresses

Beneficiaries

Merchants

KYC/status attributes where appropriate

Historical alerts/investigation references where needed

Data should contain legitimate activity, individual suspicious activity and coordinated abuse-ring activity.

# 15. Abuse-Ring Scenarios

Shared Device Ring — multiple accounts share a device and exhibit coordinated activity.

Common Beneficiary Ring — apparently independent accounts route funds toward a common beneficiary.

Rapid Fund Distribution — a large incoming payment is quickly split across connected accounts.

Historical Connection — a new account connects through infrastructure to a previously suspicious entity.

Combined Ring — several individually weak signals combine into a high-confidence network-level assessment.

Legitimate Look-Alike — shared infrastructure exists but surrounding behavior remains legitimate.

# 16. Final Detection Strategy

Transaction / behavioral modeling — learn suspicious transaction behavior.

Graph intelligence — add entity relationships, community and multi-hop signals.

Ring ML model — estimate ring-membership probability using engineered and graph features.

The investigation layer comes after detection. It does not replace the measurable risk model.

# 17. Evaluation Design

Use a leakage-resistant evaluation framework.

Create training/development data.

Use a time-based split where possible.

Ensure no account, device or IP entity is shared across train and test partitions where such isolation is required by the prediction setup.

Freeze detection logic before final test scenarios are generated.

Keep the final held-out test set untouched during tuning.

Evaluate transaction-only baseline.

Evaluate transaction + graph model.

Evaluate the final investigation workflow separately on operational metrics.

## 17.1 Threshold Selection

Use the training set to fit candidate models.

Use the validation set to select the operating threshold using a declared business constraint, such as maximum acceptable false-positive rate, minimum precision, or minimum expected business value.

Freeze the threshold before accessing the final test results.

Report final precision, recall, PR-AUC, cost and business-value results only from the untouched test set.

## 17.2 Cold-Start Handling

New accounts with insufficient history must not automatically be treated as high risk.

Use a conservative transaction/behavior baseline when graph history is sparse.

Explicitly label graph confidence as limited or unavailable when appropriate.

Increase or revise risk only as new behavioral and network evidence becomes available.

Evaluate cold-start cases separately from mature-account cases.

# 18. Model Comparison

# 19. Detection Metrics

# 20. Investigation Metrics

Average investigation time

Investigation completion rate

Tool-call success rate

Evidence retrieval success

Relevant relationships discovered

Report generation success

Human-review effort reduction

## 20.1 Investigation Efficiency Experiment

Compare a baseline analyst workflow against RingGuard-assisted review on matched investigation cases.

Use actual observed results. Do not claim analyst-time reduction unless it is measured.

# 21. Business Value

Use actual held-out test results; do not use illustrative percentages as final claims.

Recommended simplified demo model:

Fraud Loss Avoided = monetary value of true-positive abuse prevented under the selected operating policy.

Friction Cost = false positives × estimated cost per false positive.

Investigation Cost = escalated cases × estimated analyst cost per case.

Net Business Value = Fraud Loss Avoided − Friction Cost − Investigation Cost.

A more complete model may additionally account for missed-fraud cost, customer churn, support/resolution cost and legitimate transaction value. Clearly label every assumption.

For the final presentation, show the assumptions beside the ₹ calculations rather than hiding them.

# 22. Architecture

Payment Event
↓
Transaction + Behavioral Feature Engine
+
Entity Graph
↓
RingGuard ML Model (XGBoost / LightGBM)
↓
Ring Probability
↓
Evidence Engine
 ├── Device / IP relationships
 ├── Beneficiary analysis
 ├── Fund-flow analysis
 └── Multi-hop relationships
↓
Timeline Engine
↓
Controlled Investigation AI
↓
Structured Evidence
↓
LLM Explanation / Case Summary
↓
Human Risk Analyst
 ├── Approve
 ├── Reject
 └── Request More Evidence
↓
Audit Log

# 23. Technology Stack

# 24. Security and Safety

Defense-only functionality.

Read-only investigative access.

No fund movement.

No autonomous transaction approval or blocking.

Permission checks for every investigative tool.

Audit log for important model and agent actions.

Human decision required for escalation/enforcement.

No silent invention of missing evidence.

# 25. Failure Handling

Database failure → retry, record failure, then escalate/continue where possible.

Missing evidence → explicitly mark evidence unavailable and request alternatives.

Tool failure → retry or use approved alternative.

LLM failure → fall back to template-based evidence summary.

Never fabricate evidence to complete an investigation.

# 26. Final Dashboard

Active cases

High/medium/low risk distribution

Networks detected

Case queue

Ring probability

Top 3–5 evidence items

Evidence graph

Timeline

Counterfactual explanation

Investigation summary

Business impact / FP-cost panel

Human decision controls

Audit trail

# 27. Five-Minute Demo

The ₹4.8 lakh scenario must be clearly labeled synthetic if it is not derived from real permitted test data.

# 28. What Makes RingGuard Different

Do not position RingGuard as 'another AI fraud detector.' Position it as:

A network-aware abuse-ring detection and evidence-first risk investigation layer that experimentally measures the incremental value of network context over transaction-level risk scoring.

Transaction-level baseline is explicitly measured.

Graph contribution is experimentally isolated.

False-positive economics are quantified.

Evidence is traceable rather than generated from an unexplained LLM decision.

Investigation is bounded and auditable.

Human decision remains in control.

Investigation efficiency is measured rather than merely claimed.

# 29. What Is NOT Claimed

Graph fraud detection is not claimed as a new invention.

LLMs are not claimed to be superior fraud classifiers.

Synthetic data is not presented as real Razorpay transaction data.

Near-real-time/batch performance is not presented as production millisecond streaming.

The system is not claimed to replace Razorpay's existing risk infrastructure.

The system does not claim to detect every new fraud pattern.

The system does not claim that graph context will always improve detection; the experiment determines the result.

# 30. Priority Matrix

# 31. Build Order

Synthetic data generator built independently from detector logic + public benchmark loader.

Entity graph construction and community detection.

Transaction/behavior feature pipeline.

GBM classifier and ring-level target.

Time/entity-based held-out evaluation.

Transaction-only vs graph-enhanced comparison.

Threshold selection and calibration.

FP/FN cost and net-business-value calculation.

Hard-negative and legitimate-network challenge evaluation.

Evidence graph and timeline.

Controlled investigation AI.

Investigation-efficiency experiment.

LLM explanation with deterministic fallback.

Dashboard and visual polish.

If time becomes limited, prioritize model/evaluation/business evidence over styling, RAG or elaborate agent behavior.

# 32. Final Project Definition

# 33. Final Judge Positioning

The project should not claim to have invented fraud graphs, behavioral fraud detection or AI investigation. Its strongest defensible contribution is proving whether network-aware risk materially improves upon a transaction-only baseline and whether an evidence-first workflow makes those decisions more useful and economical for human analysts.

The reason this project deserves attention despite existing solutions is: it does not merely add AI features to fraud detection; it experimentally measures the incremental value of network intelligence, quantifies the economic cost of false positives, and turns the resulting alert into traceable evidence that a human risk analyst can act on.

# 34. Final Success Criteria

The graph-enhanced model must be evaluated against a transaction-only baseline.

The final test set must remain untouched during tuning.

No entity leakage between train and test.

Hard legitimate look-alikes must be included.

All final metrics must come from actual test runs.

Synthetic data must be disclosed.

Business-value calculations must expose assumptions.

The LLM must never determine the numerical risk score.

No autonomous fund action is permitted.

The live demo must clearly show the transaction-to-network-to-evidence transition.

Operating thresholds must be selected on validation data and frozen before final testing.

Cold-start cases must have an explicit, conservative handling policy.

Investigation-efficiency claims must be supported by measured comparison results.


| Requirement | RingGuard response |
| --- | --- |
| Loss class | Coordinated payment-abuse / mule-account fraud |
| Working capability | Detector + evidence-first investigation workflow |
| AI/ML | Gradient-boosted risk model using transaction, behavioral and graph features |
| Held-out evaluation | Time/entity-based held-out test set |
| Precision/Recall | Primary detection metrics |
| False-positive cost | Explicit ₹-based business-cost model |
| Defense-only | Read-only investigation; no fund movement or autonomous enforcement |
| Human oversight | Final escalation decision remains with human risk analyst |


| Layer | Purpose | Technique |
| --- | --- | --- |
| Transaction / Behavioral Engine | Detect abnormal transaction behavior | Amount, velocity, timing, frequency, behavioral change, fund splitting |
| Entity Graph | Represent relationships between financial entities | Multipartite graph / NetworkX |
| Ring ML Model | Estimate ring-membership probability | XGBoost or LightGBM |
| Evidence Engine | Collect strongest supporting signals | Structured evidence objects tied to graph/model features |
| Timeline Engine | Reconstruct what happened and when | Ordered event analysis |
| Controlled Investigation AI | Choose useful read-only investigative operations from a bounded tool set | Tool calling with permissions, logging and fallbacks |
| LLM Explanation Layer | Turn structured evidence into analyst-readable explanation | LLM; no risk scoring or enforcement |
| Human Decision | Make final risk action decision | Approve / Reject / Request more evidence |


| Evidence added | Illustrative risk state |
| --- | --- |
| Transaction-only risk | LOW |
| Add behavioral evidence | MEDIUM |
| Add network relationships | HIGH |
| Add coordinated fund-flow evidence | HIGH confidence |


| Dataset | Purpose |
| --- | --- |
| Public fraud benchmark | Baseline/generalization check for fraud-risk modeling |
| Synthetic Razorpay-shaped data | Domain-specific Indian payment and abuse-ring scenarios |
| Hard negatives | Prevent simple surface-pattern matching |
| Held-out test data | Final unbiased evaluation |


| System | Inputs | Question answered |
| --- | --- | --- |
| Baseline A | Transaction + behavioral features | How well does transaction-level detection work? |
| Model B | Transaction + behavioral + graph features | Does network context improve detection? |
| Final RingGuard | Model B + evidence/investigation workflow | Does evidence-first investigation improve review efficiency and decision support? |


| Metric | Priority | Purpose |
| --- | --- | --- |
| PR-AUC | Primary | Useful under severe class imbalance |
| Precision | Primary | How many escalations are actually relevant |
| Recall | Primary | How much abuse is detected |
| False-positive cost (₹) | Primary | Economic cost of incorrect escalation |
| Fraud ₹ prevented | Primary | Business impact estimate |
| F1 | Secondary | Combined precision/recall measure |
| ROC-AUC | Secondary | General discrimination measure |
| Calibration / Brier score | Secondary | Whether probabilities are reliable |
| False-positive rate | Secondary | Rate of legitimate cases incorrectly escalated |
| False-negative cost (₹) | Secondary | Economic cost of missed abuse |
| Latency | Secondary | Honest batch/near-real-time performance |
| Coverage | Secondary | Share of eligible activity receiving a model decision |


| Metric | Baseline review | RingGuard-assisted review |
| --- | --- | --- |
| Median time to complete case | Measure | Measure |
| Evidence retrieval success | Measure | Measure |
| Relevant relationships discovered | Measure | Measure |
| Case completion rate | Measure | Measure |
| Human effort / number of manual steps | Measure | Measure |


| Component | Recommended technology |
| --- | --- |
| Backend | Python, FastAPI, Pydantic |
| Database | PostgreSQL |
| Graph | NetworkX initially; Neo4j only if it materially improves the demo or implementation |
| ML | Pandas, scikit-learn, XGBoost or LightGBM |
| AI | LLM API, structured outputs, bounded tool calling |
| Frontend | React/Next.js or Streamlit |
| Optional retrieval | FAISS/pgvector only if time permits |
| Infrastructure | Docker, GitHub |


| Time | Demo |
| --- | --- |
| 0:00–0:25 | Show a synthetic ₹4.8 lakh transaction that looks LOW under transaction-only scoring. |
| 0:25–1:10 | Reveal the shared device, connected accounts and common beneficiary. Ring probability rises. |
| 1:10–1:50 | Show counterfactual risk: transaction-only → behavioral → network → fund-flow evidence. |
| 1:50–2:30 | Run controlled investigation and show the evidence chain. |
| 2:30–3:15 | Reconstruct the timeline and show the network/fund-flow relationships. |
| 3:15–4:00 | Show transaction-only vs graph-enhanced held-out metrics. |
| 4:00–4:35 | Show false-positive cost, legitimate-network challenge result and net business value from actual test-run results. |
| 4:35–5:00 | Explain architecture, dataset provenance, LLM boundary, human decision and defense-only safety. |


| Priority | Items |
| --- | --- |
| 🔥 MUST HAVE | Transaction baseline; graph model; ring probability; hard negatives; entity/time split; held-out test; PR-AUC/precision/recall; FP/FN cost; business value; evidence graph; human-in-loop; threshold selection; cold-start handling |
| ⭐ SHOULD HAVE | Timeline; controlled investigation AI; counterfactual explanation; legitimate-network explanation; calibration; audit trail; investigation-efficiency experiment; failure fallback; measured latency |
| 🟡 NICE TO HAVE | Historical case similarity; RAG; advanced case retrieval; richer UI; Neo4j; GNN |
| ❌ REMOVE | Free-form autonomous agent; LLM risk scoring; autonomous fund action; full AML platform; multi-LLM architecture; fake real-time claims |


| Field | Final definition |
| --- | --- |
| Name | RingGuard AI |
| Subtitle | Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation |
| Target user | Merchant risk/operations analyst |
| Loss class | Coordinated payment-abuse / mule-account fraud |
| Core AI capability | Gradient-boosted ring-risk model using transaction, behavioral and graph features, followed by controlled evidence investigation and LLM explanation. |
| Unique differentiator | Measured network-level incremental detection value + evidence-backed investigation + explicit false-positive economics + measured investigation efficiency |
| Safety | Strictly defense-only, read-only investigation, human approval required |
