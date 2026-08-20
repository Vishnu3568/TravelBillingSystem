# AMIP CHECKPOINT 8.3 — PERSISTENT OBSERVABILITY ARCHITECTURE

## 1. Current Architecture

The Travel Billing System currently operates on a hybrid enterprise architecture:
- **Database**: MySQL 8.0+ (`travelbillingdb` on port 3306) accessed via SQLAlchemy ORM (`pymysql` driver).
- **Backend**: FastAPI running on Python 3.10+ (Port 9000).
- **AMIP Platform**: Autonomous Multi-Agent Intelligence Platform operating under `backend/app/services/amip/`.

### Current Observability State (Checkpoint 8.1 & 8.2)
In Checkpoint 8.1, thread-safe in-memory telemetry structures were implemented (`MetricsCollector`, `TraceManager`, `StructuredLogger`, `ExecutionSnapshot`, `PerformanceProfiler`, `DiagnosticsEngine`). In Checkpoint 8.2, these components were exposed via authenticated REST endpoints (`/api/amip/health`, `/api/amip/metrics`, `/api/amip/executions`, `/api/amip/executions/{id}/logs`, `/api/amip/traces/{id}`, `/api/amip/diagnostics`).

**Identified Limitation**: Observability state currently resides purely in Python heap memory (`dict` and `list` structures). When the backend restarts, historical workflow executions, trace span hierarchies, and structured logs are cleared.

---

## 2. Existing Observability Data Mapping

Audit of in-memory telemetry structures created in Checkpoint 8.1 & 8.2:

| Component | Class Name | In-Memory Data Fields | Lifecycle / Retention |
| :--- | :--- | :--- | :--- |
| **Workflow State** | `ExecutionSnapshot` | `snapshot_id`, `timestamp`, `workflow_id`, `current_task`, `completed_tasks`, `pending_tasks`, `agent_states`, `timeline_records_count`, `runtime_metrics`, `memory_stats`, `retry_counts` | Memory dict (max 1,000 snapshots) |
| **Structured Logs** | `StructuredLogRecord` | `message`, `level`, `timestamp`, `trace_id`, `workflow_id`, `task_id`, `agent_name`, `execution_time_ms`, `status`, `metadata` | Memory list (max 5,000 records) |
| **Trace Hierarchy** | `TraceManager` | `span_id`, `name`, `trace_id`, `parent_span_id`, `metadata` | Memory dict (`_spans`) |
| **Metrics Summary** | `MetricsCollector` | `active_workflows`, `completed_workflows`, `failed_workflows`, `total_retries`, `success_rate`, `workflow_durations`, `agent_durations` | Cumulative atomic counters |

---

## 3. Database Persistence Architecture

### Existing Database Patterns
- **Connection Management**: `create_engine` in `backend/app/database.py` with `pool_size=10`, `max_overflow=20`, `pool_recycle=3600`, `pool_pre_ping=True`.
- **Model Declarations**: Inherit from `Base = declarative_base()`.
- **Table Initialization**: Replicates Spring Boot's `ddl-auto=update` via `Base.metadata.create_all(bind=engine)` on FastAPI `startup` event.
- **Session Lifecycle**: `SessionLocal = sessionmaker(...)` with standard `get_db()` dependency generator.
- **Migrations**: No Alembic directory exists. Tables are registered directly in SQLAlchemy `Base.metadata` and created automatically on startup.
- **JSON Column Pattern**: Complex nested structures (e.g. layout maps, confidence histories, graph relationships) use `Text` or `JSON` columns with explicit `json.dumps()` / `json.loads()` serialization.

---

## 4. Proposed Persistence Architecture

To introduce durable audit history without introducing tight coupling or performance overhead into workflow execution, we propose a **Non-Blocking Telemetry Persistence Adapter**:

```text
       AMIP Workflow Execution Engine / Supervisor
                          │
                          ▼
            In-Memory Observability Layer
    (MetricsCollector, StructuredLogger, TraceManager)
                          │
                          ▼
             AMIP Monitoring Service
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    In-Memory Response           Non-Blocking Async Worker
  (Instant REST Reads 0ms)             │
                                       ▼
                            Observability Repository
                           (IObservabilityRepository)
                                       │
                                       ▼
                              SQLAlchemy ORM Session
                                       │
                                       ▼
                                 MySQL Database
                            (amip_workflow_executions,
                             amip_execution_logs,
                             amip_trace_spans)
```

---

## 5. Proposed Database Schema

To prevent table explosion and redundant data storage, we propose **3 concise, indexed tables**:

### 1. `amip_workflow_executions`
Stores point-in-time and final execution state of autonomous workflows.

```sql
CREATE TABLE amip_workflow_executions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    execution_id VARCHAR(64) NOT NULL UNIQUE,
    workflow_id VARCHAR(64) NOT NULL,
    trace_id VARCHAR(64) NULL,
    status VARCHAR(32) NOT NULL, -- RUNNING, COMPLETED, FAILED, CANCELLED
    current_task VARCHAR(255) NULL,
    completed_tasks_json TEXT NULL, -- JSON array of task IDs
    pending_tasks_json TEXT NULL,   -- JSON array of task IDs
    agent_states_json TEXT NULL,    -- JSON dict of agent_name -> status
    retry_counts_json TEXT NULL,    -- JSON dict of task_id -> retries
    duration_ms DOUBLE NULL,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    INDEX idx_amip_wf_id (workflow_id),
    INDEX idx_amip_wf_trace (trace_id),
    INDEX idx_amip_wf_status (status),
    INDEX idx_amip_wf_started (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. `amip_execution_logs`
Stores structured telemetry log records emitted by specialized agents and orchestrators.

```sql
CREATE TABLE amip_execution_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workflow_id VARCHAR(64) NOT NULL,
    trace_id VARCHAR(64) NULL,
    task_id VARCHAR(64) NULL,
    agent_name VARCHAR(128) NULL,
    level VARCHAR(16) NOT NULL, -- INFO, DEBUG, WARNING, ERROR, CRITICAL
    message TEXT NOT NULL,
    execution_time_ms DOUBLE NOT NULL DEFAULT 0.0,
    status VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    metadata_json TEXT NULL,    -- JSON dictionary of metadata
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_amip_log_wf (workflow_id),
    INDEX idx_amip_log_trace (trace_id),
    INDEX idx_amip_log_agent (agent_name),
    INDEX idx_amip_log_level (level),
    INDEX idx_amip_log_ts (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3. `amip_trace_spans`
Stores hierarchical telemetry spans for distributed tracing and correlation.

```sql
CREATE TABLE amip_trace_spans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    span_id VARCHAR(64) NOT NULL UNIQUE,
    parent_span_id VARCHAR(64) NULL,
    name VARCHAR(255) NOT NULL,
    metadata_json TEXT NULL,    -- JSON dictionary of span metadata
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_amip_span_trace (trace_id),
    INDEX idx_amip_span_parent (parent_span_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 6. Repository Interface Design

An abstract interface `IObservabilityRepository` will decouple the AMIP observability layer from SQLAlchemy:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IObservabilityRepository(ABC):
    @abstractmethod
    def save_execution_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """Persists or updates a workflow execution snapshot."""
        pass

    @abstractmethod
    def save_log_record(self, log_record: Dict[str, Any]) -> bool:
        """Persists a single structured log record."""
        pass

    @abstractmethod
    def save_trace_span(self, span_data: Dict[str, Any]) -> bool:
        """Persists a telemetry trace span."""
        pass

    @abstractmethod
    def get_execution_history(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries historical workflow executions with pagination."""
        pass

    @abstractmethod
    def get_workflow_logs(self, workflow_id: str, level: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Queries historical structured logs for a workflow."""
        pass

    @abstractmethod
    def get_trace_spans(self, trace_id: str) -> List[Dict[str, Any]]:
        """Queries historical trace spans for a trace ID."""
        pass
```

---

## 7. Data Flow

1. **Workflow Event Trigger**: An AMIP workflow starts, executes tasks, or logs progress.
2. **Instant Memory Update**: The event is immediately recorded in memory (`StructuredLogger`, `MetricsCollector`, `TraceManager`), providing instant 0ms REST query performance for real-time monitoring.
3. **Async Persistence Queue**: An asynchronous worker task (or background thread worker pool) receives a copy of the sanitized telemetry event.
4. **Database Commit**: The worker acquires a short-lived SQLAlchemy session (`SessionLocal()`) and performs an `INSERT` or `UPDATE` into `amip_workflow_executions`, `amip_execution_logs`, or `amip_trace_spans`.
5. **Fallback Read**: REST endpoints in `AMIPMonitoringService` read from memory first. If historical data beyond current memory retention is requested, the service queries `IObservabilityRepository`.

---

## 8. Failure Handling & Non-Blocking Isolation

> **CRITICAL RESILIENCE REQUIREMENT**: Telemetry persistence failures MUST NEVER crash or delay an autonomous AI workflow.

### Fault Isolation Protocol:
1. **Try-Except Boundary**: Every database write operation inside `ObservabilityRepository` is wrapped in a strict `try-except Exception` block.
2. **Silent Degradation**: If MySQL drops connection, is locked, or experiences a disk error during a telemetry write, the repository logs a local warning and returns `False`.
3. **Zero Impact on Execution Engine**: The calling workflow continues execution without throwing exceptions or delaying step transitions.
4. **Connection Pool Safety**: Telemetry writes use dedicated short-lived sessions with `pool_pre_ping=True` so they do not exhaust main transaction connection pools.

---

## 9. Retention & Archival Strategy

1. **Memory Retention**: Max 5,000 log records, 1,000 active snapshots in Python heap memory.
2. **Database Retention**:
   - `amip_execution_logs`: Retain for **30 days**.
   - `amip_trace_spans`: Retain for **30 days**.
   - `amip_workflow_executions`: Retain for **90 days**.
3. **Automated Maintenance Strategy**:
   - Introduce a lightweight periodic cleanup function `cleanup_expired_telemetry(db_session, days_to_keep=30)` that executes simple indexed batch deletes (`DELETE FROM amip_execution_logs WHERE timestamp < NOW() - INTERVAL 30 DAY LIMIT 1000`).

---

## 10. Security & Data Privacy

1. **Sanitization Boundary**: All telemetry payloads pass through `_sanitize_value` BEFORE ORM model instantiation.
2. **Redacted Keys**:
   - `password`, `password_hash`, `token`, `access_token`, `secret`, `api_key`, `authorization`, `credentials`, `raw_content`, `raw_text`.
   - Any value matching sensitive keys is replaced with `"[REDACTED]"`.
3. **No PII or Document Persistence**: Raw document OCR outputs, parsed customer document binaries, and user auth tokens are strictly excluded from database logging.

---

## 11. Performance Analysis

- **Write Latency Overhead**: 0ms on main workflow execution thread (handled asynchronously).
- **Database Query Latency**: <5ms for indexed lookups by `workflow_id`, `trace_id`, or `timestamp`.
- **Storage Footprint**:
  - `amip_workflow_executions`: ~1 KB per workflow (~1 MB per 1,000 workflows).
  - `amip_execution_logs`: ~500 B per log entry (~50 MB per 100,000 logs).
  - Total 30-day database overhead for 10,000 workflows: <100 MB.

---

## 12. Proposed API Enhancements

When Checkpoint 8.3 is eventually implemented, the existing Checkpoint 8.2 APIs will seamlessly support historical lookups:

```text
GET /api/amip/executions?limit=50&offset=0&status=FAILED
  └─ Returns active in-memory + historical workflow executions from DB.

GET /api/amip/executions/{workflow_id}/history
  └─ Returns historical execution snapshots and status transitions.

GET /api/amip/logs?workflow_id={id}&level=ERROR&limit=100
  └─ Queries persistent log history with pagination.
```

Existing APIs remain 100% backward-compatible.

---

## 13. Database Migration Strategy

Following the project's existing SQLAlchemy configuration:
1. Declare ORM models (`AMIPWorkflowExecutionModel`, `AMIPExecutionLogModel`, `AMIPTraceSpanModel`) in `backend/app/models/amip_observability.py`.
2. Import models in `backend/app/models/__init__.py`.
3. Startup auto-creation via `Base.metadata.create_all(bind=engine)` in `main.py` will create the 3 MySQL tables automatically on boot without breaking existing tables.

---

## 14. Test Strategy for Implementation Phase

1. **Repository Unit Tests**: Verify `save_execution_snapshot`, `save_log_record`, `save_trace_span`, and paginated queries with `SessionLocal`.
2. **Database Failure Resilience Test**: Mock `SessionLocal.commit` to raise `SQLAlchemyError` -> Verify workflow execution completes cleanly without exceptions.
3. **Sanitization Unit Test**: Pass sensitive keys (`password`, `api_key`) -> Verify saved database rows contain `"[REDACTED]"`.
4. **Full Regression Test**: Ensure all existing **133 / 133 backend tests** remain 100% passing.

---

## 15. Risk Assessment

| Potential Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| DB Connection Pool Exhaustion from log writes | Low | High | Use separate short-lived sessions & non-blocking async execution |
| Disk space growth from excessive debug logs | Medium | Low | Enforce 30-day retention cleanup & log level thresholds |
| Accidental secret persistence | Low | High | Enforce mandatory `_sanitize_value` before DB record creation |

---

## 16. Recommendation

**Proceed with Implementation of Checkpoint 8.3 upon approval.**

The design is minimal (3 tables), fault-isolated (0ms execution thread overhead), highly secure (automatic secret sanitization), and 100% aligned with the existing SQLAlchemy/MySQL architecture.
