"""
AMIP Asynchronous Workflow Worker.
Provides a dedicated thread pool for dispatching and executing asynchronous multi-agent workflows.
"""
from __future__ import annotations
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Optional

logger = logging.getLogger("amip.async_worker")


class AsyncWorkflowWorker:
    """
    Thread pool worker managing non-blocking execution of background workflows.
    Ensures background exceptions are caught, logged, and isolated from HTTP request lifecycles.
    """

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="amip-async-worker",
        )
        self._lock = threading.RLock()
        self._is_shutdown = False

    def submit_workflow(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Future:
        """Submits a workflow execution function to the background thread pool."""
        with self._lock:
            if self._is_shutdown:
                raise RuntimeError("AsyncWorkflowWorker has been shut down.")
            return self._executor.submit(self._safe_wrapper, fn, *args, **kwargs)

    def _safe_wrapper(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Executes the function and catches unhandled exceptions."""
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            logger.error(f"Unhandled exception in background AMIP workflow: {exc}", exc_info=True)
            return None

    def shutdown(self, wait: bool = False) -> None:
        """Shuts down the thread pool."""
        with self._lock:
            self._is_shutdown = True
            self._executor.shutdown(wait=wait)


# Global Singleton
_worker_instance: Optional[AsyncWorkflowWorker] = None
_worker_lock = threading.RLock()


def get_async_worker() -> AsyncWorkflowWorker:
    """Returns the shared AsyncWorkflowWorker singleton."""
    global _worker_instance
    with _worker_lock:
        if _worker_instance is None:
            _worker_instance = AsyncWorkflowWorker()
        return _worker_instance
