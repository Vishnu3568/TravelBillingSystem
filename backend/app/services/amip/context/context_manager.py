"""
AMIP Context Manager.
Manages the lifecycle of ExecutionContexts and ExecutionBlackboards in memory.
Pure infrastructure layer - Zero business, AI, or routing logic.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, List, Optional
from app.services.amip.interfaces.context_interfaces import IContextManager, IBlackboard
from app.services.amip.models.execution_context import ExecutionContext
from app.services.amip.models.enums import TaskType, Priority, ExecutionMode, ExecutionStatus
from app.services.amip.context.blackboard import ExecutionBlackboard
from app.services.amip.exceptions import ContextNotFound, ContextAlreadyExists, ContextCorrupted
from app.services.amip.utils.generators import generate_request_id, generate_trace_id, generate_workflow_id


class ContextManager(IContextManager):
    """
    Thread-safe manager for creating, storing, retrieving, updating, and destroying AMIP ExecutionContexts and Blackboards.
    """

    def __init__(self):
        self._contexts: Dict[str, ExecutionContext] = {}
        self._blackboards: Dict[str, ExecutionBlackboard] = {}
        self._lock: threading.RLock = threading.RLock()

    def create_context(
        self,
        task_type: TaskType = TaskType.GENERAL_QUERY,
        user_id: str = "system",
        user_role: str = "EMPLOYEE",
        session_id: str = "default_session",
        execution_mode: ExecutionMode = ExecutionMode.SYNCHRONOUS,
        priority: Priority = Priority.NORMAL,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> ExecutionContext:
        """
        Creates a new ExecutionContext and matching ExecutionBlackboard (thread-safe).
        Raises ContextAlreadyExists if request_id is supplied and already registered.
        """
        req_id = request_id or generate_request_id()
        trc_id = trace_id or generate_trace_id()
        wfk_id = workflow_id or generate_workflow_id()

        with self._lock:
            if req_id in self._contexts:
                raise ContextAlreadyExists(req_id)

            context = ExecutionContext(
                request_id=req_id,
                trace_id=trc_id,
                session_id=session_id,
                workflow_id=wfk_id,
                task_type=task_type,
                user_id=user_id,
                user_role=user_role,
                execution_mode=execution_mode,
                priority=priority,
            )
            blackboard = ExecutionBlackboard()

            self._contexts[req_id] = context
            self._blackboards[req_id] = blackboard
            return context

    def get_context(self, request_id: str) -> ExecutionContext:
        """
        Retrieves an ExecutionContext by request_id (thread-safe).
        Raises ContextNotFound if the context does not exist.
        """
        with self._lock:
            if request_id not in self._contexts:
                raise ContextNotFound(request_id)
            return self._contexts[request_id]

    def get_blackboard(self, request_id: str) -> ExecutionBlackboard:
        """
        Retrieves the ExecutionBlackboard for a given request_id (thread-safe).
        Raises ContextNotFound if the blackboard does not exist.
        """
        with self._lock:
            if request_id not in self._blackboards:
                raise ContextNotFound(request_id)
            return self._blackboards[request_id]

    def update_context(self, context: ExecutionContext) -> None:
        """
        Updates an existing context in the manager store (thread-safe).
        Raises ContextNotFound if the context is not present.
        Raises ContextCorrupted if context structure is invalid.
        """
        if not context or not getattr(context, "request_id", None):
            raise ContextCorrupted("unknown", "Invalid or null ExecutionContext instance provided.")

        req_id = context.request_id
        with self._lock:
            if req_id not in self._contexts:
                raise ContextNotFound(req_id)
            self._contexts[req_id] = context

    def save_context(self, context: ExecutionContext) -> None:
        """
        Saves or upserts an ExecutionContext in the manager store (thread-safe).
        """
        if not context or not getattr(context, "request_id", None):
            raise ContextCorrupted("unknown", "Invalid or null ExecutionContext instance provided.")

        req_id = context.request_id
        with self._lock:
            self._contexts[req_id] = context
            if req_id not in self._blackboards:
                self._blackboards[req_id] = ExecutionBlackboard()

    def destroy_context(self, request_id: str) -> bool:
        """
        Destroys and removes an ExecutionContext and its Blackboard from memory (thread-safe).
        Returns True if context existed and was destroyed, False otherwise.
        """
        with self._lock:
            existed = request_id in self._contexts
            self._contexts.pop(request_id, None)
            self._blackboards.pop(request_id, None)
            return existed

    def list_contexts(self) -> List[str]:
        """Returns a list of all active request_ids in memory (thread-safe)."""
        with self._lock:
            return list(self._contexts.keys())

    def clear_all(self) -> None:
        """Clears all contexts and blackboards from memory (thread-safe)."""
        with self._lock:
            self._contexts.clear()
            self._blackboards.clear()
