"""
AMIP Platform Exception Definitions.
Defines core exceptions for AMIP context operations, decision calculations, execution planning, and supervisor orchestrations.
"""
from __future__ import annotations


class AmipBaseException(Exception):
    """Base exception for all AMIP platform errors."""
    pass


class ContextNotFound(AmipBaseException):
    """Raised when a requested execution context ID is not found in storage."""
    def __init__(self, context_id: str):
        self.context_id = context_id
        super().__init__(f"AMIP Execution Context '{context_id}' was not found.")


class ContextAlreadyExists(AmipBaseException):
    """Raised when attempting to create a context that already exists."""
    def __init__(self, context_id: str):
        self.context_id = context_id
        super().__init__(f"AMIP Execution Context '{context_id}' already exists.")


class ContextCorrupted(AmipBaseException):
    """Raised when a context object or blackboard state fails integrity validation."""
    def __init__(self, context_id: str, reason: str):
        self.context_id = context_id
        self.reason = reason
        super().__init__(f"AMIP Execution Context '{context_id}' is corrupted: {reason}")


class DecisionConflict(AmipBaseException):
    """Raised when agent votes conflict below confidence resolution threshold."""
    def __init__(self, decision_id: str, details: str):
        self.decision_id = decision_id
        self.details = details
        super().__init__(f"AMIP Decision '{decision_id}' failed due to unresolvable conflict: {details}")


class DecisionFailed(AmipBaseException):
    """Raised when decision evaluation algorithm encounters a fatal processing error."""
    def __init__(self, decision_id: str, reason: str):
        self.decision_id = decision_id
        self.reason = reason
        super().__init__(f"AMIP Decision '{decision_id}' evaluation failed: {reason}")


class DecisionTimeout(AmipBaseException):
    """Raised when decision evaluation exceeds deadline threshold."""
    def __init__(self, decision_id: str, timeout_ms: float):
        self.decision_id = decision_id
        self.timeout_ms = timeout_ms
        super().__init__(f"AMIP Decision '{decision_id}' timed out after {timeout_ms:.2f}ms.")


class InvalidExecutionPlan(AmipBaseException):
    """Raised when an execution plan fails structural or policy validation."""
    def __init__(self, plan_id: str, errors: list[str]):
        self.plan_id = plan_id
        self.errors = errors
        error_msg = "; ".join(errors) if errors else "Unknown validation error"
        super().__init__(f"AMIP ExecutionPlan '{plan_id}' is invalid: {error_msg}")


class DependencyCycleDetected(AmipBaseException):
    """Raised when task dependency graph contains cyclic dependencies."""
    def __init__(self, plan_id_or_tasks: str, cycle_path: list[str] | None = None):
        self.plan_id_or_tasks = plan_id_or_tasks
        self.cycle_path = cycle_path or []
        path_str = " -> ".join(self.cycle_path) if self.cycle_path else "unspecified cycle"
        super().__init__(f"Cyclic task dependency detected in '{plan_id_or_tasks}': {path_str}")


class TaskDependencyMissing(AmipBaseException):
    """Raised when a task depends on a non-existent task ID."""
    def __init__(self, task_id: str, missing_dependency_id: str):
        self.task_id = task_id
        self.missing_dependency_id = missing_dependency_id
        super().__init__(f"Task '{task_id}' depends on missing task '{missing_dependency_id}'.")


class TaskExecutionFailed(AmipBaseException):
    """Raised when an individual task execution fails during supervisor dispatch."""
    def __init__(self, task_id: str, agent_name: str, error_message: str):
        self.task_id = task_id
        self.agent_name = agent_name
        self.error_message = error_message
        super().__init__(f"Task '{task_id}' failed in agent '{agent_name}': {error_message}")


class UnsupportedTask(AmipBaseException):
    """Raised when no registered executor supports the given task type or agent."""
    def __init__(self, task_id: str, task_type: str):
        self.task_id = task_id
        self.task_type = task_type
        super().__init__(f"No registered executor supports task '{task_id}' of type '{task_type}'.")


class ExecutionCancelled(AmipBaseException):
    """Raised when supervisor execution is manually cancelled."""
    def __init__(self, workflow_id: str, reason: str = "Execution cancelled by request"):
        self.workflow_id = workflow_id
        self.reason = reason
        super().__init__(f"Workflow execution '{workflow_id}' was cancelled: {reason}")


class WorkflowTimeout(AmipBaseException):
    """Raised when total supervisor workflow execution time exceeds allowed limit."""
    def __init__(self, workflow_id: str, timeout_ms: float):
        self.workflow_id = workflow_id
        self.timeout_ms = timeout_ms
        super().__init__(f"Workflow execution '{workflow_id}' timed out after {timeout_ms:.2f}ms.")
