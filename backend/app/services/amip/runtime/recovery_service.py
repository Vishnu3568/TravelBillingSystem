"""
AMIP Startup Reconciliation & Fault-Tolerant Recovery Service.
Scans for zombie/stale workflows after server restarts or network disruptions and reconciles execution state.
"""
from __future__ import annotations
import threading
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.services.amip.utils.time_utils import current_utc_timestamp

logger = logging.getLogger("amip.recovery_service")


class RecoveryService:
    """
    Detects and reconciles stale or orphaned workflow executions on application startup.
    Protects database state from accumulating zombie 'RUNNING' records after crashes.
    """

    def __init__(self, lease_timeout_seconds: int = 120):
        self.lease_timeout_seconds = lease_timeout_seconds
        self._lock = threading.RLock()

    @staticmethod
    def _parse_iso_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
        """Parses an ISO format timestamp to UTC datetime."""
        if not ts_str:
            return None
        try:
            # Handle ISO string with or without Z / +00:00
            clean_ts = ts_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            if dt.tzinfo is None:
                # If naive, assume stored UTC timestamp
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception:
            return None

    def reconcile_stale_workflows(
        self,
        repository: Any,
        monitoring_service: Any,
    ) -> List[str]:
        """
        Scans persistent repository and memory snapshots for orphaned 'RUNNING' or 'CANCELLING'
        workflows whose heartbeat lease has expired, transitioning them to 'STALE_TERMINATED'.
        """
        reconciled_ids: List[str] = []
        now_dt = datetime.now(timezone.utc)

        with self._lock:
            # 1. Check persistent database executions
            try:
                running_records = repository.get_workflow_executions(limit=100, status="RUNNING")
                cancelling_records = repository.get_workflow_executions(limit=50, status="CANCELLING")
                candidates = running_records + cancelling_records

                for record in candidates:
                    w_id = record.get("workflow_id")
                    if not w_id:
                        continue

                    # Determine last heartbeat or start time
                    ts_str = (
                        record.get("metadata", {}).get("heartbeat_at")
                        or record.get("started_at")
                        or record.get("created_at")
                    )
                    ts_dt = self._parse_iso_timestamp(ts_str)

                    is_stale = False
                    if ts_dt:
                        elapsed_seconds = (now_dt - ts_dt).total_seconds()
                        if elapsed_seconds > self.lease_timeout_seconds:
                            is_stale = True
                    else:
                        # Missing timestamp on a RUNNING workflow -> treat as stale on restart
                        is_stale = True

                    if is_stale:
                        self._mark_stale(
                            workflow_id=w_id,
                            previous_status=record.get("status", "RUNNING"),
                            trace_id=record.get("trace_id", ""),
                            repository=repository,
                            monitoring_service=monitoring_service,
                            reason=f"Startup recovery sweep: heartbeat lease expired (>{self.lease_timeout_seconds}s)",
                        )
                        reconciled_ids.append(w_id)

            except Exception as exc:
                logger.warning(f"Error during persistent startup recovery sweep: {exc}")

            # 2. Check in-memory snapshots
            try:
                for snp in monitoring_service.get_execution_snapshots():
                    w_id = snp.get("workflow_id")
                    if w_id and snp.get("status") in ("RUNNING", "CANCELLING") and w_id not in reconciled_ids:
                        snp_ts = self._parse_iso_timestamp(snp.get("timestamp"))
                        if snp_ts and (now_dt - snp_ts).total_seconds() > self.lease_timeout_seconds:
                            self._mark_stale(
                                workflow_id=w_id,
                                previous_status=snp.get("status", "RUNNING"),
                                trace_id=snp.get("trace_id", ""),
                                repository=repository,
                                monitoring_service=monitoring_service,
                                reason=f"In-memory recovery sweep: heartbeat expired",
                            )
                            reconciled_ids.append(w_id)
            except Exception as exc:
                logger.warning(f"Error during memory recovery sweep: {exc}")

        return reconciled_ids

    def _mark_stale(
        self,
        workflow_id: str,
        previous_status: str,
        trace_id: str,
        repository: Any,
        monitoring_service: Any,
        reason: str,
    ) -> None:
        """Transitions a stale workflow to STALE_TERMINATED and writes audit logs."""
        new_status = "STALE_TERMINATED"
        now_ts = current_utc_timestamp()

        # Update in-memory if present
        with monitoring_service._lock:
            mem_snp = monitoring_service._snapshots.get(workflow_id)
            if mem_snp:
                mem_snp.agent_states["RecoveryService"] = new_status
                mem_snp.current_task = "stale_terminated"

        # Record auditable log
        monitoring_service.record_log(
            level="WARNING",
            message=f"Workflow '{workflow_id}' marked as {new_status}: {reason}",
            trace_id=trace_id,
            workflow_id=workflow_id,
            task_id="startup_recovery",
            agent_name="RecoveryService",
            status=new_status,
            metadata={"previous_status": previous_status, "reason": reason, "reconciled_at": now_ts},
        )

        # Update persistent repository
        try:
            repository.save_workflow_execution({
                "workflow_id": workflow_id,
                "trace_id": trace_id,
                "status": new_status,
                "current_task": "stale_terminated",
                "metadata": {"reconciled_at": now_ts, "reason": reason},
            })
        except Exception:
            pass


# Global Singleton
_recovery_instance: Optional[RecoveryService] = None
_recovery_lock = threading.RLock()


def get_recovery_service() -> RecoveryService:
    """Returns the shared RecoveryService singleton."""
    global _recovery_instance
    with _recovery_lock:
        if _recovery_instance is None:
            _recovery_instance = RecoveryService()
        return _recovery_instance
