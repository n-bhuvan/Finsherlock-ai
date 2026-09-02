# RingGuard AI — Architecture Specification

## Overview

**Product Name:** RingGuard AI  
**Subtitle:** Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation  
**Track:** Razorpay AI Buildathon 2026 — Track 02 (AI Risk Manager)  
**Current Stage:** Stage 1 — Project Foundation

RingGuard AI is an enterprise-grade, defense-only AI risk investigation platform designed to detect coordinated payment abuse, fraud syndicates, and mule-account networks.

---

## Architectural Philosophy: Modular Monolith

RingGuard AI is intentionally architected as a **Modular Monolith**. 

### Why a Modular Monolith?
- **Unified Domain Model:** Coordinated fraud detection requires tight coupling between transaction logs, behavioral signals, entity graph topologies, and evidence synthesis.
- **Operational Simplicity:** Avoids the premature operational complexity, distributed transaction overhead, and eventual consistency delays of microservices.
- **Strict Module Boundaries:** Components (Evidence, Graph, Timeline, ML, Audit, Investigation) are strictly separated by clear service interfaces and typed contracts, allowing easy extraction into separate services in the future if scale demands.

---

## High-Level Architecture Flow

```
┌────────────────────────────────────────────────────────┐
│           Next.js / React / TypeScript Frontend        │
│    (Dark Enterprise Risk Ops UI, Real-Time Badges)     │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON (HTTP)
                            ▼
┌────────────────────────────────────────────────────────┐
│                  FastAPI Backend Gateway               │
│        (Pydantic Validation, Modular Routing, CORS)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Application Services                 │
│ (Case Manager, Account Aggregator, Transaction Feed)   │
└───────────────┬──────────────────────┬─────────────────┘
                │                      │
        ┌───────┴──────────┐   ┌───────┴──────────┐
        │   PostgreSQL     │   │     NetworkX     │
        │ (Persistent Data │   │ (Graph Topology  │
        │ Source of Truth) │   │ & Ring Traversal)│
        └───────┬──────────┘   └───────┬──────────┘
                │                      │
                └──────────┬───────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                XGBoost ML Risk Pipeline                │
│       (Tabular Features + Graph Network Features)      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Evidence & Timeline Engine                 │
│      (Deterministic Rule Hits, Graph Subgraphs)        │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│         Controlled Read-Only Investigation AI          │
│       (Structured-Output LLM Natural Explanations)     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Human Risk Analyst (Final Authority)       │
│     (Reviews Evidence Dossier, Makes Human Decision)   │
└────────────────────────────────────────────────────────┘
```

---

## Core System Components

### 1. Frontend (`frontend/`)
- **Technology:** Next.js (App Router), React, TypeScript, Tailwind CSS.
- **Design Language:** High-density, dark enterprise operations theme tailored for risk analysts.
- **Role:** Interactive visualization of risk cases, timeline events, entity graph relationships, and AI evidence dossiers.

### 2. Backend Gateway & Services (`backend/app/`)
- **Technology:** Python 3.13+, FastAPI, Pydantic v2.
- **Organization:**
  - `api/`: Route definitions organized by domain (`/risk`, `/cases`, `/accounts`, `/transactions`, `/networks`, `/evidence`, `/investigation`, `/timeline`, `/analytics`).
  - `schemas/`: Pydantic request/response validation contracts.
  - `models/`: Database models and domain entities.
  - `services/`: Business logic orchestration.
  - `investigation/`: Read-only investigation tool runners.
  - `evidence/`: Deterministic signal and subgraph extraction.
  - `timeline/`: Chronological event sequencing.
  - `audit/`: Immutable operational decision logs.

### 3. Data & Graph Layer
- **PostgreSQL (Implemented in Stage 3):** Serves as the authoritative, transactional persistence layer for customers, accounts, devices, IPs, beneficiaries, merchants, transactions, and provenance metadata. Enforces exact decimal financial precision (`Numeric(14, 2)`), timezone-aware timestamps, foreign-key referential integrity, and positive amount check constraints.
- **NetworkX (Planned for Later Stages):** In-memory graph computation engine for analyzing shared device footprints, IP clusters, bank account re-use, and community detection algorithms (Louvain / Connected Components).

### 4. ML Risk Model (Planned for Later Stages)
- **XGBoost & Scikit-learn:** Hybrid risk scoring combining behavioral transaction features with graph centrality/community metrics.
- **Explainability (SHAP):** Transparent feature attributions explaining each risk score.

### 5. Investigation AI & LLM Explanation (Planned for Later Stages)
- **Controlled Read-Only Tools:** The investigation assistant operates strictly with read-only query capabilities across the evidence base.
- **Structured Output:** Enforces Pydantic-validated JSON output for explainable narratives, hypothesis formulation, and evidence referencing.

---

## Strict Safety Boundaries & Explicit Non-Goals

> [!CAUTION]
> RingGuard AI is strictly an **evidence-first investigation and decision-support platform**. It operates under clear security, financial, and operational boundaries:

1. **No Movement of Funds:** RingGuard AI has no payment gateway credentials and cannot move, debit, credit, or transfer funds under any circumstances.
2. **No Autonomous Payment Execution:** RingGuard AI does not execute financial transactions.
3. **No Autonomous Approvals:** RingGuard AI does not autonomously clear or approve flagged accounts/transactions.
4. **No Autonomous Blocks:** RingGuard AI does not autonomously freeze or block payment processing.
5. **Read-Only Investigation Environment:** The AI investigation assistant interacts solely with read-only tools; it cannot mutate system state or delete data.
6. **Human-in-the-Loop Authority:** Final risk decisions (e.g., sanctioning, escalating, clearing) rest exclusively with human risk analysts.

---

## Current Status (Stage 3 Complete)

- **Stage 1 (Foundation):** Clean modular monolith architecture, Next.js frontend, FastAPI backend with live `GET /health` connectivity check.
- **Stage 2 (Synthetic Data Engine):** Reproducible generator with default seed `20260903` producing 7 controlled scenarios and hard negatives.
- **Stage 3 (PostgreSQL Database):** Authoritative PostgreSQL persistence layer with SQLAlchemy models, Alembic migrations, full dataset import (500 customers, 500 accounts, 2,000 transactions, 100 devices, 150 IPs, 100 beneficiaries, 50 merchants), positive check constraints, and 100% referential integrity validation.

