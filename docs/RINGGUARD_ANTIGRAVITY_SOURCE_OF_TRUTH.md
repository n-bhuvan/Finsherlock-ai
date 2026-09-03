# RingGuard AI — Antigravity Project Reference

## Purpose
This folder contains the four project source documents for RingGuard AI, Razorpay AI Buildathon 2026, Track 02 — AI Risk Manager.

## Source-of-truth priority
1. Official Razorpay Buildathon rules when explicitly provided
2. Final Build Specification
3. PRD
4. Technical Stack / Architecture
5. UI/UX Design
6. Existing verified implementation and tests
7. Stage-specific instructions from the project owner

## Current verified state
Stages 1–8 are complete and audited. Stage 8 commit: `785326a` (`stage 8: fastapi risk APIs`).
Next stage: Stage 9 — Evidence + Timeline Engine.

## Frozen-stage rule
Do not rebuild or casually refactor completed stages. Preserve existing APIs, models, database schema, point-in-time feature safety, NetworkX architecture, and verified tests unless a real defect is found or a later stage explicitly requires a backward-compatible change.

## Core architecture
Next.js/React/TypeScript frontend; FastAPI/Pydantic backend; PostgreSQL persistent source of truth; NetworkX graph computation; XGBoost/scikit-learn ML; React Flow graph UI; Recharts analytics; structured-output LLM plus bounded read-only investigation tools; Git/GitHub.

## Core product
Network-aware coordinated payment-abuse / mule-ring detection plus evidence-first investigation. Workflow:
Detect → Connect → Investigate → Correlate → Explain → Quantify Impact → Human Decision.

## Safety boundaries
Defense-only. No autonomous fund movement, payments, approval/rejection, blocking, financial-record modification, risk-score modification by LLM, unrestricted agent behavior, fabricated evidence, or claims that synthetic data is real Razorpay data.

## ML architecture
Model A = transaction + behavioral.
Model B = transaction + behavioral + point-in-time-safe graph.
Final RingGuard = Model B + evidence/investigation workflow.
Do not manufacture graph uplift; current synthetic data reached a metric ceiling and later hard negatives are intended to test incremental network value.

## Stage discipline
BUILD → Implementation Report → Audit Gate → GREEN/YELLOW/RED → Git checkpoint → next stage.

## Reference files
- `RingGuard_Final_Build_Spec_v1.0.md`
- `RingGuard_PRD_v1.0.md`
- `RingGuard_Technical_Stack_v1.0.md`
- `RingGuard_UI_Design_v1.0.md`
