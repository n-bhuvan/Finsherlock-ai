# RingGuard AI — Development Guide

This guide describes how to run and verify RingGuard AI locally during **Stage 1 (Project Foundation)**.

---

## Prerequisites

- **Python:** 3.11+ (Python 3.13 tested)
- **Node.js:** 18.x or later (Node 24 tested)
- **npm:** 9.x or later

---

## 1. Backend Setup

### Navigate to the backend directory
```bash
cd backend
```

### Create and activate a virtual environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the FastAPI server
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be live at `http://localhost:8000`.

### Verify Backend Health
Open `http://localhost:8000/health` in your browser or run:
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{
  "status": "ok",
  "service": "ringguard-backend"
}
```

### Run Backend Tests
```bash
pytest
```

---

## 2. Frontend Setup

### Navigate to the frontend directory
```bash
cd frontend
```

### Install dependencies
```bash
npm install
```

### Run the Next.js development server
```bash
npm run dev
```

The frontend will be live at `http://localhost:3000`.

### Verify Frontend Connectivity
1. Open `http://localhost:3000` in your browser.
2. The page should show:
   - `Frontend: Online`
   - `Backend: Connected` (with a green indicator when the backend is running)
3. If the backend is shut down, the status updates to:
   - `Backend: Not Connected` (with a red indicator)

---

## 3. Environment Configuration

Copy the example environment files if custom overrides are needed:

```bash
# Root example
cp .env.example .env

# Frontend environment
cp frontend/.env.example frontend/.env.local
```
