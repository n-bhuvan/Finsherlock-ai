RINGGUARD AI

Product Requirements Document — PRD v1.0

Razorpay AI Buildathon 2026
Track 02 — AI Risk Manager

Product

RingGuard AI

Subtitle

Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation

Target User

Merchant Risk / Risk Operations Analyst

Loss Class

Coordinated Payment Abuse / Mule-Account Fraud

Product Status

Hackathon MVP / Demonstration Prototype

1. Executive Summary

RingGuard AI is a network-aware risk detection and investigation system designed to identify coordinated payment-abuse and mule-account networks that may appear legitimate when individual transactions are analyzed in isolation.

The system combines:

Transaction-level behavioral analysis

Entity and relationship graphs

Gradient-boosted machine learning

Ring-membership probability

Evidence extraction

Multi-hop relationship analysis

Fund-flow tracing

Timeline reconstruction

Controlled read-only investigation AI

Evidence-grounded LLM explanations

Human-in-the-loop decision making

False-positive economic analysis

The core product workflow is:

Detect → Connect → Investigate → Correlate → Explain → Quantify Impact → Human Decision

RingGuard does not attempt to replace a payment processor's existing risk infrastructure. It is designed as a defense-only risk investigation and decision-support layer.

The primary product hypothesis is:

Does network-level context materially improve coordinated abuse detection compared with transaction-only risk scoring, while maintaining an acceptable false-positive cost, and can evidence-first investigation reduce the effort required to review resulting alerts?

RingGuard therefore treats measurable experimentation as part of the product rather than simply adding graph and AI capabilities.

2. Problem Statement

Traditional transaction-level fraud detection can identify suspicious individual behavior, but coordinated abuse can remain difficult to detect when each account or transaction looks reasonable independently.

Examples include:

Multiple accounts sharing a device

Multiple accounts operating from the same IP infrastructure

Apparently unrelated accounts sending funds toward a common beneficiary

Rapid splitting of funds across connected accounts

Newly created accounts performing unusually large transactions

Indirect relationships between apparently unrelated entities

Coordinated activity occurring within suspiciously similar time windows

The existing investigation problem is separate from the detection problem.

After an alert is generated, an analyst may still need to:

Retrieve account information.

Examine transaction history.

Find related accounts.

Investigate shared devices and IPs.

Identify common beneficiaries.

Trace fund flows.

Reconstruct the timeline.

Determine which relationships are relevant.

Document the evidence.

Make a final risk decision.

RingGuard addresses both problems:

Problem A — Detection

Identify coordinated abuse that may not be obvious at transaction level.

Problem B — Investigation

Convert the alert into a traceable evidence chain that allows a human analyst to understand and act on the case efficiently.

3. Product Vision

Build an evidence-first risk intelligence layer that helps risk analysts move from:

"This transaction looks suspicious."

to:

"These entities form a measurable network pattern, these specific relationships support the alert, this is how the activity unfolded, these are the economic implications, and here is the evidence a human analyst can review before making the final decision."

4. Product Goals

4.1 Primary Goals

G1 — Detect coordinated abuse

Identify account-level or cluster-level ring risk using transaction, behavioral and graph information.

G2 — Measure the value of network intelligence

Compare:

Transaction + Behavioral Model

against:

Transaction + Behavioral + Graph Model

using an isolated held-out evaluation.

G3 — Reduce investigation complexity

Automatically retrieve and organize relevant relationships and evidence.

G4 — Make risk decisions explainable

Every important risk conclusion should be supported by structured evidence rather than an unexplained LLM-generated claim.

G5 — Quantify false-positive economics

Measure the economic consequences of incorrectly escalating legitimate activity.

G6 — Maintain human control

The system must remain defense-only and must not autonomously move funds, approve transactions, block transactions, or enforce financial actions.

5. Non-Goals

RingGuard AI will NOT attempt to:

Replace an enterprise fraud platform.

Detect every possible fraud pattern.

Claim universal superiority over existing fraud systems.

Invent a new graph-fraud-detection algorithm.

Use an LLM as the numerical risk classifier.

Allow a free-form autonomous agent to perform unrestricted actions.

Move funds.

Execute payments.

Approve or reject transactions autonomously.

Automatically block customers.

Build a complete AML platform.

Claim production-grade millisecond real-time performance.

Present synthetic data as real Razorpay transaction data.

These boundaries are intentional and should remain visible in the product/demo.

6. Target Users

6.1 Primary User — Risk Analyst

Responsible for reviewing suspicious accounts, transactions or networks.

Needs

Fast understanding of why a case was flagged

Relevant evidence

Relationship discovery

Transaction history

Timeline reconstruction

Network visualization

Ability to request additional evidence

Clear audit trail

Pain Point

Too much time may be spent manually connecting information that already exists across transaction and entity relationships.

6.2 Secondary User — Risk Operations Team

Needs:

Case prioritization

Risk distribution

Network-level visibility

Investigation efficiency metrics

False-positive monitoring

Business impact reporting

7. Core User Journey

Payment / Account Activity

↓

Transaction & Behavioral Analysis

↓

Entity Graph Construction

↓

Ring Risk Model

↓

Ring Probability

↓

Evidence Extraction

↓

Relationship Investigation

↓

Timeline Reconstruction

↓

Controlled Investigation AI

↓

Structured Evidence Package

↓

LLM Explanation

↓

Human Risk Analyst

↓

Approve / Reject / Request More Evidence

↓

Audit Log

This reflects the core architecture defined in the current build specification.

8. Product Capability Stack

9. Functional Requirements

FR-01 — Transaction Analysis

Requirement

The system shall ingest transaction-level information and calculate relevant behavioral features.

Inputs

Examples:

Transaction amount

Timestamp

Sender

Receiver

Transaction frequency

Transaction velocity

Account age

Historical transaction behavior

Transaction direction

Outputs

Transaction-level behavioral features

Risk-related feature values

Behavioral anomaly indicators

Acceptance Criteria

Features are reproducible.

Missing values are handled explicitly.

Feature generation does not use future information.

Features can be associated with an account/entity and investigation case.

10. Behavioral Risk Analysis

The system shall identify patterns such as:

Unusual transaction velocity

Unusual transaction frequency

Sudden behavioral changes

Large-value transactions relative to historical behavior

Rapid movement after incoming funds

Unusual activity shortly after account creation

Behavioral evidence must be treated as contextual evidence rather than an automatic fraud verdict.

11. Entity Graph

FR-02 — Graph Construction

The system shall construct a multipartite entity graph.

Node Types

Customer

Account

Transaction

Device

IP address

Beneficiary

Merchant where applicable

Edge Types

Examples:

Customer → Account

Account → Transaction

Account → Device

Account → IP

Account → Beneficiary

Account → Account

Transaction → Beneficiary

The graph must support relationship traversal and investigation.

The underlying specification explicitly defines customers, accounts, transactions, devices, IPs, beneficiaries and merchants as relevant graph entities.

12. Network Intelligence

The system shall calculate network-level signals including:

Shared device relationships

Shared IP relationships

Common beneficiaries

Connected accounts

Suspicious neighbors

Multi-hop relationships

Community/cluster structure

Coordinated timing

Fund-flow relationships

A single shared attribute must not automatically classify an entity as fraudulent.

13. Ring Detection Model

FR-03 — Ring Risk Prediction

The system shall generate an account or cluster-level:

Ring Membership Probability

rather than relying exclusively on individual transaction risk.

Candidate Model

XGBoost

LightGBM

Feature Categories

Transaction

Amount

Frequency

Velocity

Transaction direction

Transaction timing

Behavioral

Behavioral change

Account age

Historical activity

Relative transaction magnitude

Graph

Number of connected entities

Shared devices

Shared IPs

Common beneficiaries

Suspicious neighbors

Multi-hop connectivity

Community characteristics

Fund Flow

Rapid splitting

Concentration of beneficiaries

Connected fund movement

14. Model Architecture

RingGuard shall support at least two measurable model configurations.

Model A — Baseline

Transaction + Behavioral Features

Purpose:

Determine how well transaction-level intelligence performs without network context.

Model B — Graph Enhanced

Transaction + Behavioral + Graph Features

Purpose:

Determine whether network context provides measurable incremental value.

Final RingGuard

Model B + Evidence/Investigation Workflow

Purpose:

Determine whether the investigation layer improves practical review and decision support.

This comparison is central to the product hypothesis.

15. Threshold Management

The system shall not arbitrarily select a risk threshold based on the final test set.

Required process

Training Data

↓

Candidate Models

↓

Validation Data

↓

Threshold Selection

↓

Threshold Frozen

↓

Untouched Test Data

↓

Final Evaluation

The threshold may be selected using a declared business constraint such as:

Minimum precision

Maximum acceptable false-positive rate

Expected business value

Final test results must not influence threshold selection.

16. Cold-Start Handling

New accounts often lack sufficient behavioral and graph history.

The system shall NOT automatically classify a new account as high risk simply because graph information is unavailable.

Cold-start policy

Use available transaction/behavioral evidence.

Apply conservative scoring.

Mark graph confidence as limited/unavailable.

Increase risk only as additional evidence becomes available.

Evaluate cold-start cases separately.

This prevents missing graph history from being interpreted as suspicious by default.

17. Evidence Engine

FR-04 — Evidence Collection

The evidence engine shall collect the strongest supporting signals for an investigation.

Every evidence item should contain, where applicable:

Evidence type

Related entity

Related transaction

Timestamp

Relationship

Source

Feature/value

Explanation

Confidence/status

Example

Evidence:

Shared Device

Account A

Account B

Relationship:

Both accounts used Device D17

Relevant Period:

T1 → T2

Supporting activity:

Transactions X, Y, Z

Every displayed relationship must be traceable to underlying data.

18. Evidence Ranking

The system should prioritize evidence based on relevance.

Example ranking:

Coordinated fund flow

Multiple connected accounts

Common beneficiary

Suspicious temporal coordination

Shared device

Shared IP

Account-age anomaly

Individual behavioral anomaly

The exact ranking should ultimately be determined by the implementation/evaluation rather than being presented as a universal fraud rule.

19. Timeline Reconstruction

FR-05 — Investigation Timeline

RingGuard shall reconstruct relevant events chronologically.

Example:

10:02

Account created

10:17

First large incoming payment

10:21

Funds transferred to Account B

10:23

Funds transferred to Account C

10:25

Shared device relationship discovered

10:31

Common beneficiary identified

10:36

Historical suspicious connection identified

10:40

Ring investigation completed

The purpose is to allow an analyst to understand the case without manually correlating timestamps.

20. Controlled Investigation AI

FR-06 — Investigation Agent

The investigation agent shall be bounded to approved, read-only operations.

Approved operations

get_account()

get_transactions()

find_related_accounts()

find_shared_devices()

find_shared_ips()

find_common_beneficiaries()

trace_fund_flow()

reconstruct_timeline()

get_risk_features()

Agent Restrictions

The agent shall NOT:

Modify risk scores

Move funds

Execute payments

Approve transactions

Block transactions

Modify customer data

Issue autonomous enforcement

Access unauthorized information

Every tool call shall be:

Permission checked

Logged

Associated with the case

Associated with resulting evidence

This bounded approach replaces the unrestricted autonomous-agent concept in the earlier design.

21. LLM Explanation Layer

FR-07 — Evidence-Grounded Explanation

The LLM shall operate after detection and investigation.

LLM Inputs

Only structured information such as:

Model output

Risk probability

Important features

Graph relationships

Evidence objects

Timeline

Investigation results

LLM Outputs

The LLM may generate:

Why the case was flagged

Strongest evidence chain

Potential benign explanations

Concise investigator summary

Suggested additional evidence to review

Critical restriction

The LLM must NOT:

Calculate the numerical risk score

Override the ML model

Invent evidence

Make the final enforcement decision

The specification explicitly defines the LLM as a post-hoc explanation layer.

22. LLM Failure Fallback

If the LLM fails:

ML + Graph Results

↓

Structured Evidence

↓

Template-Based Summary

Detection and investigation must remain usable without the LLM.

This ensures that the AI explanation layer is not a single point of failure.

23. Counterfactual Explanation

RingGuard shall demonstrate how risk changes as additional evidence becomes available.

Example:

Transaction-only

↓

LOW

+ Behavioral evidence

↓

MEDIUM

+ Network relationships

↓

HIGH

+ Coordinated fund-flow evidence

↓

HIGH CONFIDENCE

These states are illustrative and must not be presented as actual model results unless produced by the implemented system.

24. Legitimate-Network Protection

The system must explicitly test legitimate cases that resemble suspicious networks.

Required hard-negative scenarios

Family members sharing a device

Employees sharing an office IP

Businesses sharing suppliers

Legitimate common beneficiaries

High-volume legitimate merchants

Normal recurring payment relationships

The system should determine whether surrounding behavioral and transaction context supports legitimate activity before escalating.

A dedicated:

Legitimate Network Challenge Set

shall be included in evaluation.

25. Dataset Requirements

The project shall use a combination of:

Dataset A — Public Fraud Benchmark

Purpose:

General fraud-risk modeling and baseline comparison.

Dataset B — Synthetic Razorpay-Shaped Dataset

Purpose:

Represent Indian payment and coordinated abuse-ring scenarios that may not exist in public benchmarks.

Dataset C — Hard Negatives

Purpose:

Prevent simplistic pattern matching.

Dataset D — Held-Out Test Set

Purpose:

Final unbiased evaluation.

Synthetic data must be explicitly disclosed as synthetic. The detector should not simply memorize hand-coded generation rules.

26. Synthetic Data Entities

Synthetic data should include:

Customers

Accounts

Transactions

Devices

IP addresses

Beneficiaries

Merchants

Appropriate KYC/status attributes

Historical investigation references where needed

The dataset must include:

Legitimate activity

Individual suspicious activity

Coordinated abuse-ring activity

Legitimate look-alike networks

27. Required Abuse Scenarios

Scenario 1 — Shared Device Ring

Multiple accounts share a device and exhibit coordinated behavior.

Scenario 2 — Common Beneficiary Ring

Multiple apparently independent accounts route funds toward a common beneficiary.

Scenario 3 — Rapid Fund Distribution

A large incoming payment is rapidly split across connected accounts.

Scenario 4 — Historical Connection

A new account connects through infrastructure to a previously suspicious entity.

Scenario 5 — Combined Ring

Several individually weak signals combine into a stronger network-level assessment.

Scenario 6 — Legitimate Look-Alike

Shared infrastructure exists, but surrounding behavior remains legitimate.

These scenarios are explicitly required by the existing specification.

28. Data Leakage Prevention

The evaluation pipeline shall be leakage resistant.

Requirements:

Time-based splitting where appropriate

Entity-based separation where required

No account leakage

No device leakage

No IP leakage where the prediction setup requires isolation

Final test data must remain untouched

Detection logic must be frozen before final test evaluation

29. Evaluation Framework

RingGuard must evaluate both:

Detection Performance

Does graph context improve detection?

Investigation Performance

Does evidence-first investigation improve review efficiency?

These should be treated as separate experiments.

30. Detection Metrics

Primary Metrics

PR-AUC

Primary metric because fraud/abuse datasets can be highly imbalanced.

Precision

Percentage of escalated cases that are actually relevant.

Recall

Percentage of relevant abuse cases detected.

False-Positive Cost

Economic cost of incorrectly escalating legitimate cases.

Fraud ₹ Prevented

Estimated monetary value of abuse prevented under the chosen operating policy.

Secondary Metrics

F1

ROC-AUC

Calibration

Brier score

False-positive rate

False-negative cost

Latency

Coverage

The metric priorities follow the current build specification.

31. Investigation Metrics

The investigation layer shall be evaluated using:

Average investigation time

Median investigation time

Investigation completion rate

Tool-call success rate

Evidence retrieval success

Relevant relationships discovered

Report generation success

Number of manual steps

Human-review effort

32. Investigation Efficiency Experiment

RingGuard-assisted investigation shall be compared with a baseline investigation workflow.

No reduction in analyst time should be claimed unless it is actually measured.

33. Business Value Model

RingGuard shall expose assumptions behind business-value calculations.

Fraud Loss Avoided

Value of true-positive abuse prevented under the selected operating policy.

Friction Cost

False Positives × Cost per False Positive

Investigation Cost

Escalated Cases × Estimated Analyst Cost per Case

Net Business Value

Fraud Loss Avoided

− Friction Cost

− Investigation Cost

Optional extensions:

Missed-fraud cost

Customer churn

Support cost

Resolution cost

Legitimate transaction value

Every assumption must be visible in the dashboard/demo.

34. Case Management

Each investigation case shall contain:

Case ID

Entity / Account

Ring Probability

Risk Level

Primary Evidence

Network

Timeline

Transactions

Investigation Actions

LLM Summary

Business Impact

Human Decision

Audit Trail

35. Risk Levels

The UI may present:

Low

Medium

High

However, the UI must clearly distinguish:

Model probability

from:

Operational decision threshold

The probability itself should not be presented as a guarantee of fraud.

36. Dashboard Requirements

The main dashboard shall display:

Overview

Active cases

Risk distribution

Networks detected

High-risk cases

Case Queue

Case ID

Entity

Risk level

Ring probability

Evidence count

Investigation status

Case Detail

Risk probability

Top evidence

Graph

Timeline

Transactions

Fund-flow relationships

Counterfactual explanation

LLM investigation summary

Business impact

Human decision

Audit

Tool calls

Evidence retrieval

Model version

Investigation actions

Final decision

The current specification identifies these dashboard elements as the target final interface.

37. Evidence Graph UX

The graph view shall allow an analyst to understand:

Account A

│

├── Device D1

│

├── IP X

│

├── Account B

│ │

│ └── Beneficiary Z

│

└── Account C

│

└── Beneficiary Z

The UI should distinguish relationship types.

The purpose is not visual complexity; it is evidence comprehension.

38. Timeline UX

The timeline should show:

Account creation

Significant transactions

Transfers

Relationship discoveries

Device/IP connections

Beneficiary relationships

Historical connections

Investigation actions

Final assessment

39. Human Decision Controls

The final analyst interface shall provide:

Approve / Clear

Case does not require escalation.

Reject / Escalate

Case is considered sufficiently suspicious for the applicable workflow.

Request More Evidence

Additional investigation is required.

The system should record:

Decision

Analyst

Timestamp

Evidence reviewed

Optional rationale

The final decision must remain human controlled.

40. Audit Requirements

Important actions shall be logged.

Audit records should include:

Case ID

Model version

Risk output

Investigation tool call

Tool parameters where appropriate

Tool result

Evidence generated

LLM explanation generation

Human decision

Timestamp

41. Security Requirements

RingGuard is strictly defense-only.

The system shall provide:

Read-only investigative access

Permission checking

Audit logging

Human approval

No fund movement

No autonomous transaction enforcement

No silent evidence invention

These safety boundaries are explicitly part of the existing specification.

42. Failure Handling

Database Failure

Retry

Log failure

Continue where possible

Surface unavailable evidence

Missing Evidence

Mark unavailable

Do not infer it

Request alternative evidence

Tool Failure

Retry where appropriate

Use approved alternative

Log failure

LLM Failure

Use deterministic/template summary

Graph Failure

Fall back to available transaction/behavioral evidence

Mark network evidence unavailable

Missing Historical Data

Explicitly label evidence limitations

43. No-Hallucination Requirement

The system must never fabricate:

Transactions

Relationships

Devices

IP addresses

Beneficiaries

Historical cases

Risk evidence

Investigation results

If information is unavailable, the UI must state:

Evidence unavailable

rather than generating an assumed answer.

44. Technology Requirements

The graph/database choice should remain pragmatic: NetworkX is preferred initially, with Neo4j only if it materially improves the implementation or demo.

45. API-Level Product Requirements

Detection API

Input

{

"account_id": "A123",

"transaction_id": "T456"

}

Output

{

"ring_probability": 0.91,

"risk_level": "HIGH",

"model_version": "ringguard_v1",

"top_features": [],

"network_available": true

}

46. Investigation API

The investigation layer should support requests such as:

Get account

Get transactions

Find related accounts

Find shared devices

Find shared IPs

Find common beneficiaries

Trace fund flow

Reconstruct timeline

Get risk features

Each response must be structured so that evidence can be linked back to its source.

47. Evidence Object

A conceptual evidence object should contain:

{

"evidence_id": "E123",

"type": "SHARED_DEVICE",

"entities": ["A123", "A456"],

"source": "device_relationship",

"timestamp_range": ["T1", "T2"],

"description": "Accounts share device D17",

"supporting_records": ["R1", "R2"],

"availability": "verified"

}

48. Explainability Requirements

For each high-risk case, the system should answer:

Why was this case flagged?

Provide major model signals.

What network evidence supports the case?

Show relevant relationships.

What happened?

Show timeline.

What could explain this legitimately?

Surface possible benign explanations.

What additional evidence should the analyst review?

Provide bounded investigation suggestions.

49. Product Differentiation

RingGuard should NOT be marketed as:

"An AI fraud detector."

Instead:

"A network-aware abuse-ring detection and evidence-first risk investigation layer that experimentally measures the incremental value of network context over transaction-level risk scoring."

The defensible differentiators are:

Explicit transaction-only baseline

Experimental isolation of graph contribution

False-positive economics

Traceable evidence

Bounded investigation AI

Human-controlled decisions

Measured investigation efficiency

This positioning is directly aligned with the current specification.

50. Product Success Criteria

RingGuard will be considered successful if:

Detection

Graph-enhanced model is evaluated against transaction-only baseline.

Evaluation uses leakage-resistant splitting.

Held-out test set remains untouched.

Precision/recall/PR-AUC are measured.

FP/FN economics are calculated.

Data

Synthetic data is clearly disclosed.

Legitimate look-alikes are included.

Hard negatives are included.

Abuse scenarios are represented.

Investigation

Relevant relationships can be discovered.

Evidence can be traced.

Timeline can be reconstructed.

Investigation efficiency can be measured.

AI

LLM does not determine numerical risk.

LLM explanations are evidence-grounded.

LLM failure has deterministic fallback.

Safety

No autonomous financial action.

Human decision required.

All important actions auditable.

Demo

Transaction-only → network context → evidence transition is visually obvious.

Actual test results are shown.

Business assumptions are visible.

Synthetic data is labeled.

51. MVP Scope

MUST HAVE

Transaction/behavioral baseline

Synthetic dataset generator

Abuse-ring scenarios

Legitimate-network challenge set

Entity graph

Graph features

Ring ML model

Ring probability

Time/entity-aware evaluation

Held-out test set

Transaction vs graph comparison

Threshold methodology

Precision/recall/PR-AUC

FP/FN cost

Business-value calculation

Evidence graph

Human-in-the-loop decision

Cold-start policy

These correspond closely to the highest-priority items in the existing build specification.

52. SHOULD HAVE

Timeline

Controlled investigation AI

Counterfactual explanation

Legitimate-network explanation

Calibration

Audit trail

Investigation-efficiency experiment

Failure fallback

Measured latency

53. NICE TO HAVE

Historical case similarity

RAG

Advanced case retrieval

Richer UI

Neo4j

GNN

Advanced graph analytics

54. Explicitly Remove

The following should NOT be built unless requirements materially change:

Free-form autonomous agent

LLM risk scoring

Autonomous fund action

Full AML platform

Multi-LLM architecture

Fake real-time claims

55. Implementation Roadmap

Phase 1 — Data

Build independent synthetic generator

Load public benchmark

Create legitimate cases

Create abuse-ring cases

Create hard negatives

Create held-out test set

Phase 2 — Graph

Build entities

Build relationships

Implement traversal

Implement community detection

Generate graph features

Phase 3 — ML

Build transaction baseline

Build graph-enhanced model

Perform validation

Select threshold

Freeze model

Run final test

Phase 4 — Economics

Calculate FP cost

Calculate FN cost

Calculate fraud loss avoided

Calculate investigation cost

Calculate net business value

Phase 5 — Investigation

Evidence engine

Fund-flow tracing

Timeline

Controlled tools

Investigation agent

Audit logs

Phase 6 — Explanation

Structured evidence package

LLM summary

Counterfactual explanation

Deterministic fallback

Phase 7 — Dashboard

Case queue

Risk overview

Graph

Timeline

Evidence

Business impact

Human decision

Audit trail

Phase 8 — Demo

Freeze model

Freeze test set

Run final evaluation

Capture actual metrics

Validate demo scenario

Verify all claims

The current specification follows essentially this build order.

56. Five-Minute Demo Requirements

0:00–0:25 — The Blind Spot

Show a synthetic ₹4.8 lakh transaction.

Transaction-only model:

LOW

Explain:

"Viewed independently, this transaction does not provide enough evidence for a high-risk decision."

0:25–1:10 — Reveal the Network

Reveal:

Shared device

Connected accounts

Common beneficiary

Coordinated activity

Ring probability increases.

1:10–1:50 — Counterfactual

Show:

Transaction-only

↓

LOW

+ Behavioral

↓

MEDIUM

+ Network

↓

HIGH

+ Fund Flow

↓

HIGH Confidence

Only use actual values if produced by the system.

1:50–2:30 — Investigation AI

Run bounded investigation operations.

Show:

Related accounts

Device relationship

IP relationship

Beneficiary

Fund flow

2:30–3:15 — Evidence + Timeline

Show the graph and chronological activity.

The judge should understand the entire case without reading raw transactions manually.

3:15–4:00 — Experimental Proof

Show:

Transaction-only vs Graph-enhanced

Metrics:

PR-AUC

Precision

Recall

FP cost

Fraud ₹ prevented

4:00–4:35 — Business Impact

Show:

False-positive cost

Legitimate-network challenge

Investigation efficiency

Net business value

Only show measured results.

4:35–5:00 — Trust & Safety

Finish with:

Synthetic data disclosure

Architecture

Evidence traceability

LLM boundary

Human decision

Defense-only design

The five-minute structure is based on the existing demonstration sequence.

57. Key Product Risks

Risk 1 — Synthetic Data Looks Unrealistic

Mitigation

Use multiple independent scenarios, realistic distributions, hard negatives and a public benchmark.

Risk 2 — Data Leakage

Mitigation

Use time/entity-aware splitting and untouched final test data.

Risk 3 — Graph Features Simply Memorize Synthetic Rules

Mitigation

Develop data generation and detection logic independently.

Risk 4 — False Positives From Shared Infrastructure

Mitigation

Include legitimate-network challenge cases.

Risk 5 — LLM Hallucination

Mitigation

LLM receives only structured evidence and cannot create evidence. Provide deterministic fallback.

Risk 6 — Overclaiming Novelty

Mitigation

Do not claim invention of graph fraud detection. Position the contribution around experimentally measured incremental network value and evidence-first investigation.

Risk 7 — Overbuilding

Mitigation

Prioritize ML/evaluation/business evidence before RAG, GNN, Neo4j or elaborate agent behavior.

58. Product Principles

Principle 1 — Evidence Before Explanation

The system must first establish structured evidence and only then generate natural-language explanations.

Principle 2 — Measurement Before Claims

No performance or business improvement should be claimed without an actual experiment.

Principle 3 — Network Context, Not Network Bias

Shared infrastructure is evidence, not proof of fraud.

Principle 4 — Human Before Enforcement

The system supports human decisions rather than autonomously enforcing them.

Principle 5 — Explicit Uncertainty

Missing data, cold-start conditions and unavailable evidence must be visible.

Principle 6 — Simple Architecture Before Fancy AI

A reliable gradient-boosted model with strong evaluation is more important than unnecessary GNN/RAG/agent complexity.

59. Final Product Definition

60. Final Product Statement

RingGuard AI is a network-aware abuse-ring detection and evidence-first risk investigation system that identifies coordinated payment abuse using transaction, behavioral and graph intelligence, then converts the resulting risk signal into traceable evidence, timelines and analyst-readable explanations while keeping the final decision under human control.

Its central claim is not that graph analytics or AI investigation are inherently new.

Its strongest defensible claim is:

RingGuard experimentally measures whether network context provides meaningful incremental value over transaction-level risk scoring, quantifies the economic cost of false positives, and turns network-level risk signals into traceable evidence that can improve human investigation.

That positioning keeps the project technically ambitious while avoiding unsupported novelty or performance claims.


| Layer | Responsibility |
| --- | --- |
| Transaction Engine | Analyze transaction behavior |
| Behavioral Engine | Detect abnormal behavioral changes |
| Entity Graph | Represent relationships |
| Ring ML Model | Estimate ring-membership probability |
| Evidence Engine | Extract supporting evidence |
| Fund-Flow Engine | Trace connected money movement |
| Timeline Engine | Reconstruct events |
| Investigation AI | Select bounded read-only investigation operations |
| LLM Layer | Explain structured evidence |
| Human Decision | Final risk action |
| Audit Layer | Record important actions and evidence |


| Metric | Baseline | RingGuard |
| --- | --- | --- |
| Median case completion time | Measure | Measure |
| Evidence retrieval success | Measure | Measure |
| Relevant relationships discovered | Measure | Measure |
| Case completion rate | Measure | Measure |
| Manual investigation steps | Measure | Measure |


| Component | Recommended Technology |
| --- | --- |
| Backend | Python + FastAPI + Pydantic |
| Database | PostgreSQL |
| Graph | NetworkX initially |
| Optional Graph DB | Neo4j |
| ML | Pandas + scikit-learn + XGBoost/LightGBM |
| LLM | LLM API + structured outputs |
| Frontend | React/Next.js or Streamlit |
| Optional Retrieval | FAISS / pgvector |
| Deployment | Docker |
| Repository | GitHub |


| Field | Definition |
| --- | --- |
| Product | RingGuard AI |
| Subtitle | Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation |
| User | Merchant Risk / Operations Analyst |
| Problem | Coordinated payment abuse and mule-account networks |
| Detection | Transaction + behavioral + graph ML |
| Model | XGBoost / LightGBM |
| Output | Ring-membership probability |
| Investigation | Evidence-first, read-only |
| AI Agent | Bounded investigation tool-calling |
| LLM | Post-hoc evidence explanation |
| Graph | Multipartite entity graph |
| Core Experiment | Transaction-only vs graph-enhanced |
| Primary Metrics | PR-AUC, precision, recall, FP cost |
| Business Metric | Net business value |
| Investigation Metric | Measured review efficiency |
| Data | Public benchmark + disclosed synthetic data + hard negatives |
| Safety | Defense-only |
| Final Decision | Human analyst |
| Primary Differentiator | Measured incremental network value + evidence-backed investigation |
