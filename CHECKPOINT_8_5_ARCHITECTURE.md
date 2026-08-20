# AMIP CHECKPOINT 8.5 — ARCHITECTURAL DISCOVERY & PROPOSAL

## Executive Recommendation

We recommend implementing:
**`AMIP CHECKPOINT 8.5 — OPERATIONAL MISSION CONTROL & HUMAN-IN-THE-LOOP (HITL) MANAGEMENT`**

### Core Rationale
Through Checkpoints 8.1–8.4, the AMIP backend has achieved complete autonomous agent maturity:
- **Telemetry & Observability** (Metrics, Structured Logging, Distributed Traces, Diagnostics — CP 8.1)
- **Runtime Monitoring APIs** (REST Health, Metrics, Spans, and Execution Snapshots — CP 8.2)
- **Durable Persistence & Audit Retention** (MySQL tables, non-blocking fault isolation, 30/90d cleanup — CP 8.3)
- **Autonomous Execution Gateway & Dispatcher** (Workflow execution, cooperative cancellation, audit bundles — CP 8.4)

However, the platform currently lacks:
1. **An Operational Visual Surface (Mission Control Center)**: Operators have no unified UI interface to observe live multi-agent workflows, trigger execution tasks, inspect trace waterwalls, or examine explainability narratives.
2. **Human-in-the-Loop (HITL) Governance & Review Queues**: When multi-agent consensus diverges or confidence falls below the auto-approval threshold (`DecisionStatus.REVIEW_REQUIRED`), there is currently no formal mechanism for human operators to inspect the pending review queue, review evidence breakdowns, and record manual overrides (`APPROVE`, `REJECT`, `ESCALATE`) with audit integrity.

Checkpoint 8.5 bridges these final capabilities, delivering an enterprise operator portal and HITL review management system.

---

## 1. Current Architecture Assessment

```text
AMIP Engine Architecture (Checkpoints 1 - 8.4)
┌─────────────────────────────────────────────────────────────────────────────┐
│ REST API Gateway (amip_monitoring_router, amip_workflow_router)             │
│   ├── POST /api/amip/workflows/execute                                      │
│   ├── POST /api/amip/workflows/{id}/cancel                                  │
│   ├── GET  /api/amip/workflows/{id}/audit                                   │
│   └── GET  /api/amip/{health, metrics, executions, traces, diagnostics}     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Core Facade: AMIPWorkflowGateway & AMIPSupervisor                          │
│   ├── Planning Layer (ExecutionPlanner, TaskDependencyGraph)                │
│   ├── Execution Engine & Agent Adapters (DocIntel, Validation, Learning...) │
│   ├── Decision Matrix (Confidence scoring, Consensus, Conflict resolution)   │
│   ├── Resilience Runtime (CircuitBreaker, CancellationToken, Timeouts)      │
│   └── Explainability Engine (TimelineRenderer, ExecutionNarrator)           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dual-Layer Observability & Persistence                                      │
│   ├── In-Memory Buffer (Instant 0ms live query response)                    │
│   └── SQLAlchemy Observability Repository (Non-blocking MySQL audit)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Capability Gap Analysis Across Evaluated Dimensions

### Area A: Operational UI / AMIP Control Center
- **Why Needed**: Operators cannot be expected to run raw `curl` commands to inspect distributed traces, check circuit breaker health, or trigger autonomous doc intelligence jobs.
- **What Exists**: Complete backend REST APIs for health, metrics, traces, execution snapshots, and diagnostics.
- **Gaps**: Dedicated React control center dashboard with real-time polling, visual health cards, trace timeline waterfall, and interactive workflow execution modal.

### Area B: Workflow Lifecycle Management
- **Why Needed**: Track workflow state transitions (`RUNNING` -> `COMPLETED` / `REVIEW_REQUIRED` / `CANCELLED`), view live retry counts, and inspect historical execution runs.
- **What Exists**: `ExecutionSnapshot`, `amip_workflow_executions` table, `AMIPWorkflowGateway.cancel_workflow`.
- **Gaps**: UI representation of historical executions table with status filters, duration metrics, and task progress indicators.

### Area C: Human-in-the-Loop (HITL) Controls
- **Why Needed**: Autonomous systems must not make unreviewed irreversible decisions when confidence is borderline or agent votes conflict (`DecisionPolicy.AUTO_REVIEW` / `MANUAL_REVIEW`). Operators need a formal review queue and override mechanism.
- **What Exists**: `DecisionMatrix` outputs `REVIEW_REQUIRED` and provides conflicting agent evidence.
- **Gaps**:
  1. Backend HITL review queue endpoint: `GET /api/amip/reviews/pending`.
  2. Backend HITL decision override endpoint: `POST /api/amip/workflows/{workflow_id}/override` (recording operator action, justification reason, and timestamp).
  3. Interactive UI review modal displaying conflicting agent votes, validation summaries, and decision action buttons (`Approve Override`, `Reject`, `Escalate`).

### Area D: Security / Governance
- **Why Needed**: Prevent unauthorized users from executing workflows or approving overrides.
- **What Exists**: `RoleChecker(["OWNER", "MANAGER"])` securing all AMIP endpoints.
- **Gaps**: UI route protection restricting AMIP Mission Control to `OWNER` and `MANAGER` roles in `frontend/src/main.jsx`.

### Area E: Production Readiness
- **Why Needed**: High-frequency telemetry queries must not overload the database or UI main thread.
- **What Exists**: Non-blocking in-memory reads + fault-isolated database fallback.
- **Gaps**: Configurable UI auto-refresh interval (e.g. 5s / 10s polling with manual pause).

### Area F: Frontend Integration
- **Why Needed**: Seamless integration with the existing React / Vite / Tailwind UI theme and navigation.
- **What Exists**: React 18, Vite, Lucide React icons, Tailwind CSS, Sonner toast notifications, `MainLayout.jsx`.
- **Gaps**: New dedicated navigation item (`AMIP Mission Control`) and sub-views in `frontend/src/pages/AMIPControlCenterPage.jsx`.

---

## 3. Proposed Checkpoint 8.5 Scope

### Title
**`AMIP CHECKPOINT 8.5 — OPERATIONAL MISSION CONTROL & HUMAN-IN-THE-LOOP (HITL) MANAGEMENT`**

### Exact Objective
1. Expose backend Human-in-the-Loop (HITL) review queue and operator override endpoints.
2. Build a rich, production-grade **AMIP Mission Control Center** in the React frontend.
3. Enable operators to:
   - Monitor real-time platform health, active workflows, throughput, and error rates.
   - Dispatch autonomous workflows with custom task parameters.
   - Inspect visual distributed trace waterfalls and parent-child span hierarchies.
   - Review pending HITL decision conflicts and submit audited manual overrides.
   - Explore narrative explainability reports and structured log streams.

---

## 4. Components to Be Created & Modified

### Backend Components
1. **`backend/app/schemas/amip_hitl.py`** [NEW]:
   - `HITLReviewItemResponse`: Workflow ID, task type, confidence, reason, conflicting agents, requested at.
   - `HITLOverrideRequest`: Action (`APPROVE`, `REJECT`, `ESCALATE`), operator justification reason.
   - `HITLOverrideResponse`: Workflow ID, previous status, new status, operator, timestamp.
2. **`backend/app/routers/amip_workflow.py`** [MODIFY]:
   - `GET /api/amip/reviews/pending`: Returns workflows currently in `REVIEW_REQUIRED` status.
   - `POST /api/amip/workflows/{workflow_id}/override`: Records operator override, updates execution snapshot and database record, logs audit entry.
3. **`backend/app/services/amip/gateway/workflow_gateway.py`** [MODIFY]:
   - Add `get_pending_reviews()` and `submit_human_override()`.

### Frontend Components
1. **`frontend/src/services/amipService.js`** [NEW]:
   - API client wrapper for all `/api/amip/*` and `/api/amip/workflows/*` endpoints.
2. **`frontend/src/pages/AMIPControlCenterPage.jsx`** [NEW]:
   - Comprehensive Mission Control dashboard featuring:
     - **Overview Tab**: Live health cards, throughput metrics, active subsystem badges.
     - **Workflows Tab**: Execution history table with status filter, duration, task badges, and cancel actions.
     - **HITL Review Queue Tab**: Pending reviews list with confidence breakdown, conflicting votes, and override actions.
     - **Trace & Spans Tab**: Trace waterfall hierarchy visualizer.
     - **Logs & Diagnostics Tab**: Real-time log streamer and platform diagnostics report viewer.
     - **Trigger Workflow Modal**: Form to trigger autonomous jobs with task type and custom JSON payload.
3. **`frontend/src/ui/Sidebar.jsx` & `frontend/src/main.jsx`** [MODIFY]:
   - Add `/amip-control-center` route protected by `RoleChecker(["OWNER", "MANAGER"])`.

---

## 5. Security, Persistence & Concurrency Considerations

- **Security**: All HITL overrides and workflow dispatches require `OWNER` or `MANAGER` role. Operator username and timestamp are recorded into the audit trail.
- **Persistence**: Reuses the existing `amip_workflow_executions` table by updating `status` to `APPROVED` / `REJECTED` and appending override details in `metadata_json`. **Zero new database tables required.**
- **Concurrency**: State updates use existing `_lock` (RLock) in `AMIPMonitoringService` and `AMIPWorkflowGateway`.
- **Fault Isolation**: Telemetry and audit writes remain strictly non-blocking.

---

## 6. Testing Strategy

1. **Backend Unit & Integration Tests** (`backend/app/services/amip/tests/test_amip_hitl.py`):
   - Test querying pending review queue.
   - Test operator approval override.
   - Test operator rejection override.
   - Test role authorization (401, 403, 200).
   - Test idempotency and invalid override handling.
2. **Frontend Build & Integration**:
   - Verify `npm --prefix frontend run build` succeeds with zero errors.
3. **Full Regression**:
   - Ensure all **148+ existing backend tests** continue to pass (100%).

---

## 7. Explicit Exclusions (What Checkpoint 8.5 Must NOT Implement)

- Do NOT modify existing ERP billing or invoice domain orchestrators (`ValidationOrchestrator`, `BulkImportService`, etc.).
- Do NOT introduce external LLM/AI dependencies.
- Do NOT alter database tables or create migrations.

---

## 8. Recommended Implementation Sequence

1. Define HITL schemas in `backend/app/schemas/amip_hitl.py`.
2. Add HITL methods in `AMIPWorkflowGateway` and endpoints in `amip_workflow.py`.
3. Add backend tests in `test_amip_hitl.py` and verify all tests pass.
4. Implement frontend API client `frontend/src/services/amipService.js`.
5. Implement `frontend/src/pages/AMIPControlCenterPage.jsx` and register route in `main.jsx` and `Sidebar.jsx`.
6. Run full verification (`pytest`, `node --check ai/server.js`, `npm run build`).
7. Generate `CHECKPOINT_8_5_REPORT.md`.
