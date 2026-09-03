# RINGGUARD AI

TECHNICAL STACK & ARCHITECTURE DOCUMENT — v1.0

Razorpay AI Buildathon 2026 | Track 02 — AI Risk Manager

This document records the complete recommended technology stack, architecture, project structure, implementation boundaries, and rationale for RingGuard AI.

# 1. Recommended Stack — Executive View

RINGGUARD AI
 │
 ┌──────────┴──────────┐
 │ │
 React / Next.js FastAPI
 Analyst Dashboard Backend API
 │ │
 └──────────┬──────────┘
 │
 ┌──────────┴──────────┐
 │ │
 PostgreSQL NetworkX
 Transaction Data Evidence Graph
 │ │
 └──────────┬──────────┘
 │
 Feature Engine
 │
 ┌──────────┴──────────┐
 │ │
 XGBoost Graph Features
 Risk Classification Network Intelligence
 │ │
 └──────────┬──────────┘
 │
 Evidence Engine
 │
 Investigation Tools
 │
 Controlled Agent
 │
 LLM API
 │
 Evidence Explanation
 │
 Human Analyst

# 2. Final Technology Stack

# 3. Core Architecture Principle

RingGuard should be implemented as a modular monolith rather than microservices. The architecture should keep the frontend, backend, graph, ML, evidence, investigation, and explanation responsibilities clearly separated while avoiding unnecessary deployment and networking complexity.

Next.js Frontend
 │
 ▼
FastAPI Backend
 │
 ┌─────┼─────────────────────────────────┐
 ▼ ▼ ▼ ▼ ▼
DB Graph ML Evidence Audit
 NetworkX XGBoost Engine Log
 │ │ │
 └────────────┼────────────┘
 ▼
 Investigation AI
 │
 ▼
 LLM
 │
 ▼
 Human Analyst

# 4. Frontend Stack

## 4.1 Next.js

Use Next.js as the primary frontend application framework.

### Responsibilities

Application routing

Page structure

Dashboard rendering

Case investigation interface

Analytics screens

Audit interface

API integration

## 4.2 React

Use React for the component model and interactive analyst workspace.

## 4.3 TypeScript

Use TypeScript throughout the frontend to keep case, evidence, graph, risk, timeline, and API response structures explicit.

## 4.4 Tailwind CSS

Use Tailwind for the dark enterprise/SOC-style visual system, spacing, layout, responsive behavior, and rapid UI iteration.

## 4.5 shadcn/ui

Use shadcn/ui for reusable interface primitives such as dialogs, tabs, tables, badges, dropdowns, tooltips, buttons, drawers, and command/search components. Customize the components to match RingGuard's visual identity.

## 4.6 Lucide Icons

Use Lucide-style line icons for entity types and interface actions.

# 5. Frontend Visualization Stack

## 5.1 React Flow — Network Graph

React Flow should render the interactive financial evidence graph in the browser.

NetworkX
 ↓
Graph JSON
 ↓
FastAPI
 ↓
React
 ↓
React Flow
 ↓
Interactive Evidence Graph

### Graph Interactions

Click node → inspect entity

Click edge → show supporting evidence

Expand network → reveal next-hop relationships

Filter by device/IP/beneficiary/fund flow

Focus case → hide unrelated entities

## 5.2 Recharts — Analytics

Use Recharts for lightweight product analytics and evaluation visualizations.

PR-AUC comparison

Precision

Recall

Risk trends

Fraud ₹ prevented

False-positive cost

False-negative cost

Investigation time

# 6. Backend Stack

## 6.1 FastAPI

FastAPI is the recommended backend framework because RingGuard's ML, graph, evidence and investigation components are Python-based.

FastAPI
 ├── /risk
 ├── /cases
 ├── /accounts
 ├── /transactions
 ├── /networks
 ├── /evidence
 ├── /investigation
 ├── /timeline
 └── /analytics

## 6.2 Pydantic

Use Pydantic for API request/response validation and structured evidence, risk, case, investigation and LLM output schemas.

## 6.3 SQLAlchemy

Use SQLAlchemy as the PostgreSQL ORM/data-access layer.

## 6.4 Alembic

Use Alembic for database migrations so the database schema can evolve reproducibly.

# 7. Database — PostgreSQL

PostgreSQL is the primary persistent datastore.

## Data to Store

Customers

Accounts

Transactions

Devices

IP addresses

Beneficiaries

Merchants

Cases

Evidence objects

Investigation logs

Model outputs

Human decisions

Audit records

PostgreSQL
 ↑
SQLAlchemy
 ↑
FastAPI

PostgreSQL should remain the source of truth for persistent application data. NetworkX should operate as the graph-computation layer rather than becoming the primary persistent datastore.

# 8. Graph Layer — NetworkX

Use NetworkX initially for graph construction, traversal and graph-derived features.

## Graph Node Types

Customer

Account

Transaction

Device

IP

Beneficiary

Merchant

## Graph Relationship Types

Customer → Account

Account → Transaction

Account → Device

Account → IP

Account → Beneficiary

Account → Account

Transaction → Beneficiary

## Graph Operations

Multi-hop traversal

Connected-component analysis

Community/cluster analysis

Neighbor analysis

Relationship discovery

Graph-derived feature generation

Fund-flow path analysis

# 9. Why Not Neo4j Initially?

Neo4j should not be the starting point for the hackathon. NetworkX plus PostgreSQL is sufficient for the MVP and reduces infrastructure complexity.

Neo4j can be introduced later if graph query complexity or scale becomes a genuine implementation bottleneck. It should not be added merely to make the architecture look more sophisticated.

# 10. Machine Learning Stack

## 10.1 XGBoost

Use XGBoost as the primary RingGuard risk model.

The expected input is a tabular feature matrix containing transaction, behavioral and graph-derived features.

Transactions
 │
 ├── Amount
 ├── Velocity
 ├── Frequency
 ├── Timing
 ├── Account Age
 └── Behavioral Change
 │
 ▼
 Behavioral Features
 │
 +
 Graph Features
 │
 ▼
 XGBoost
 │
 ▼
 Ring Probability

## 10.2 scikit-learn

Preprocessing

Train/validation/test splitting

Evaluation metrics

Threshold selection

Calibration

Precision/recall analysis

Confusion matrices

## 10.3 Pandas + NumPy

Use Pandas and NumPy for data generation, cleaning, transformation, feature engineering, evaluation tables, and experiment analysis.

## 10.4 Joblib

Use Joblib to persist the trained model and related preprocessing artifacts when appropriate.

models/
 ringguard_xgb_v1.joblib

# 11. Model Architecture — Two Required Experiments

## Baseline A

Transaction + behavioral features.

## Model B

Transaction + behavioral + graph features.

## Final RingGuard

Model B + evidence/investigation workflow.

Baseline A
Transaction + Behavioral
 ↓
 XGBoost
 ↓
Baseline Results

Model B
Transaction + Behavioral + Graph
 ↓
 XGBoost
 ↓
Graph-Enhanced Results

Final RingGuard
Graph Model
 +
Evidence / Investigation
 ↓
Operational Results

# 12. Explainability — SHAP

SHAP should be added to explain model feature contributions without giving the LLM responsibility for calculating risk.

XGBoost
 ↓
Risk Probability
 +
SHAP
 ↓
Top Model Contributors
 ↓
Structured Evidence
 ↓
LLM Explanation

Example UI content:

Rapid fund splitting +0.21
Common beneficiary +0.18
Shared device +0.14
Coordinated timing +0.11
Account age +0.08

The exact values must come from the implemented model and should not be hard-coded as final results.

# 13. Synthetic Data Stack

Use Python, Faker, NumPy, Pandas and custom scenario generators.

generate_legitimate_accounts()

generate_shared_device_ring()

generate_common_beneficiary_ring()

generate_rapid_distribution_ring()

generate_historical_connection()

generate_combined_ring()

generate_legitimate_network()

## Required Dataset Categories

Legitimate activity

Individual suspicious activity

Coordinated abuse-ring activity

Legitimate look-alike networks

Hard negatives

Held-out test data

## Important Data Principle

The synthetic data generator and detection logic should be developed independently so that the model is not simply learning the generator's hand-coded rules.

# 14. Investigation AI Stack

RingGuard should use a bounded tool-calling layer rather than a free-form autonomous agent.

## Approved Tools

get_account()
get_transactions()
find_related_accounts()
find_shared_devices()
find_shared_ips()
find_common_beneficiaries()
trace_fund_flow()
reconstruct_timeline()
get_risk_features()

## Tool Execution Flow

Analyst
 ↓
Investigation Agent
 ↓
Permission Check
 ↓
Approved Tool
 ↓
Structured Result
 ↓
Evidence Object
 ↓
Audit Log

## Restrictions

No risk-score modification

No fund movement

No payment execution

No autonomous approval

No autonomous blocking

No customer-data modification

No autonomous enforcement

No unauthorized data access

# 15. LLM Stack

The LLM is a post-hoc evidence explanation layer.

## LLM Input

Ring probability

Model features/SHAP results

Graph relationships

Evidence objects

Timeline

Investigation results

## LLM Output

Why the case was flagged

Strongest evidence chain

Potential benign explanations

Concise investigator summary

Suggested additional evidence to review

## LLM Restrictions

Must not calculate numerical risk

Must not override ML output

Must not invent evidence

Must not make the final enforcement decision

## 15.1 Structured LLM Output

{
 "summary": "...",
 "strongest_evidence": [],
 "benign_explanations": [],
 "additional_evidence": []
}

## 15.2 LLM Provider Abstraction

LLMProvider
 ├── OpenAIProvider
 ├── GeminiProvider
 └── OtherProvider

The application should call an internal interface such as generate_investigation_summary(evidence) rather than hard-coding provider-specific logic throughout the backend.

# 16. LLM Failure Fallback

ML + Graph Results
 ↓
Structured Evidence
 ↓
Template-Based Summary

The application must remain capable of detection and investigation even if the LLM call fails.

# 17. Evidence Engine

The evidence engine converts graph, transaction and model outputs into structured, traceable evidence.

## Evidence Fields

Evidence ID

Evidence type

Related entities

Supporting transactions

Timestamp/range

Source

Description

Availability/status

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

# 18. Timeline Engine

The timeline engine reconstructs relevant events from underlying transaction and relationship records.

Account creation

Large incoming payment

Rapid transfers

Linked-account discovery

Shared device/IP discovery

Beneficiary relationship

Historical suspicious connection

Final risk assessment

# 19. Risk and Business Analytics

## Detection Metrics

PR-AUC

Precision

Recall

F1

ROC-AUC

Calibration/Brier score

False-positive rate

False-positive cost

False-negative cost

Fraud ₹ prevented

Latency

Coverage

## Investigation Metrics

Median case completion time

Evidence retrieval success

Relevant relationships discovered

Case completion rate

Manual investigation steps

Tool-call success

Report generation success

## Business Value

Fraud Loss Avoided
− False-Positive Friction Cost
− Investigation Cost
=
Net Business Value

# 20. Frontend Page Architecture

frontend/
├── app/
│ ├── page.tsx # Overview
│ ├── cases/
│ ├── networks/
│ ├── analytics/
│ └── audit/
│
├── components/
│ ├── dashboard/
│ ├── cases/
│ ├── graph/
│ ├── timeline/
│ ├── evidence/
│ ├── investigation/
│ └── analytics/
│
├── lib/
└── types/

## Primary Pages

Overview Dashboard

Case Queue

Case Investigation

Network Explorer

Analytics

Audit Trail

# 21. Backend Architecture

backend/
└── app/
 ├── api/
 │ ├── risk.py
 │ ├── cases.py
 │ ├── accounts.py
 │ ├── transactions.py
 │ ├── networks.py
 │ ├── evidence.py
 │ ├── investigation.py
 │ ├── timeline.py
 │ └── analytics.py
 │
 ├── models/
 ├── schemas/
 ├── services/
 ├── investigation/
 ├── evidence/
 ├── timeline/
 └── audit/

# 22. ML Architecture

ml/
├── data/
├── generators/
├── features/
├── graph/
├── models/
├── evaluation/
├── experiments/
└── notebooks/

## Recommended Responsibilities

# 23. Complete Repository Structure

ringguard-ai/
│
├── frontend/
│ ├── app/
│ ├── components/
│ │ ├── dashboard/
│ │ ├── cases/
│ │ ├── graph/
│ │ ├── timeline/
│ │ ├── evidence/
│ │ └── investigation/
│ ├── lib/
│ └── types/
│
├── backend/
│ ├── app/
│ │ ├── api/
│ │ ├── models/
│ │ ├── schemas/
│ │ ├── services/
│ │ ├── investigation/
│ │ ├── evidence/
│ │ ├── timeline/
│ │ └── audit/
│ └── tests/
│
├── ml/
│ ├── data/
│ ├── generators/
│ ├── features/
│ ├── graph/
│ ├── models/
│ ├── evaluation/
│ ├── experiments/
│ └── notebooks/
│
├── models/
│ └── ringguard_xgb_v1.joblib
│
├── scripts/
├── docker/
│
├── docs/
│ ├── PRD.md
│ ├── ARCHITECTURE.md
│ └── API.md
│
├── docker-compose.yml
├── README.md
└── .env.example

# 24. API Architecture

Frontend
 ↓
Next.js API Client
 ↓
FastAPI
 ├── Risk
 ├── Cases
 ├── Networks
 ├── Evidence
 ├── Investigation
 ├── Timeline
 └── Analytics
 ↓
 Services
 ↓
PostgreSQL / NetworkX / ML / LLM

## Core API Groups

# 25. Testing Stack

## Pytest

Unit tests

Feature-engineering tests

Graph tests

Evidence tests

Investigation-tool tests

API tests

## HTTPX

Use HTTPX for FastAPI endpoint/integration testing.

## Critical Tests

No fabricated evidence.

Investigation tools cannot perform write operations.

Risk model returns valid probabilities.

Cold-start accounts follow conservative policy.

Graph relationships are traceable.

LLM output cannot overwrite risk probability.

Final human decision is recorded.

# 26. Security Architecture

User
 ↓
Frontend
 ↓
FastAPI
 ↓
Permission Layer
 ↓
Read-only Investigation Tools
 ↓
Evidence
 ↓
Audit Log

Permission checks for every investigation tool

Read-only investigation

Audit logging

Human approval

No fund movement

No autonomous enforcement

No silent evidence invention

# 27. Deployment Stack

For a hackathon, choose the deployment provider your team can operate reliably. Avoid spending build time on infrastructure complexity.

# 28. Environment Configuration

.env.example

DATABASE_URL=
LLM_API_KEY=
MODEL_PATH=
APP_ENV=development
API_BASE_URL=

Never commit real API keys, database passwords, or credentials to GitHub.

# 29. Technologies Explicitly Not Recommended Initially

These exclusions are deliberate. The goal is a reliable end-to-end product rather than a technology showcase.

# 30. Optional Future Stack

Only after the MVP works should the following be considered:

Neo4j for larger/more complex graph workloads

GNN for a future graph-learning experiment

RAG for historical case retrieval

FAISS/pgvector for semantic case search

MLflow for experiment tracking

Advanced authentication/authorization

Background job queues for larger-scale workloads

# 31. Data Flow

Payment Event
 ↓
Transaction / Behavioral Feature Engine
 +
Entity Graph
 ↓
Graph Features
 ↓
XGBoost
 ↓
Ring Probability
 ↓
Evidence Engine
 ├── Device / IP
 ├── Beneficiary
 ├── Fund Flow
 └── Multi-hop
 ↓
Timeline Engine
 ↓
Controlled Investigation AI
 ↓
Structured Evidence
 ↓
LLM Explanation
 ↓
Human Risk Analyst
 ├── Clear
 ├── Escalate
 └── Request More Evidence
 ↓
Audit Log

# 32. Recommended Build Order

1. Set up repository, Docker, frontend and FastAPI.

2. Create PostgreSQL schema.

3. Build independent synthetic data generator.

4. Create legitimate, suspicious, ring and hard-negative datasets.

5. Build NetworkX graph construction.

6. Build transaction and behavioral features.

7. Build graph-derived features.

8. Train transaction-only XGBoost baseline.

9. Train graph-enhanced XGBoost model.

10. Build leakage-resistant evaluation.

11. Select threshold on validation data.

12. Freeze final test set and run final evaluation.

13. Implement FP/FN cost and net-business-value calculations.

14. Build evidence engine.

15. Build timeline engine.

16. Build bounded investigation tools.

17. Add investigation audit logging.

18. Add SHAP explanations.

19. Add structured LLM explanation with deterministic fallback.

20. Build case investigation UI.

21. Build graph visualization with React Flow.

22. Build analytics dashboard.

23. Polish UI and prepare demo.

# 33. Technology Decision Summary

# 34. Final Architecture Decision

The recommended RingGuard architecture is intentionally pragmatic:

NEXT.JS + REACT + TYPESCRIPT
 │
 ▼
 FASTAPI
 │
 ┌─────┼─────┐
 ▼ ▼ ▼
POSTGRES NETWORKX ML
 │ │
 └──┬───┘
 ▼
 EVIDENCE ENGINE
 │
 ▼
 CONTROLLED INVESTIGATION
 │
 ▼
 LLM
 │
 ▼
 HUMAN RISK ANALYST
 │
 ▼
 AUDIT LOG

This architecture gives RingGuard a clear separation of responsibilities: ML determines numerical risk, graph and investigation services discover and organize evidence, the LLM explains verified evidence, and the human analyst makes the final decision.

# 35. Final Recommendation

For the Razorpay AI Buildathon, this stack is preferable to a more complicated architecture because it maximizes the probability of completing and demonstrating the full RingGuard workflow.

The most important technologies are Next.js/React, FastAPI, PostgreSQL, NetworkX, XGBoost, scikit-learn, React Flow, and the bounded investigation/LLM layer. Neo4j, GNN, RAG, microservices, and advanced agent frameworks should remain optional until the core product is working.

The technical stack should support the product's central proof: transaction-only risk → graph-enhanced risk → traceable evidence → investigation assistance → human decision.


| Field | Value |
| --- | --- |
| Product | RingGuard AI |
| Architecture Goal | Complete, demo-ready network-aware risk detection and investigation platform |
| Primary Architecture | Modular monolith |
| Frontend | Next.js + React + TypeScript |
| Backend | FastAPI + Pydantic |
| Database | PostgreSQL |
| Graph Computation | NetworkX |
| ML | XGBoost + scikit-learn |
| Explainability | SHAP |
| Graph Visualization | React Flow |
| Charts | Recharts |
| UI | Tailwind CSS + shadcn/ui |
| AI | Structured-output LLM + bounded tool calling |
| Deployment | Docker + GitHub |


| Layer | Technology | Priority |
| --- | --- | --- |
| Frontend | Next.js + React + TypeScript | 🔥 MUST HAVE |
| UI | Tailwind CSS + shadcn/ui | 🔥 MUST HAVE |
| Graph UI | React Flow | 🔥 MUST HAVE |
| Charts | Recharts | 🔥 MUST HAVE |
| Backend | FastAPI | 🔥 MUST HAVE |
| Validation | Pydantic | 🔥 MUST HAVE |
| Database | PostgreSQL | 🔥 MUST HAVE |
| ORM | SQLAlchemy | ⭐ SHOULD HAVE |
| Migrations | Alembic | ⭐ SHOULD HAVE |
| Graph computation | NetworkX | 🔥 MUST HAVE |
| Data | Pandas + NumPy | 🔥 MUST HAVE |
| ML | XGBoost | 🔥 MUST HAVE |
| ML utilities | scikit-learn | 🔥 MUST HAVE |
| Explainability | SHAP | ⭐ SHOULD HAVE |
| Synthetic data | Faker + NumPy + custom generators | 🔥 MUST HAVE |
| LLM | Structured-output LLM API | 🔥 MUST HAVE |
| Agent | Bounded tool-calling layer | 🔥 MUST HAVE |
| Model persistence | Joblib | ⭐ SHOULD HAVE |
| Testing | Pytest | ⭐ SHOULD HAVE |
| API testing | HTTPX | ⭐ SHOULD HAVE |
| Containerization | Docker | ⭐ SHOULD HAVE |
| Version control | Git/GitHub | 🔥 MUST HAVE |


| Directory | Responsibility |
| --- | --- |
| data/ | Load, clean and prepare datasets |
| generators/ | Independent synthetic scenario generation |
| features/ | Transaction, behavioral and graph feature engineering |
| graph/ | NetworkX construction and graph analytics |
| models/ | Training and model persistence |
| evaluation/ | Metrics, threshold selection and test evaluation |
| experiments/ | Versioned experiment configurations/results |
| notebooks/ | Exploratory analysis only; production logic should remain in modules |


| API Group | Purpose |
| --- | --- |
| /risk | Risk prediction and risk details |
| /cases | Case creation, retrieval and decisions |
| /accounts | Account information |
| /transactions | Transaction information |
| /networks | Graph/network exploration |
| /evidence | Evidence retrieval |
| /investigation | Controlled investigation operations |
| /timeline | Timeline reconstruction |
| /analytics | Model and business metrics |


| Component | Recommended Choice |
| --- | --- |
| Frontend | Vercel or equivalent |
| Backend | Render / Railway / AWS or equivalent |
| Database | Managed PostgreSQL such as Supabase PostgreSQL or equivalent |
| Containerization | Docker |
| Repository | GitHub |


| Technology | Decision | Reason |
| --- | --- | --- |
| Neo4j | Not initially | NetworkX + PostgreSQL is sufficient for MVP |
| GNN | Do not use initially | Adds complexity without being necessary for the core experiment |
| RAG | Do not use initially | Evidence already comes from structured graph/database operations |
| Microservices | Do not use | Unnecessary deployment and operational complexity |
| Free-form autonomous agent | Remove | Conflicts with bounded, auditable investigation design |
| LLM risk scoring | Remove | Risk scoring should remain measurable and model-based |
| Autonomous financial action | Remove | Defense-only product boundary |
| Multi-LLM architecture | Avoid | Adds complexity without improving core product proof |


| Decision | Final Choice |
| --- | --- |
| Frontend framework | Next.js |
| Frontend library | React |
| Frontend language | TypeScript |
| Styling | Tailwind CSS |
| UI primitives | shadcn/ui |
| Icons | Lucide |
| Graph visualization | React Flow |
| Charts | Recharts |
| Backend | FastAPI |
| Schema validation | Pydantic |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Graph computation | NetworkX |
| Data processing | Pandas + NumPy |
| Primary ML | XGBoost |
| ML utilities | scikit-learn |
| Model explainability | SHAP |
| Synthetic data | Faker + NumPy + custom generator |
| Model persistence | Joblib |
| Investigation AI | Bounded tool-calling |
| LLM | Structured-output LLM API |
| Testing | Pytest + HTTPX |
| Deployment | Docker |
| Source control | Git/GitHub |
