"""
AMIP platform enums for execution status, task types, priority levels, and decision policies.
"""
from __future__ import annotations
from enum import Enum


class ExecutionStatus(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DEGRADED = "DEGRADED"
    REJECTED = "REJECTED"


class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskType(str, Enum):
    DOCUMENT_IMPORT = "DOCUMENT_IMPORT"
    COPILOT_CHAT = "COPILOT_CHAT"
    PREDICTIVE_FORECAST = "PREDICTIVE_FORECAST"
    GRAPH_QUERY = "GRAPH_QUERY"
    REVIEW_CORRECTION = "REVIEW_CORRECTION"
    GENERAL_QUERY = "GENERAL_QUERY"
    VALIDATION_ENGINE = "VALIDATION_ENGINE"


class Priority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionMode(str, Enum):
    SYNCHRONOUS = "SYNCHRONOUS"
    ASYNCHRONOUS = "ASYNCHRONOUS"
    BATCH = "BATCH"
    DEGRADED = "DEGRADED"


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"


class DecisionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"


class DecisionPolicy(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"
    AUTO_REVIEW = "AUTO_REVIEW"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    AUTO_REJECT = "AUTO_REJECT"


class PlanningStrategy(str, Enum):
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    HYBRID = "HYBRID"


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
