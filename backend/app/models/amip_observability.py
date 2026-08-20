"""
SQLAlchemy ORM Models for AMIP Persistent Observability & Audit History.
Defines tables for workflow executions, structured execution logs, and trace spans.
"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from app.database import Base


class AMIPWorkflowExecution(Base):
    """
    Persisted point-in-time and completion state of autonomous workflow executions.
    """
    __tablename__ = "amip_workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(64), unique=True, index=True, nullable=False)
    workflow_id = Column(String(64), index=True, nullable=False)
    trace_id = Column(String(64), index=True, nullable=True)
    status = Column(String(32), index=True, nullable=False, default="RUNNING")
    current_task = Column(String(255), nullable=True)
    completed_tasks_json = Column(Text, nullable=True)
    pending_tasks_json = Column(Text, nullable=True)
    agent_states_json = Column(Text, nullable=True)
    retry_counts_json = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class AMIPExecutionLog(Base):
    """
    Persisted structured telemetry log records emitted during AMIP agent and workflow execution.
    """
    __tablename__ = "amip_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(64), index=True, nullable=False)
    trace_id = Column(String(64), index=True, nullable=True)
    task_id = Column(String(64), nullable=True)
    agent_name = Column(String(128), index=True, nullable=True)
    level = Column(String(16), index=True, nullable=False, default="INFO")
    message = Column(Text, nullable=False)
    execution_time_ms = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), nullable=False, default="COMPLETED")
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)


class AMIPTraceSpan(Base):
    """
    Persisted hierarchical telemetry spans for distributed tracing and correlation.
    """
    __tablename__ = "amip_trace_spans"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(64), index=True, nullable=False)
    span_id = Column(String(64), unique=True, index=True, nullable=False)
    parent_span_id = Column(String(64), index=True, nullable=True)
    name = Column(String(255), nullable=False)
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
