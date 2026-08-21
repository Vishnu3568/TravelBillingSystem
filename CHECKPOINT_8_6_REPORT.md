# AMIP CHECKPOINT 8.6 REPORT — WORKFLOW DURABILITY, IDEMPOTENCY & FAULT-TOLERANT RECOVERY RUNTIME

## 1. Executive Summary

AMIP Checkpoint 8.6 hardens the execution runtime beneath the operational control plane. It resolves key production edge cases:
- **True Asynchronous Execution**: Workflows dispatched with `execution_mode: "ASYNCHRONOUS"` return immediately (`202 Accepted` / status `RUNNING`) to the caller, executing to completion in the background thread pool without blocking the HTTP request thread.
- **Idempotency & Deduplication**: Added `idempotency_key` support across schemas, runtime lease management, and gateway execution. Duplicate requests return cached responses or in-flight references without re-running tasks.
- **Fault-Tolerant Startup Recovery**: `RecoveryService` sweeps for orphaned `RUNNING` or `CANCELLING` workflow records on startup whose heartbeat lease has expired, transitioning them to `STALE_TERMINATED` with auditable telemetry.
- **Atomic HITL Override State Transitions**: Implemented mutual exclusion around operator reviews (`APPROVE`, `REJECT`, `ESCALATE`) to guarantee atomic resolution under concurrent operator actions.
- **Intermediate Step Checkpointing**: Workflows record point-in-time progress (`current_task`, `completed_tasks`, `agent_states`, `heartbeat_at`) immediately upon dispatch and at completion.

---

## 2. Verification Gates & Test Results

| Gate | Requirement | Test Case | Outcome |
| :--- | :--- | :--- | :--- |
| **1. Async Dispatch** | Non-blocking immediate return with background thread execution | `test_async_workflow_dispatch_is_non_blocking` | **PASSED (< 0.25s return, background completion verified)** |
| **2. Same Idempotency Key** | Returns identical cached workflow without re-executing | `test_same_idempotency_key_returns_identical_execution` | **PASSED (exact same workflow_id & timestamp)** |
| **3. Different Idempotency Keys** | Spawns distinct, independent workflow executions | `test_different_idempotency_keys_produce_independent_executions` | **PASSED (independent executions)** |
| **4. Startup Stale Recovery** | Detects & reconciles orphaned `RUNNING` workflows after crash | `test_startup_reconciliation_cleans_stale_zombie_workflows` | **PASSED (transitions to STALE_TERMINATED with audit log)** |
| **5. Atomic HITL Overrides** | Concurrent overrides on same review item allow only 1 winner | `test_concurrent_hitl_overrides_atomic_resolution` | **PASSED (winner gets 200, loser gets 400)** |
| **6. Checkpoint Persistence** | Initial state persisted immediately upon starting | `test_workflow_initial_checkpoint_persisted` | **PASSED (persisted in DB)** |
| **7. Fault Isolation** | Telemetry/database failure never disrupts business workflow | `test_durability_fault_isolation_on_db_error` | **PASSED (workflow completes cleanly)** |
| **8. Full Regression** | All platform tests pass without degradation | `pytest backend/tests backend/app/services/amip/tests` | **160 / 160 PASSED (100%)** |

---

## 3. Files Created & Modified

### Backend Core
- `backend/app/services/amip/runtime/__init__.py` [NEW]
- `backend/app/services/amip/runtime/idempotency_manager.py` [NEW]
- `backend/app/services/amip/runtime/async_worker.py` [NEW]
- `backend/app/services/amip/runtime/recovery_service.py` [NEW]
- `backend/app/schemas/amip_workflow.py` [MODIFY] (Added `idempotency_key`)
- `backend/app/services/amip/gateway/workflow_gateway.py` [MODIFY] (Integrated async worker, idempotency manager, atomic lock)
- `backend/app/services/amip/persistence/observability_repository.py` [MODIFY] (Added `get_workflow_execution` alias and custom `started_at` support)
- `backend/app/main.py` [MODIFY] (Wired startup recovery sweep and shutdown worker hook)

### Tests
- `backend/app/services/amip/tests/test_amip_recovery_and_durability.py` [NEW] (7 new durability and concurrency tests)

### Frontend
- `frontend/src/pages/AMIPControlCenterPage.jsx` [MODIFY] (Added optional `idempotency_key` input in workflow trigger modal)

### Documentation
- `CHECKPOINT_8_6_ARCHITECTURE.md` [NEW]
- `CHECKPOINT_8_6_REPORT.md` [NEW]

---

## 4. Platform Baseline Status

- **Backend Pytest Suite**: **160 / 160 PASSED** (13.56s)
- **Node AI Server Syntax**: **PASS (Exit 0)**
- **Frontend Production Build**: **PASS (Exit 0)** (890 modules transformed)
- **Git Working Tree**: Clean diff format, pending user review and commit authorization.
