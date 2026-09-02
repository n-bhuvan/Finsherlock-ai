# RingGuard AI

> **Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation**  
> *Razorpay AI Buildathon 2026 — Track 02 (AI Risk Manager)*

---

## Overview & Purpose

**RingGuard AI** is a defense-only AI risk investigation platform engineered to detect, analyze, and document coordinated payment abuse and mule-account networks. 

Traditional payment fraud detection often evaluates transactions in isolation. RingGuard AI couples transaction graph intelligence with machine learning and controlled AI investigation tools to expose multi-account syndicates sharing devices, IPs, beneficiary tokens, and cyclic fund flows.

---

## Current Status: Stage 1 — Project Foundation

> [!IMPORTANT]
> **Stage 1 strictly establishes the foundational architecture.**
> - The application does **NOT** yet perform fraud or abuse-ring detection.
> - No fake or placeholder risk metrics, transactions, cases, or graphs are displayed.
> - The repository structure, modular backend, and reactive frontend foundation are initialized and verified.

---

## Technology Stack

### Currently Initialized (Stage 1)
- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS, Lucide React
- **Backend:** Python 3.13+, FastAPI, Pydantic v2, Uvicorn
- **Testing & Tooling:** Pytest, HTTPX, ESLint

### Planned for Subsequent Stages
- **Data & Persistence:** PostgreSQL, SQLAlchemy / AsyncPG
- **Graph Engine:** NetworkX
- **Data Processing:** Pandas, NumPy
- **Machine Learning & Explainability:** XGBoost, Scikit-learn, SHAP
- **Visualization:** React Flow, Recharts
- **Investigation AI:** Controlled read-only LLM agent with structured JSON output
- **Safety & Audit:** Immutable audit logging, Human-in-the-Loop decision gateway

---

## Project Structure

```
ringguard-ai/
├── frontend/                 # Next.js + React + TypeScript web client
│   ├── app/                  # App Router pages and layout
│   ├── components/           # UI components by domain
│   │   ├── dashboard/        # Dashboard view containers
│   │   ├── cases/            # Case list and detail views
│   │   ├── graph/            # Network graph visualization
│   │   ├── timeline/         # Chronological event sequence
│   │   ├── evidence/         # Evidence dossiers
│   │   └── investigation/    # AI investigation assistant
│   ├── lib/                  # Shared utilities and API client
│   └── types/                # TypeScript type definitions
│
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/              # Domain routers (risk, cases, accounts, etc.)
│   │   ├── models/           # Domain entity definitions
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Core application services
│   │   ├── investigation/    # Read-only investigation runners
│   │   ├── evidence/         # Evidence extraction logic
│   │   ├── timeline/         # Timeline generation logic
│   │   └── audit/            # Audit trail & decision logging
│   └── tests/                # Automated backend test suite
│
├── ml/                       # Machine learning & data pipeline
│   ├── data/                 # Raw/processed dataset storage
│   ├── generators/           # Synthetic network & transaction generators
│   ├── features/             # Feature engineering pipelines
│   ├── graph/                # NetworkX topology builders
│   ├── models/               # Model training & serialization
│   ├── evaluation/           # Performance benchmarks & metrics
│   ├── experiments/          # Research and iteration logs
│   └── notebooks/            # Exploratory analysis notebooks
│
├── models/                   # Saved model binaries / weights
├── scripts/                  # Operational & deployment utility scripts
├── docker/                   # Docker build assets
├── docs/                     # Technical specifications & architecture
│   ├── ARCHITECTURE.md       # Full architecture specification
│   └── DEVELOPMENT.md        # Local development setup instructions
│
├── .gitignore                # Git ignore patterns
├── .env.example              # Environment variables template
├── docker-compose.yml        # Multi-container orchestration foundation
└── README.md                 # Project README
```

---

## Quick Start

### 1. Backend
```bash
cd backend
python -m venv venv
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Health Check: `http://localhost:8000/health`

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Web UI: `http://localhost:3000`

---

## Operational Safeguards & Boundaries

- **Defense-Only:** Designed solely for risk detection, evidence presentation, and analyst decision support.
- **No Financial Authority:** Does not move funds, execute transfers, or communicate with payment rails.
- **Human Authority:** No automated blocking or clearing; human analysts retain full decision control.
- **Read-Only AI:** AI investigation capabilities are strictly sandboxed to read-only evidence retrieval.
