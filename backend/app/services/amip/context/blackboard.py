"""
AMIP Execution Blackboard.
Thread-safe shared memory storage for context variables, state, and cross-agent artifacts.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, List, Optional
from app.services.amip.interfaces.context_interfaces import IBlackboard


class ExecutionBlackboard(IBlackboard):
    """
    Thread-safe key-value blackboard for storing execution state and intermediate artifacts.
    Guarantees thread safety via reentrant lock (RLock).
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        self._store: Dict[str, Any] = dict(initial_data) if initial_data else {}
        self._lock: threading.RLock = threading.RLock()

    def put(self, key: str, value: Any) -> None:
        """Puts a key-value pair into the blackboard storage (thread-safe)."""
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Blackboard key must be a non-empty string.")
        with self._lock:
            self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a value by key from the blackboard (thread-safe)."""
        with self._lock:
            return self._store.get(key, default)

    def exists(self, key: str) -> bool:
        """Checks if a key exists in the blackboard (thread-safe)."""
        with self._lock:
            return key in self._store

    def remove(self, key: str) -> bool:
        """Removes a key from the blackboard (thread-safe). Returns True if key existed."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> None:
        """Clears all stored entries from the blackboard (thread-safe)."""
        with self._lock:
            self._store.clear()

    def keys(self) -> List[str]:
        """Returns a list of all current keys in the blackboard (thread-safe)."""
        with self._lock:
            return list(self._store.keys())

    def snapshot(self) -> Dict[str, Any]:
        """Creates a shallow copy dictionary snapshot of the current blackboard state (thread-safe)."""
        with self._lock:
            return dict(self._store)

    def __repr__(self) -> str:
        with self._lock:
            return f"ExecutionBlackboard(keys={list(self._store.keys())})"
