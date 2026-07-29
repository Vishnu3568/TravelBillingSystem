"""
AMIP Platform Enumerations.
Defines core statuses, priority levels, task types, execution modes, decision policies, and planning strategies.
"""
from __future__ import annotations
from enum import Enum


class ExecutionStatus(str, Enum):
    """Lifecycle status of an execution workflow context."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DEGRADED = "DEGRADED"
    REJECTED = "REJECTED"


class TaskType(str, Enum):
    """Categorization of tasks processed by the platform."""
    DOCUMENT_IMPORT = "DOCUMENT_IMPORT"
    COPILOT_CHAT = "COPILOT_CHAT"
    PREDICTIVE_FORECAST = "PREDICTIVE_FORECAST"
    GRAPH_QUERY = "GRAPH_QUERY"
    REVIEW_CORRECTION = "REVIEW_CORRECTION"
    GENERAL_QUERY = "GENERAL_QUERY"


class Priority(str, Enum):
    """Priority level assigned to execution tasks."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionMode(str, Enum):
    """Execution dispatch mode for processing tasks."""
    SYNCHRONOUS = "SYNCHRONOUS"
    ASYNCHRONOUS = "ASYNCHRONOUS"
    BATCH = "BATCH"
    DEGRADED = "DEGRADED"


class AgentStatus(str, Enum):
    """Execution state of an individual agent step."""
    IDLE = "IDLE"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"


class DecisionStatus(str, Enum):
    """Status of an AMIP decision evaluation process."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class DecisionPolicy(str, Enum):
    """Policy resolution rule for AMIP consensus decision making."""
    AUTO_APPROVE = "AUTO_APPROVE"
    AUTO_REVIEW = "AUTO_REVIEW"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    AUTO_REJECT = "AUTO_REJECT"


class PlanningStrategy(str, Enum):
    """Execution strategy for scheduling and sequencing plan tasks."""
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    HYBRID = "HYBRID"
