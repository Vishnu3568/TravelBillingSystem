"""
SQLAlchemy Implementation of AMIP Observability Repository.
Provides fault-isolated, sanitized, and short-lived session persistence for workflow executions, logs, and trace spans.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.amip_observability import (
    AMIPWorkflowExecution,
    AMIPExecutionLog,
    AMIPTraceSpan,
)
from app.services.amip.interfaces.observability_repository_interface import (
    IObservabilityRepository,
)

logger = logging.getLogger("amip_persistence")

_REDACTION_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "secret",
    "api_key",
    "authorization",
    "auth",
    "credential",
    "credentials",
    "raw_content",
    "raw_text",
}


def sanitize_payload(val: Any) -> Any:
    """
    Recursively redacts sensitive keys (passwords, tokens, API keys, secrets, raw document text)
    from dictionaries and lists before persistence.
    """
    if isinstance(val, dict):
        sanitized = {}
        for k, v in val.items():
            if str(k).lower() in _REDACTION_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_payload(v)
        return sanitized
    elif isinstance(val, list):
        return [sanitize_payload(item) for item in val]
    return val


class SQLAlchemyObservabilityRepository(IObservabilityRepository):
    """
    Production SQLAlchemy persistence layer for AMIP Observability.
    Guarantees non-blocking fault isolation: database errors degrade telemetry logging
    without failing or altering autonomous workflow execution.
    """

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def save_workflow_execution(self, execution_data: Dict[str, Any]) -> bool:
        """
        Persists or updates an autonomous workflow execution record.
        Fault-isolated: returns False on failure without raising exceptions.
        """
        db: Optional[Session] = None
        try:
            clean_data = sanitize_payload(execution_data)
            exec_id = str(clean_data.get("execution_id") or clean_data.get("snapshot_id") or f"exe-{clean_data.get('workflow_id', 'unknown')}")
            wfk_id = str(clean_data.get("workflow_id", ""))
            trc_id = clean_data.get("trace_id")
            status = str(clean_data.get("status", "COMPLETED"))
            current_task = str(clean_data.get("current_task", ""))

            completed_tasks = clean_data.get("completed_tasks", [])
            pending_tasks = clean_data.get("pending_tasks", [])
            agent_states = clean_data.get("agent_states", {})
            retry_counts = clean_data.get("retry_counts", {})
            duration_ms = clean_data.get("duration_ms")
            if duration_ms is None and isinstance(clean_data.get("runtime_metrics"), dict):
                duration_ms = clean_data["runtime_metrics"].get("duration_ms")

            db = self.session_factory()
            existing = db.query(AMIPWorkflowExecution).filter(
                (AMIPWorkflowExecution.execution_id == exec_id) | (AMIPWorkflowExecution.workflow_id == wfk_id)
            ).first()

            if existing:
                existing.status = status
                existing.current_task = current_task
                existing.completed_tasks_json = json.dumps(completed_tasks)
                existing.pending_tasks_json = json.dumps(pending_tasks)
                existing.agent_states_json = json.dumps(agent_states)
                existing.retry_counts_json = json.dumps(retry_counts)
                if duration_ms is not None:
                    existing.duration_ms = float(duration_ms)
                if status in ("COMPLETED", "FAILED", "CANCELLED") and not existing.completed_at:
                    existing.completed_at = datetime.utcnow()
            else:
                new_record = AMIPWorkflowExecution(
                    execution_id=exec_id,
                    workflow_id=wfk_id,
                    trace_id=trc_id,
                    status=status,
                    current_task=current_task,
                    completed_tasks_json=json.dumps(completed_tasks),
                    pending_tasks_json=json.dumps(pending_tasks),
                    agent_states_json=json.dumps(agent_states),
                    retry_counts_json=json.dumps(retry_counts),
                    duration_ms=float(duration_ms) if duration_ms is not None else None,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow() if status in ("COMPLETED", "FAILED", "CANCELLED") else None,
                )
                db.add(new_record)

            db.commit()
            return True
        except Exception as e:
            logger.warning(f"Telemetry persistence degraded: Failed to save workflow execution: {e}")
            if db:
                try:
                    db.rollback()
                except Exception:
                    pass
            return False
        finally:
            if db:
                db.close()

    def save_structured_log(self, log_record: Dict[str, Any]) -> bool:
        """
        Persists a single structured telemetry log record.
        Fault-isolated: returns False on failure without raising exceptions.
        """
        db: Optional[Session] = None
        try:
            clean_log = sanitize_payload(log_record)
            wfk_id = str(clean_log.get("workflow_id", ""))
            trc_id = clean_log.get("trace_id")
            task_id = clean_log.get("task_id")
            agent_name = clean_log.get("agent_name")
            level = str(clean_log.get("level", "INFO")).upper()
            message = str(clean_log.get("message", ""))
            exec_time = float(clean_log.get("execution_time_ms", 0.0))
            status = str(clean_log.get("status", "COMPLETED"))
            metadata = clean_log.get("metadata", {})

            db = self.session_factory()
            new_log = AMIPExecutionLog(
                workflow_id=wfk_id,
                trace_id=trc_id,
                task_id=task_id,
                agent_name=agent_name,
                level=level,
                message=message,
                execution_time_ms=exec_time,
                status=status,
                metadata_json=json.dumps(metadata) if metadata else None,
                timestamp=datetime.utcnow(),
            )
            db.add(new_log)
            db.commit()
            return True
        except Exception as e:
            logger.warning(f"Telemetry persistence degraded: Failed to save log record: {e}")
            if db:
                try:
                    db.rollback()
                except Exception:
                    pass
            return False
        finally:
            if db:
                db.close()

    def save_trace_span(self, span_data: Dict[str, Any]) -> bool:
        """
        Persists a telemetry trace span.
        Fault-isolated: handles duplicate span_id and returns False on failure.
        """
        db: Optional[Session] = None
        try:
            clean_span = sanitize_payload(span_data)
            span_id = str(clean_span.get("span_id", ""))
            trace_id = str(clean_span.get("trace_id", ""))
            parent_span_id = clean_span.get("parent_span_id")
            name = str(clean_span.get("name", "UnnamedSpan"))
            metadata = clean_span.get("metadata", {})

            db = self.session_factory()
            existing = db.query(AMIPTraceSpan).filter(AMIPTraceSpan.span_id == span_id).first()
            if existing:
                existing.name = name
                existing.metadata_json = json.dumps(metadata) if metadata else None
            else:
                new_span = AMIPTraceSpan(
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    name=name,
                    metadata_json=json.dumps(metadata) if metadata else None,
                    timestamp=datetime.utcnow(),
                )
                db.add(new_span)

            db.commit()
            return True
        except Exception as e:
            logger.warning(f"Telemetry persistence degraded: Failed to save trace span: {e}")
            if db:
                try:
                    db.rollback()
                except Exception:
                    pass
            return False
        finally:
            if db:
                db.close()

    def get_workflow_executions(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Queries historical workflow executions with pagination.
        Fault-isolated: returns empty list on failure.
        """
        db: Optional[Session] = None
        try:
            db = self.session_factory()
            query = db.query(AMIPWorkflowExecution)
            if status:
                query = query.filter(AMIPWorkflowExecution.status == status.upper())

            records = query.order_by(AMIPWorkflowExecution.started_at.desc()).offset(offset).limit(limit).all()
            results = []
            for r in records:
                results.append(self._format_workflow_record(r))
            return results
        except Exception as e:
            logger.warning(f"Telemetry persistence query failed: {e}")
            return []
        finally:
            if db:
                db.close()

    def get_workflow_execution_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest execution state for a specific workflow_id or execution_id.
        Fault-isolated: returns None on failure.
        """
        db: Optional[Session] = None
        try:
            db = self.session_factory()
            record = db.query(AMIPWorkflowExecution).filter(
                (AMIPWorkflowExecution.workflow_id == workflow_id) | (AMIPWorkflowExecution.execution_id == workflow_id)
            ).first()
            if not record:
                return None
            return self._format_workflow_record(record)
        except Exception as e:
            logger.warning(f"Telemetry persistence query failed for workflow '{workflow_id}': {e}")
            return None
        finally:
            if db:
                db.close()

    def get_logs_by_workflow_id(
        self,
        workflow_id: str,
        level: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves structured log records for a specific workflow.
        Fault-isolated: returns empty list on failure.
        """
        db: Optional[Session] = None
        try:
            db = self.session_factory()
            query = db.query(AMIPExecutionLog).filter(AMIPExecutionLog.workflow_id == workflow_id)
            if level:
                query = query.filter(AMIPExecutionLog.level == level.upper())

            records = query.order_by(AMIPExecutionLog.timestamp.asc()).limit(limit).all()
            results = []
            for r in records:
                meta = json.loads(r.metadata_json) if r.metadata_json else {}
                results.append({
                    "message": r.message,
                    "level": r.level,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                    "trace_id": r.trace_id or "",
                    "workflow_id": r.workflow_id,
                    "task_id": r.task_id or "",
                    "agent_name": r.agent_name or "",
                    "execution_time_ms": r.execution_time_ms,
                    "status": r.status,
                    "metadata": meta,
                })
            return results
        except Exception as e:
            logger.warning(f"Telemetry persistence query failed for logs of '{workflow_id}': {e}")
            return []
        finally:
            if db:
                db.close()

    def get_trace_spans_by_trace_id(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all spans registered under a specific trace_id.
        Fault-isolated: returns empty list on failure.
        """
        db: Optional[Session] = None
        try:
            db = self.session_factory()
            records = db.query(AMIPTraceSpan).filter(AMIPTraceSpan.trace_id == trace_id).all()
            results = []
            for r in records:
                meta = json.loads(r.metadata_json) if r.metadata_json else {}
                results.append({
                    "span_id": r.span_id,
                    "name": r.name,
                    "trace_id": r.trace_id,
                    "parent_span_id": r.parent_span_id,
                    "metadata": meta,
                })
            return results
        except Exception as e:
            logger.warning(f"Telemetry persistence query failed for trace spans of '{trace_id}': {e}")
            return []
        finally:
            if db:
                db.close()

    def cleanup_old_records(
        self,
        workflow_days: int = 90,
        log_days: int = 30,
        span_days: int = 30,
    ) -> Dict[str, int]:
        """
        Cleans up expired historical observability records according to retention policy.
        - Workflows: 90 days
        - Logs: 30 days
        - Trace Spans: 30 days
        Fault-isolated: returns deleted counts or zeros on failure.
        """
        db: Optional[Session] = None
        counts = {"deleted_workflows": 0, "deleted_logs": 0, "deleted_spans": 0}
        try:
            db = self.session_factory()
            wf_cutoff = datetime.utcnow() - timedelta(days=workflow_days)
            log_cutoff = datetime.utcnow() - timedelta(days=log_days)
            span_cutoff = datetime.utcnow() - timedelta(days=span_days)

            wf_del = db.query(AMIPWorkflowExecution).filter(AMIPWorkflowExecution.started_at < wf_cutoff).delete(synchronize_session=False)
            log_del = db.query(AMIPExecutionLog).filter(AMIPExecutionLog.timestamp < log_cutoff).delete(synchronize_session=False)
            span_del = db.query(AMIPTraceSpan).filter(AMIPTraceSpan.timestamp < span_cutoff).delete(synchronize_session=False)

            db.commit()
            counts["deleted_workflows"] = wf_del
            counts["deleted_logs"] = log_del
            counts["deleted_spans"] = span_del
            return counts
        except Exception as e:
            logger.warning(f"Telemetry retention cleanup failed: {e}")
            if db:
                try:
                    db.rollback()
                except Exception:
                    pass
            return counts
        finally:
            if db:
                db.close()

    @staticmethod
    def _format_workflow_record(r: AMIPWorkflowExecution) -> Dict[str, Any]:
        """Helper to format AMIPWorkflowExecution model into a standardized dictionary."""
        completed_tasks = json.loads(r.completed_tasks_json) if r.completed_tasks_json else []
        pending_tasks = json.loads(r.pending_tasks_json) if r.pending_tasks_json else []
        agent_states = json.loads(r.agent_states_json) if r.agent_states_json else {}
        retry_counts = json.loads(r.retry_counts_json) if r.retry_counts_json else {}

        return {
            "snapshot_id": r.execution_id,
            "execution_id": r.execution_id,
            "workflow_id": r.workflow_id,
            "trace_id": r.trace_id or "",
            "status": r.status,
            "current_task": r.current_task or "",
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "agent_states": agent_states,
            "retry_counts": retry_counts,
            "duration_ms": r.duration_ms or 0.0,
            "timestamp": r.started_at.isoformat() if r.started_at else "",
            "started_at": r.started_at.isoformat() if r.started_at else "",
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "timeline_records_count": len(completed_tasks) + len(pending_tasks),
            "runtime_metrics": {"duration_ms": r.duration_ms or 0.0},
            "memory_stats": {"active_threads": 1},
        }
