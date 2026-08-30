# Travel Billing System — Production Operations & Deployment Runbook

Comprehensive operational guide for deploying, managing, monitoring, and troubleshooting the Travel Billing System ERP and AMIP (Autonomous Multi-Agent Intelligence Platform).

---

## 1. System Architecture & Topology

```text
                               ┌────────────────────────────────┐
                               │   React 19 Frontend (Vite)     │
                               │   http://localhost:5173        │
                               └───────────────┬────────────────┘
                                               │ HTTP / REST / JWT
                                               ▼
┌──────────────────────────┐      ┌─────────────────────────────┐
│  MySQL Database          │◄────►│  FastAPI Backend (Python)   │
│  localhost:3306          │      │  http://localhost:9000      │
│  Schema: travelbillingdb │      │  AMIP Multi-Agent Engine    │
└──────────────────────────┘      └──────────────┬──────────────┘
                                                 │ Internal API (Port 9001)
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │  AI Microservice (Node.js)  │
                                  │  http://localhost:9001      │
                                  │  Google Gemini Engine       │
                                  └─────────────────────────────┘
```

---

## 2. Port & Service Matrix

| Service | Directory | Port | Health Endpoint | Startup Command |
| :--- | :--- | :--- | :--- | :--- |
| **MySQL Database** | N/A | `3306` | `SELECT 1;` | `net start MySQL80` or docker container |
| **Node.js AI Service** | `ai/` | `9001` | `GET http://localhost:9001/health` | `node server.js` |
| **FastAPI Backend** | `backend/` | `9000` | `GET http://localhost:9000/api/health` | `python -m uvicorn app.main:app --port 9000` |
| **React Frontend** | `frontend/` | `5173` | `GET http://localhost:5173/` | `npm run dev` |

---

## 3. Environment Configuration

### Backend (`backend/.env`):
```env
ENV=dev
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=travelbillingdb

JWT_SECRET=travel-billing-default-secret-key-change-me-please-32chars
JWT_EXPIRATION_MS=86400000

GEMINI_API_KEY=your_gemini_api_key_here
INTERNAL_API_KEY=travel_billing_secret_token_123

USE_ENTERPRISE_LEARNING=True
USE_ENTERPRISE_COPILOT=True
USE_ENTERPRISE_GRAPH=True
USE_PREDICTIVE_ENGINE=True
```

### AI Service (`ai/.env`):
```env
PORT=9001
GEMINI_API_KEY=your_gemini_api_key_here
INTERNAL_API_KEY=travel_billing_secret_token_123
```

### Frontend (`frontend/.env`):
```env
VITE_API_BASE_URL=http://localhost:9000/api
```

---

## 4. Production Startup Sequence

### Step 1: Verify MySQL Service
Ensure MySQL is listening on port `3306`:
```powershell
Test-NetConnection -ComputerName localhost -Port 3306
```

### Step 2: Start Node.js AI Service
```powershell
cd "e:\Project Folder\TravelBillingSystem\ai"
node server.js
```

### Step 3: Start Python FastAPI Backend
```powershell
cd "e:\Project Folder\TravelBillingSystem\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

### Step 4: Start React Frontend
```powershell
cd "e:\Project Folder\TravelBillingSystem\frontend"
npm run dev
```

---

## 5. Container & Cloud Probes

The FastAPI backend exposes standard Kubernetes / container health probes:

- **Liveness Probe**: `GET /api/health/live`
  - Returns `{"status": "ALIVE", "uptime_seconds": 120.5}`
- **Readiness Probe**: `GET /api/health/ready`
  - Validates active database connectivity. Returns `200 OK` or `503 Service Unavailable`.
- **System Health & Diagnostic**: `GET /api/health`
  - Reports composite status across Database, Node AI service, and feature flags.

---

## 6. AMIP Multi-Agent Operations

### Mission Control Center
Access the interactive Mission Control dashboard at:
[http://localhost:5173/amip-control-center](http://localhost:5173/amip-control-center) (Restricted to `OWNER` / `MANAGER`).

### Key AMIP APIs:
- `POST /api/amip/workflows/execute`: Trigger workflow with optional `idempotency_key` and `execution_mode: "ASYNCHRONOUS"`.
- `GET /api/amip/reviews/pending`: Query pending human-in-the-loop validation reviews.
- `POST /api/amip/workflows/{id}/override`: Submit atomic `APPROVE`, `REJECT`, or `ESCALATE` decision.
- `GET /api/amip/workflows/{id}/audit`: Fetch complete audit bundle with execution trace spans and decision explainability trees.

---

## 7. Data Export & Financial Reporting

- **CSV Bill Export**: `GET /api/bills/export/csv`
- **Financial Metric Aggregates**: `GET /api/bills/export/summary`
- **Invoice PDF Generator**: `GET /api/bills/{id}/pdf`

---

## 8. Verification & Test Automation

```powershell
# 1. Run complete Backend Test Suite (166 tests)
& "e:\Project Folder\TravelBillingSystem\backend\.venv\Scripts\python.exe" -m pytest "e:\Project Folder\TravelBillingSystem\backend\tests" "e:\Project Folder\TravelBillingSystem\backend\app\services\amip\tests" -v

# 2. Check Node AI Service Syntax
node --check "e:\Project Folder\TravelBillingSystem\ai\server.js"

# 3. Verify Frontend Production Build
npm --prefix "e:\Project Folder\TravelBillingSystem\frontend" run build
```
