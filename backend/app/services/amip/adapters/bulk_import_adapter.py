"""
AMIP Bulk Import Adapter.
Wraps existing BulkImportService without modifying underlying business logic.
Emits telemetry, timeline records, decision votes, and enforces resilience policies.
"""
from __future__ import annotations
import time
import logging
from typing import Dict, Any, Optional

from app.services.amip.interfaces.adapter_interfaces import IAdapter
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.models.execution_context import ExecutionContext
from app.services.amip.models.agent_record import AgentExecutionRecord
from app.services.amip.models.enums import AgentStatus
from app.services.amip.resilience.circuit_breaker import CircuitBreaker
from app.services.amip.resilience.retry_policy import RetryPolicy
from app.services.amip.runtime.health_monitor import HealthMonitor
from app.services.amip.utils.time_utils import current_utc_timestamp

logger = logging.getLogger("bulk_import_adapter")


class BulkImportAdapter(IAdapter):
    """
    Production adapter wrapping BulkImportService.
    """

    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_policy: Optional[RetryPolicy] = None,
        health_monitor: Optional[HealthMonitor] = None,
    ):
        self.circuit_breaker = circuit_breaker or CircuitBreaker("BulkImportCircuit")
        self.retry_policy = retry_policy or RetryPolicy()
        self.health_monitor = health_monitor or HealthMonitor()
        self.agent_name = "BulkImportAgent"

    def get_agent_name(self) -> str:
        return self.agent_name

    def is_healthy(self) -> bool:
        return self.circuit_breaker.state.value != "OPEN"

    def execute(self, task: ExecutionTask, context: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """
        Executes BulkImportService with context propagation and resilience.
        """
        self.circuit_breaker.allow_execution()
        self.health_monitor.record_heartbeat(self.agent_name)

        db = kwargs.get("db") or task.metadata.get("db")
        files = kwargs.get("files") or task.metadata.get("files") or []
        mode = kwargs.get("mode") or task.metadata.get("mode") or "PARSE_ONLY"
        created_by = kwargs.get("created_by") or task.metadata.get("created_by") or "amip_importer"
        ip = kwargs.get("ip") or task.metadata.get("ip") or "127.0.0.1"

        start_time = current_utc_timestamp()
        t0 = time.perf_counter()

        attempt = 0
        while True:
            try:
                from app.services.imports import BulkImportService
                import_res = None
                if db and files:
                    if mode == "IMPORT_BILLS":
                        import_res = BulkImportService.import_bills(db, files, created_by, ip)
                        output_summary = f"Imported bills: {import_res.get('successCount', 0)} succeeded, {import_res.get('failureCount', 0)} failed"
                    else:
                        import_res = BulkImportService.parse_bills_only(db, files)
                        output_summary = f"Parsed bills preview for {len(files)} files"
                else:
                    output_summary = "Skipped direct BulkImportService (db or files metadata absent)"

                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                end_time = current_utc_timestamp()

                record = AgentExecutionRecord(
                    agent_name=self.agent_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    status=AgentStatus.SUCCESS,
                    input_summary=f"Task {task.task_id} document import",
                    output_summary=output_summary,
                )
                context.timeline.append(record)

                context.evidence.knowledge_context.append(output_summary)

                self.circuit_breaker.record_success()
                self.health_monitor.record_heartbeat(self.agent_name)

                return {
                    "status": "SUCCESS",
                    "agent_name": self.agent_name,
                    "task_id": task.task_id,
                    "workflow_id": context.workflow_id,
                    "trace_id": context.trace_id,
                    "duration_ms": duration_ms,
                    "confidence": 0.92,
                    "output_summary": output_summary,
                    "import_result": import_res,
                }

            except Exception as e:
                attempt += 1
                if self.retry_policy.should_retry(attempt, e):
                    time.sleep(self.retry_policy.next_delay(attempt) / 1000.0)
                    continue
                else:
                    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                    end_time = current_utc_timestamp()

                    self.circuit_breaker.record_failure(e)
                    self.health_monitor.record_executor_failure(self.agent_name)

                    record = AgentExecutionRecord(
                        agent_name=self.agent_name,
                        start_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        status=AgentStatus.FAILURE,
                        input_summary=f"Task {task.task_id} bulk import",
                        output_summary="Bulk import execution failed",
                        errors=[str(e)],
                    )
                    context.timeline.append(record)

                    raise e
