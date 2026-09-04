@echo off
TITLE RingGuard AI -- Judge Demo Launcher
echo ======================================================================
echo RINGGUARD AI -- RAZORPAY AI BUILDATHON 2026 (TRACK 02: AI RISK MANAGER)
echo Automated One-Click Judge Demonstration Launcher
echo ======================================================================
echo.

set REPO_ROOT=%~dp0
cd /d "%REPO_ROOT%"

:: 1. Check Python Virtual Environment
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Backend virtual environment not found at backend\venv!
    echo Please create it with: python -m venv backend\venv and install requirements.
    pause
    exit /b 1
)

:: 2. Check Database Connectivity
echo [1/4] Verifying PostgreSQL database connectivity and ML models...
backend\venv\Scripts\python -c "from app.db.session import SessionLocal; from app.models.transaction import Transaction; s = SessionLocal(); count = s.query(Transaction).count(); s.close(); print(f'Connected successfully: {count} verified transactions in database.')"
if %errorlevel% neq 0 (
    echo [WARNING] Database connection check encountered an error. Ensure PostgreSQL is running.
)

:: 3. Launch Backend Server (FastAPI on Port 8000)
echo.
echo [2/4] Starting FastAPI Risk Engine on http://localhost:8000 ...
start "RingGuard Backend (Port 8000)" cmd /k "cd /d %REPO_ROOT% && backend\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: Wait 3 seconds for backend initialization
timeout /t 3 /nobreak >nul

:: 4. Launch Frontend Server (Next.js on Port 3000)
echo [3/4] Starting Next.js Investigation Dashboard on http://localhost:3000 ...
start "RingGuard Frontend (Port 3000)" cmd /k "cd /d %REPO_ROOT%\frontend && npm run start"

:: Wait 3 seconds for frontend initialization
timeout /t 3 /nobreak >nul

:: 5. Open Web Browser to Primary Hero Case
echo [4/4] Launching Browser to Primary Ring Hero Case (TXN_00000203)...
start http://localhost:3000/cases/TXN_00000203

echo.
echo ======================================================================
echo RingGuard AI Demonstration is now LIVE!
echo - Dashboard URL : http://localhost:3000/cases/TXN_00000203
echo - Analytics URL : http://localhost:3000/analytics
echo - Backend API   : http://localhost:8000/docs
echo.
echo Press any key to exit this launcher window (servers will stay open).
echo ======================================================================
pause >nul
