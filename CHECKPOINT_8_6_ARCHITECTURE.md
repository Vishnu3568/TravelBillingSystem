# AMIP CHECKPOINT 8.6 — ARCHITECTURAL DISCOVERY & PROPOSAL

## 1. Title
**`AMIP CHECKPOINT 8.6 — WORKFLOW DURABILITY, IDEMPOTENCY & FAULT-TOLERANT RECOVERY RUNTIME`**

---

## 2. Executive Summary

Through Checkpoints 8.1 to 8.5, the Autonomous Multi-Agent Intelligence Platform (AMIP) has established:
- **Telemetry & Distributed Tracing** (CP 8.1)
- **Runtime Monitoring APIs** (CP 8.2)
- **Persistent MySQL Observability & Retention** (CP 8.3)
- **Unified Workflow Gateway & Dispatcher** (CP 8.4)
- **Operational Mission Control & Human-in-the-Loop Review Queue** (CP 8.5)

Our skeptical architectural audit of the active codebase reveals that while the control plane and API interfaces are complete, the **runtime execution model remains fragile under real-world production edge cases**:
1. **Asynchronous Execution Gap**: `WorkflowExecutionRequest` accepts `execution_mode: ASYNCHRONOUS`, but the gateway currently processes all workflows synchronously on the HTTP request thread, blocking clients and risking HTTP timeouts during long-running multi-agent pipelines.
2. **Missing Idempotency Protection**: Repeated executions (from network retries, double-clicks, or webhook deliveries) spawn duplicate workflows and parallel task executions because no deduplication key or in-flight lease is enforced.
3. **Zombie Workflow Leakage on Process Restart**: In-flight workflows that are interrupted by application crashes or server restarts remain permanently marked as `RUNNING` in the database with no startup recovery or heartbeat lease reconciliation.
4. **Optimistic Concurrency Gaps in HITL Overrides**: Concurrent operator submissions on the same `REVIEW_REQUIRED` workflow lack check-and-set versioning, risking lost updates and inconsistent audit histories.
5. **Missing Intermediate Task Checkpointing**: Intermediate task states are held solely in in-memory blackboards; if a multi-task workflow fails mid-execution, prior completed task outputs cannot be recovered.

Checkpoint 8.6 addresses these fundamental durability, concurrency, and reliability gaps to transition AMIP from a prototype runtime to an enterprise-grade resilient platform.

---

## 3. Current Platform State Assessment

```text
Current State (Checkpoints 8.1 - 8.5):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Fast-Path REST Interfaces (FastAPI Router + React Mission Control)          │
│   ├── POST /api/amip/workflows/execute                                      │
│   ├── POST /api/amip/workflows/{id}/cancel                                  │
│   ├── GET  /api/amip/reviews/pending                                        │
│   └── POST /api/amip/workflows/{id}/override                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Core Facade: AMIPWorkflowGateway                                            │
│   ├── Executes synchronously on the calling thread (Blocking)               │
│   ├── No Idempotency Key validation                                         │
│   ├── No Heartbeat Lease or Startup Reconciliation                          │
│   └── Single-Point in-memory snapshot updates                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ Persistence Layer: SQLAlchemyObservabilityRepository                        │
│   ├── Non-blocking async error suppression                                  │
│   └── Saves only at workflow completion (No step checkpointing)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Deep Audit Findings (Skeptical Codebase Review)

| Area / Question | Current Codebase Finding | Architectural Risk Level |
| :--- | :--- | :--- |
| **1. Asynchronous Execution** | `execution_mode: ASYNCHRONOUS` is parsed in `workflow_gateway.py:128-133`, but `self.supervisor.orchestrate()` is called synchronously on line 200. | **CRITICAL** (Blocks HTTP thread for multi-task jobs) |
| **2. Process Crash / Restart** | If server restarts mid-execution, memory state is lost and database status remains stuck at `RUNNING` indefinitely. | **HIGH** (Zombie workflows in DB & dashboard) |
| **3. Idempotency & Replay** | No `idempotency_key` in `WorkflowExecutionRequest` (`backend/app/schemas/amip_workflow.py`). Every POST creates a new UUID `workflow_id`. | **HIGH** (Duplicate billing/OCR runs on network retry) |
| **4. Concurrent HITL Overrides** | `submit_human_override()` reads status from snapshot and updates without optimistic locking or version checking. | **MEDIUM** (Race condition on simultaneous operator actions) |
| **5. Task-Level Checkpointing** | `ExecutionEngine.execute_plan()` iterates tasks in memory. If step 3 of 4 fails, step 1 & 2 outputs on blackboard are lost on crash. | **MEDIUM** (Requires full re-run rather than resuming) |
| **6. Database Availability** | Persistence failures are safely isolated via try/except in `SQLAlchemyObservabilityRepository`, which correctly prevents workflow disruption. | **HEALTHY** (Verified in Checkpoint 8.3 & 8.4) |
| **7. Role-Based Access** | `RoleChecker(["OWNER", "MANAGER"])` is enforced on all AMIP endpoints at the FastAPI dependency layer. | **HEALTHY** (Verified in Checkpoint 8.2, 8.4, 8.5) |
| **8. Secret Sanitization** | `sanitize_payload()` recursively scrubs sensitive keys (`password`, `token`, `secret`, `raw_text`). | **HEALTHY** (Verified in Checkpoint 8.3) |

---

## 5. Capability Gaps to Address in Checkpoint 8.6

1. **True Asynchronous Execution Engine**:
   - Add a non-blocking background task worker pool (`BackgroundTasks` / thread pool executor) in `AMIPWorkflowGateway`.
   - When `execution_mode: ASYNCHRONOUS` is requested, return `202 Accepted` immediately with status `RUNNING`, `workflow_id`, and `trace_id`.
2. **Idempotency & Deduplication Guard**:
   - Add optional `idempotency_key: Optional[str]` to `WorkflowExecutionRequest`.
   - If an idempotency key is submitted while an identical workflow is `RUNNING` or `COMPLETED` within a deduplication window (e.g. 15 minutes), return the existing execution result instead of re-executing.
3. **Heartbeat Lease & Zombie Workflow Recovery**:
   - Add an execution heartbeat updater during active workflow runs.
   - Implement a startup reconciliation hook in `FastAPI` startup to scan for stale `RUNNING` workflows whose heartbeat expired (> 2 minutes) and mark them as `RECOVERED_FAILED` or `STALE_TERMINATED` with an audit log.
4. **Optimistic Versioning on HITL Overrides**:
   - Enforce atomic state transition checks (`WHERE status = 'REVIEW_REQUIRED'`) to guarantee only one operator override succeeds.
5. **Incremental Step Checkpointing**:
   - Persist intermediate task execution progress (`current_task`, `completed_tasks`, `agent_states`) to the database as each task completes.

---

## 6. Proposed Checkpoint 8.6 Scope

### Title
**`AMIP CHECKPOINT 8.6 — WORKFLOW DURABILITY, IDEMPOTENCY & FAULT-TOLERANT RECOVERY RUNTIME`**

### Exact Objective
Build a durable, fault-tolerant execution runtime for AMIP that supports:
1. True asynchronous background dispatching (`202 Accepted` with background thread pool).
2. Idempotent workflow deduplication via client-provided or payload-hashed idempotency keys.
3. Automated startup reconciliation and lease-based heartbeat recovery for interrupted/zombie workflows.
4. Atomic optimistic state transitions for Human-in-the-Loop decision overrides.
5. Incremental step checkpointing across multi-agent task lifecycles.

---

## 7. Component Boundaries & Architecture

```text
HTTP Ingress (POST /api/amip/workflows/execute)
                  │
                  ▼
       Idempotency Lease Manager
  (Check in-flight / cached idempotency_key)
  ┌───────────────┴───────────────┐
  ▼ (Duplicate Key)               ▼ (New Key)
Return Cached Response     Allocate workflow_id & trace_id
                                  │
                                  ▼
                    Execution Mode Inspection
                    ┌─────────────┴─────────────┐
                    ▼ (SYNCHRONOUS)             ▼ (ASYNCHRONOUS)
               In-band execution         Dispatch to Background
             Return 200 OK + Result      Return 202 Accepted + wfk_id
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
                         AMIP Execution Worker
                    ┌───────────────────────────┐
                    │ 1. Initial Checkpoint     │
                    │ 2. Periodic Heartbeat     │
                    │ 3. Task-by-Task Progress  │
                    │ 4. Final Snapshot & Log   │
                    └───────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
       FastAPI Server Restart         Operator Override
   (Startup Reconciliation Sweep)   (Atomic Version Check)
```

---

## 8. Components to Create & Modify

### New Components
1. **`backend/app/services/amip/runtime/async_worker.py`** [NEW]:
   - Thread-safe background execution manager for async workflows.
2. **`backend/app/services/amip/runtime/idempotency_manager.py`** [NEW]:
   - In-memory / database lease cache with TTL expiry (15m window).
3. **`backend/app/services/amip/runtime/recovery_service.py`** [NEW]:
   - Startup zombie workflow reconciliation and lease timeout sweeper.
4. **`backend/app/services/amip/tests/test_amip_recovery_and_durability.py`** [NEW]:
   - Test suite for async dispatch, idempotency, zombie recovery, and optimistic locking.

### Modified Components
1. **`backend/app/schemas/amip_workflow.py`** [MODIFY]:
   - Add `idempotency_key: Optional[str] = None` to `WorkflowExecutionRequest`.
2. **`backend/app/services/amip/gateway/workflow_gateway.py`** [MODIFY]:
   - Integrate `IdempotencyManager`, `AsyncWorker`, and `RecoveryService`.
   - Update `execute_workflow()` to branch for `ASYNCHRONOUS` mode.
   - Update `submit_human_override()` with atomic status verification.
3. **`backend/app/main.py`** [MODIFY]:
   - Invoke `RecoveryService.reconcile_zombie_workflows()` on application startup.
4. **`frontend/src/pages/AMIPControlCenterPage.jsx`** [MODIFY]:
   - Add Idempotency Key input option in Trigger Workflow Modal.
   - Display `202 Accepted` / `RUNNING` status banner for asynchronous jobs.

---

## 9. Database, Security & Concurrency Considerations

- **Database Changes**: **ZERO new tables required.**
  - Heartbeat timestamp and idempotency key are stored in the existing `metadata_json` field of `AMIPWorkflowExecution`.
- **Security**: Idempotency keys are scoped to the authenticated tenant/user.
- **Concurrency**: Background workers use thread-safe queues and isolated DB session contexts.
- **Non-Blocking Observability**: Failure in lease caching or heartbeat recording never interrupts the core business execution.

---

## 10. Backward Compatibility & Exclusions

- **Backward Compatibility**: All existing Checkpoint 8.1–8.5 endpoints retain 100% contract compatibility. If `idempotency_key` is omitted, behavior defaults to standard execution.
- **Explicit Exclusions**:
  - Do NOT modify existing ERP billing orchestrators (`ValidationOrchestrator`, `BulkImportService`).
  - Do NOT introduce external queue servers (RabbitMQ/Redis/Celery) — use Python's robust in-process asynchronous thread pool worker.
  - Do NOT introduce external AI/LLM API calls.

---

## 11. Testing Strategy

1. **Async Worker Execution**: Test `execution_mode=ASYNCHRONOUS` returns status `RUNNING` immediately and transitions to `COMPLETED` in background.
2. **Idempotency Deduplication**: Test duplicate POST with same `idempotency_key` returns the identical `workflow_id` and cached response.
3. **Zombie Reconciliation**: Test startup sweeper detects simulated `RUNNING` workflows with expired heartbeats and marks them `STALE_TERMINATED`.
4. **Atomic Override**: Test concurrent override submissions on a single workflow allow exactly one winner.
5. **Full Regression**: Maintain 100% pass rate on all 153 existing backend tests.

---

## 12. Recommended Implementation Sequence

1. Create `idempotency_manager.py`, `async_worker.py`, and `recovery_service.py` under `backend/app/services/amip/runtime/`.
2. Update `WorkflowExecutionRequest` in `amip_workflow.py` with `idempotency_key`.
3. Integrate async execution, step checkpointing, and idempotency into `AMIPWorkflowGateway`.
4. Wire startup recovery into `backend/app/main.py`.
5. Create comprehensive test suite `test_amip_recovery_and_durability.py`.
6. Update frontend `AMIPControlCenterPage.jsx` with async state polling and idempotency key input.
7. Run verification suite (`pytest`, `node --check`, `npm run build`) and produce `CHECKPOINT_8_6_REPORT.md`.
