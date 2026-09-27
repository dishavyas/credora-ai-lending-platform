# Credora AI — Intelligent Loan Origination & Underwriting Platform

Credora AI is a portfolio-grade full-stack fintech application demonstrating a modern loan-origination workflow with AI-assisted risk and underwriting features.

## What actually works

- JWT authentication and role-aware users
- Customer onboarding
- Loan application creation and lifecycle tracking
- KYC status management
- Financial document metadata registration and verification
- Deterministic explainable risk scoring
- AI-style underwriting brief generated from application facts
- Human-in-the-loop approve / reject / request-info decisions
- Missing-document recommendations
- Customer notification records
- Audit trail
- Management dashboard KPIs
- REST API documentation via FastAPI Swagger
- Vue 3 + TypeScript responsive dashboard
- SQLite persistence for zero-setup local development
- Docker Compose

## Honest architecture note

The runnable demo uses SQLite and a deterministic local AI/risk engine so it works without paid cloud credentials. The repository contains clear extension points for enterprise services such as Azure OpenAI, Claude, Gemini, Llama, Kafka, Oracle, Redis, OpenSearch, OCR/document intelligence, credit bureaus, e-signature, email and SMS. Do not describe those as live integrations unless you implement and configure them.

## Workflow

Customer → Application → Documents/KYC → Risk Analysis → AI Underwriting Brief → Human Review → Decision → Notification

## Demo credentials

- Admin: `admin@credora.ai`
- Password: `Admin@123`

The backend seeds this user automatically.

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

## Docker

```bash
docker compose up --build
```

Then open `http://localhost:5173`.

## Main API areas

- `/api/auth`
- `/api/dashboard`
- `/api/customers`
- `/api/applications`
- `/api/documents`
- `/api/risk`
- `/api/underwriting`
- `/api/notifications`
- `/api/audit`

## Portfolio talking points

This project demonstrates API design, authentication, relational data modeling, explainable decision support, human-in-the-loop workflows, auditability, Vue/TypeScript UI development, Python/FastAPI services, and an extensible architecture for enterprise AI integrations.

## Security disclaimer

This is a portfolio/demo system. It is not certified for real lending, KYC/AML compliance, credit decisions, or storage of real customer financial/identity data. Use synthetic data only.

## Windows quick start

Double-click `start-windows.bat`, or run it from Command Prompt. The Vite dev server proxies `/api` to FastAPI, so frontend actions reach the backend.

## End-to-end smoke test

After backend dependencies are installed:
```bash
cd backend
.venv\Scripts\activate
python smoke_test.py
```
Expected final line starts with `PASS:`.
