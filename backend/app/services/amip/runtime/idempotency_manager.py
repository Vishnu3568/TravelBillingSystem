"""
AMIP Idempotency & Deduplication Manager.
Guarantees at-most-once execution semantics by enforcing idempotency keys and active execution leases.
"""
from __future__ import annotations
import threading
import time
import hashlib
import json
from typing import Dict, Any, Optional, Tuple


class IdempotencyManager:
    """
    Thread-safe manager for tracking in-flight and completed idempotency keys.
    Maintains a 15-minute sliding TTL cache to prevent duplicate workflow runs.
    """

    def __init__(self, ttl_seconds: int = 900):
        self.ttl_seconds = ttl_seconds
        # Maps idempotency_key -> {"workflow_id": str, "result": Optional[dict], "expires_at": float, "payload_hash": str}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock: threading.RLock = threading.RLock()

    @staticmethod
    def compute_payload_hash(payload: Any) -> str:
        """Computes deterministic SHA256 hash of the input payload."""
        try:
            serialized = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            serialized = str(payload)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def acquire_lease(
        self,
        idempotency_key: str,
        workflow_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Attempts to acquire an execution lease for the given idempotency key.
        Returns:
            (True, None) if lease acquired (first time execution).
            (False, existing_cached_data) if duplicate request detected.
        """
        if not idempotency_key:
            return True, None

        now = time.time()
        payload_hash = self.compute_payload_hash(payload)

        with self._lock:
            # Clean expired entries periodically
            self._purge_expired(now)

            if idempotency_key in self._cache:
                entry = self._cache[idempotency_key]
                if entry["expires_at"] > now:
                    return False, entry

            # New or expired lease: claim it
            self._cache[idempotency_key] = {
                "workflow_id": workflow_id,
                "result": None,
                "expires_at": now + self.ttl_seconds,
                "payload_hash": payload_hash,
                "status": "RUNNING",
            }
            return True, None

    def record_completion(
        self,
        idempotency_key: str,
        workflow_id: str,
        result: Dict[str, Any],
    ) -> None:
        """Records the final execution result for an idempotency key."""
        if not idempotency_key:
            return

        now = time.time()
        with self._lock:
            if idempotency_key in self._cache:
                self._cache[idempotency_key]["result"] = result
                self._cache[idempotency_key]["status"] = result.get("status", "COMPLETED")
                self._cache[idempotency_key]["expires_at"] = now + self.ttl_seconds

    def get_cached_result(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached result if present and not expired."""
        if not idempotency_key:
            return None

        now = time.time()
        with self._lock:
            entry = self._cache.get(idempotency_key)
            if entry and entry["expires_at"] > now and entry.get("result"):
                return entry["result"]
            return None

    def _purge_expired(self, now: float) -> None:
        """Removes expired entries from memory cache (internal)."""
        expired_keys = [k for k, v in self._cache.items() if v["expires_at"] <= now]
        for k in expired_keys:
            del self._cache[k]

    def clear(self) -> None:
        """Clears all cached idempotency keys (useful for test isolation)."""
        with self._lock:
            self._cache.clear()


# Global Singleton
_idempotency_instance: Optional[IdempotencyManager] = None
_idempotency_lock = threading.RLock()


def get_idempotency_manager() -> IdempotencyManager:
    """Returns the shared IdempotencyManager singleton."""
    global _idempotency_instance
    with _idempotency_lock:
        if _idempotency_instance is None:
            _idempotency_instance = IdempotencyManager()
        return _idempotency_instance
