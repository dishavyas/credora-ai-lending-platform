@echo off
start "Credora API" cmd /k "cd /d %~dp0backend && if not exist .venv python -m venv .venv && .venv\Scripts\python -m pip install -r requirements.txt && .venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"
start "Credora Web" cmd /k "cd /d %~dp0frontend && if not exist node_modules npm install && npm run dev"
echo Starting Credora AI. Open http://localhost:5173 after both terminals are ready.
