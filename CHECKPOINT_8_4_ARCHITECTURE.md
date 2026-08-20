# AMIP CHECKPOINT 8.4 — AUTONOMOUS WORKFLOW GATEWAY & EXECUTION DISPATCHER

## 1. Proposed Title
**AMIP Checkpoint 8.4 — Autonomous Workflow Gateway & Execution Dispatcher**

---

## 2. Exact Objective
Provide a unified, secure, enterprise-grade execution gateway and dispatching layer that enables authorized operators and system services to trigger, track, control, and audit autonomous multi-agent workflows through dedicated REST endpoints.

This layer bridges the core AMIP intelligence engine (`AMIPSupervisor`, `ExecutionPlanner`, `ContextManager`, `DecisionMatrix`, `ExplainabilityEngine`, `ResilienceRuntime`) with the REST API layer and the persistent observability layer established in Checkpoint 8.3.

---

## 3. Why This Layer Belongs After Checkpoint 8.3
1. **Durable Telemetry Foundation Ready**: In Checkpoints 8.1, 8.2, and 8.3, we established the full observability, runtime monitoring, and persistent audit infrastructure (`amip_workflow_executions`, `amip_execution_logs`, `amip_trace_spans`).
2. **Safe Operational Execution**: With non-blocking persistence and fault isolation proven, the platform can now safely accept, orchestrate, and audit live workflow executions with guaranteed trace propagation, live telemetry logging, and durable audit history.
3. **Completes the AMIP Autonomous Lifecycle**:
   ```text
   Workflow Request Ingress (Checkpoint 8.4)
             ↓
   Adaptive Execution Planning (Checkpoint 3)
             ↓
   Supervisor Orchestration & Task Execution (Checkpoint 5)
             ↓
   Multi-Agent Decision Matrix & Consensus (Checkpoint 4)
             ↓
   Resilience & Circuit Breaking (Checkpoint 6)
             ↓
   Explainability Narrative & Audit Trail (Checkpoint 7)
             ↓
   Live Observability & Persistent History (Checkpoints 8.1 - 8.3)
             ↓
   Execution Audit Bundle Response (Checkpoint 8.4)
   ```

---

## 4. Components to Be Created

### A. `AMIPWorkflowGateway` (`backend/app/services/amip/gateway/workflow_gateway.py`)
The central facade coordinating end-to-end execution:
- **`execute_workflow(...)`**: Initializes execution context, generates dynamic execution plan, executes plan via supervisor, records trace spans and structured logs, renders narrative explanation, persists audit snapshots, and returns structured decision results.
- **`cancel_workflow(...)`**: Signals cancellation to active workflows using `CancellationToken`.
- **`get_workflow_audit_bundle(...)`**: Synthesizes a comprehensive audit bundle containing the decision result, narrative explanation, timeline events, and telemetry trace hierarchy.

### B. Typed Pydantic Schemas (`backend/app/schemas/amip_workflow.py`)
- `WorkflowExecutionRequest`: `task_type`, `summary`, `priority`, `execution_mode`, `timeout_ms`, `input_payload`.
- `WorkflowExecutionResponse`: `workflow_id`, `trace_id`, `status`, `confidence`, `recommended_action`, `reason`, `execution_duration_ms`, `evidence`.
- `WorkflowCancelResponse`: `workflow_id`, `status`, `message`, `cancelled_at`.
- `WorkflowAuditBundleResponse`: `workflow_id`, `trace_id`, `decision_result`, `explanation_report`, `timeline`, `spans`, `logs`.

### C. FastAPI Router (`backend/app/routers/amip_workflow.py` or extended `amip_monitoring.py`)
Exposing workflow dispatching and execution control endpoints.

---

## 5. Existing Components to Be Integrated

| Component | Source File | Role in Checkpoint 8.4 |
| :--- | :--- | :--- |
| **`AMIPSupervisor`** | `amip/supervisor/amip_supervisor.py` | Orchestrates context, plan execution, and decision resolution |
| **`ContextManager`** | `amip/context/context_manager.py` | Manages blackboard and execution context lifecycles |
| **`ExecutionPlanner`** | `amip/planner/execution_planner.py` | Synthesizes task dependency graphs and execution plans |
| **`ExplainabilityEngine`** | `amip/explainability/explainability_engine.py` | Generates narrative explanation reports and audit timelines |
| **`CancellationToken`** | `amip/resilience/cancellation_token.py` | Provides cooperative cancellation propagation |
| **`AMIPMonitoringService`** | `amip/monitoring_service.py` | Collects live telemetry metrics, logs, and trace spans |
| **`IObservabilityRepository`** | `amip/persistence/observability_repository.py` | Persists durable execution state, logs, and trace spans |

---

## 6. Files to Be Created
- `backend/app/schemas/amip_workflow.py`
- `backend/app/services/amip/gateway/__init__.py`
- `backend/app/services/amip/gateway/workflow_gateway.py`
- `backend/app/routers/amip_workflow.py`
- `backend/app/services/amip/tests/test_amip_workflow_gateway.py`
- `CHECKPOINT_8_4_REPORT.md`

---

## 7. Files to Be Modified
- `backend/app/main.py` (Register `amip_workflow_router`)

---

## 8. API Endpoints Required

| Method | Path | Response Model | Description | Auth Guard |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/amip/workflows/execute` | `WorkflowExecutionResponse` | Trigger an autonomous AMIP workflow | `OWNER`, `MANAGER` |
| `POST` | `/api/amip/workflows/{workflow_id}/cancel` | `WorkflowCancelResponse` | Cancel an active AMIP workflow execution | `OWNER`, `MANAGER` |
| `GET` | `/api/amip/workflows/{workflow_id}/audit` | `WorkflowAuditBundleResponse` | Retrieve complete decision, timeline, explanation, and trace audit bundle | `OWNER`, `MANAGER` |

---

## 9. Database Changes Required
**NONE.**
The 3 tables created in Checkpoint 8.3 (`amip_workflow_executions`, `amip_execution_logs`, `amip_trace_spans`) completely satisfy all storage requirements for workflow state, audit history, logs, and trace spans.

---

## 10. Security & Authorization Requirements
1. **Authentication**: All workflow execution, cancellation, and audit endpoints secured with `RoleChecker(["OWNER", "MANAGER"])`.
2. **Context Propagation**: Authenticated user's `username` and `role` are injected into `ExecutionContext`.
3. **Payload Sanitization**: All input payloads and outputs pass through `sanitize_payload()` before database persistence.

---

## 11. Failure & Resilience Considerations
1. **Non-Blocking Telemetry**: If database persistence fails during workflow execution, telemetry logging degrades gracefully without crashing the workflow.
2. **Timeout Enforcement**: If workflow exceeds `timeout_ms`, `TimeoutController` aborts execution cleanly.
3. **Cancellation Safety**: `cancel_workflow` marks cancellation token and updates supervisor state to `CANCELLED`.

---

## 12. Test Strategy
Create `backend/app/services/amip/tests/test_amip_workflow_gateway.py` covering:
- Synchronous & asynchronous workflow execution via gateway.
- High-confidence approval vs. conflicting review-required decision flows.
- Cooperative workflow cancellation.
- Complete audit bundle generation (Decision + Narrative + Timeline + Spans).
- Role authorization (401 unauthenticated, 403 employee, 200 manager/owner).
- Full regression verification (**142+ tests passing**).

---

## 13. Regression Risks
- **Risk**: Modifying existing billing/document routes.
- **Mitigation**: All new endpoints reside strictly under the `/api/amip/workflows/*` namespace. Zero modification to existing billing or ERP routers.

---

## 14. Explicit Boundaries (What Checkpoint 8.4 Must NOT Implement)
- Do NOT build frontend React UI components yet (UI dashboard will consume these APIs in the UI checkpoint).
- Do NOT rewrite or modify existing domain orchestrator business logic.
- Do NOT make external LLM/AI calls.
- Do NOT create new database tables.

---

## 15. Dependencies on Earlier Checkpoints
- Fully compatible with Checkpoint 8.1 (Observability), 8.2 (Monitoring APIs), and 8.3 (Persistence).

---

## 16. Recommended Implementation Sequence
1. Create typed Pydantic models in `backend/app/schemas/amip_workflow.py`.
2. Implement `AMIPWorkflowGateway` in `backend/app/services/amip/gateway/workflow_gateway.py`.
3. Implement `amip_workflow_router` in `backend/app/routers/amip_workflow.py`.
4. Register router in `backend/app/main.py`.
5. Implement unit & integration test suite `test_amip_workflow_gateway.py`.
6. Run full verification suite (pytest, node syntax check, frontend build).
7. Create `CHECKPOINT_8_4_REPORT.md`.
