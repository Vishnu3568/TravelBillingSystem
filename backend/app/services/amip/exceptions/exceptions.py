"""
AMIP platform exceptions for context, decision, planner, supervisor, explainability, and resilience errors.
"""
from __future__ import annotations


class AmipBaseException(Exception):
    """Base exception for all AMIP platform errors."""
    pass


class ContextNotFound(AmipBaseException):
    def __init__(self, context_id: str):
        self.context_id = context_id
        self.workflow_id = context_id
        super().__init__(f"AMIP Execution Context '{context_id}' was not found.")


class ContextAlreadyExists(AmipBaseException):
    def __init__(self, context_id: str):
        self.context_id = context_id
        super().__init__(f"AMIP Execution Context '{context_id}' already exists.")


class ContextCorrupted(AmipBaseException):
    def __init__(self, context_id: str, reason: str):
        self.context_id = context_id
        self.reason = reason
        super().__init__(f"AMIP Execution Context '{context_id}' is corrupted: {reason}")


class ContextStateError(AmipBaseException):
    def __init__(self, context_id: str, current_state: str, expected_state: str):
        self.context_id = context_id
        self.current_state = current_state
        self.expected_state = expected_state
        super().__init__(f"Context '{context_id}' is in state '{current_state}', expected '{expected_state}'.")


class BlackboardKeyNotFound(AmipBaseException):
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Blackboard key '{key}' was not found.")


class DecisionConflict(AmipBaseException):
    def __init__(self, decision_id: str, details: str):
        self.decision_id = decision_id
        self.workflow_id = decision_id
        self.details = details
        super().__init__(f"AMIP Decision '{decision_id}' failed due to unresolvable conflict: {details}")


class DecisionFailed(AmipBaseException):
    def __init__(self, decision_id: str, reason: str):
        self.decision_id = decision_id
        self.reason = reason
        super().__init__(f"AMIP Decision '{decision_id}' evaluation failed: {reason}")


class DecisionTimeout(AmipBaseException):
    def __init__(self, decision_id: str, timeout_ms: float):
        self.decision_id = decision_id
        self.timeout_ms = timeout_ms
        super().__init__(f"AMIP Decision '{decision_id}' timed out after {timeout_ms:.2f}ms.")


class InvalidExecutionPlan(AmipBaseException):
    def __init__(self, plan_id: str, errors: list[str] | None = None):
        self.plan_id = plan_id
        self.errors = errors or []
        error_msg = "; ".join(self.errors) if self.errors else "Unknown validation error"
        super().__init__(f"AMIP ExecutionPlan '{plan_id}' is invalid: {error_msg}")


class DependencyCycleDetected(AmipBaseException):
    def __init__(self, plan_id_or_tasks: str = "", cycle_path: list[str] | None = None):
        self.plan_id_or_tasks = plan_id_or_tasks
        self.cycle_path = cycle_path or []
        path_str = " -> ".join(self.cycle_path) if self.cycle_path else "unspecified cycle"
        super().__init__(f"Cyclic task dependency detected in '{plan_id_or_tasks}': {path_str}")


class TaskDependencyMissing(AmipBaseException):
    def __init__(self, task_id: str = "", missing_dependency_id: str = ""):
        self.task_id = task_id
        self.missing_dependency_id = missing_dependency_id
        super().__init__(f"Task '{task_id}' depends on missing task '{missing_dependency_id}'.")


class TaskExecutionFailed(AmipBaseException):
    def __init__(self, task_id: str, agent_name: str, error_message: str):
        self.task_id = task_id
        self.agent_name = agent_name
        self.error_message = error_message
        super().__init__(f"Task '{task_id}' failed in agent '{agent_name}': {error_message}")


class UnsupportedTask(AmipBaseException):
    def __init__(self, task_id: str, task_type: str):
        self.task_id = task_id
        self.task_type = task_type
        super().__init__(f"No registered executor supports task '{task_id}' of type '{task_type}'.")


class ExecutionCancelled(AmipBaseException):
    def __init__(self, workflow_id: str, reason: str = "Execution cancelled by request"):
        self.workflow_id = workflow_id
        self.reason = reason
        super().__init__(f"Workflow execution '{workflow_id}' was cancelled: {reason}")


class WorkflowTimeout(AmipBaseException):
    def __init__(self, workflow_id: str, timeout_ms: float):
        self.workflow_id = workflow_id
        self.timeout_ms = timeout_ms
        super().__init__(f"Workflow execution '{workflow_id}' timed out after {timeout_ms:.2f}ms.")


class ExplainabilityError(AmipBaseException):
    def __init__(self, report_id_or_wf: str, reason: str):
        self.report_id_or_wf = report_id_or_wf
        self.reason = reason
        super().__init__(f"Explainability processing failed for '{report_id_or_wf}': {reason}")


class NarrativeGenerationError(ExplainabilityError):
    def __init__(self, workflow_id: str, reason: str):
        super().__init__(workflow_id, f"Narrative generation failed: {reason}")


class TimelineGenerationError(ExplainabilityError):
    def __init__(self, workflow_id: str, reason: str):
        super().__init__(workflow_id, f"Timeline generation failed: {reason}")


class RetryLimitExceeded(AmipBaseException):
    def __init__(self, task_id_or_wf: str, max_retries: int, last_error: str = ""):
        self.task_id_or_wf = task_id_or_wf
        self.max_retries = max_retries
        self.last_error = last_error
        super().__init__(f"Retry limit ({max_retries}) exceeded for '{task_id_or_wf}': {last_error}")


class CircuitBreakerOpen(AmipBaseException):
    def __init__(self, circuit_name: str, state: str = "OPEN"):
        self.circuit_name = circuit_name
        self.state = state
        super().__init__(f"Circuit Breaker '{circuit_name}' is currently {state}. Execution rejected.")


class WorkflowCancelled(AmipBaseException):
    def __init__(self, workflow_id: str = "", reason: str = "User cancellation"):
        self.workflow_id = workflow_id
        self.cancellation_reason = reason
        self.reason = reason
        super().__init__(f"Workflow '{workflow_id}' was cancelled: {reason}")


class ExecutionTimeout(AmipBaseException):
    def __init__(self, entity_id: str = "", timeout_ms: float = 0.0):
        self.entity_id = entity_id
        self.timeout_ms = timeout_ms
        super().__init__(f"Execution for '{entity_id}' timed out after {timeout_ms:.2f}ms.")


class HealthCheckFailed(AmipBaseException):
    def __init__(self, component_name: str, reason: str):
        self.component_name = component_name
        self.reason = reason
        super().__init__(f"Health check failed for '{component_name}': {reason}")


# Aliases for backward compatibility
CycleDetected = DependencyCycleDetected
InvalidTaskDependency = TaskDependencyMissing
PlanningFailed = InvalidExecutionPlan
TimeoutException = ExecutionTimeout
OperationCancelled = WorkflowCancelled
