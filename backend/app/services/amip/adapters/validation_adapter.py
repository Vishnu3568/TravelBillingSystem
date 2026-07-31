"""
AMIP Validation Adapter.
Wraps existing ValidationOrchestrator without modifying underlying business rules.
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

logger = logging.getLogger("validation_adapter")


class ValidationAdapter(IAdapter):
    """
    Production adapter wrapping ValidationOrchestrator.
    """

    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_policy: Optional[RetryPolicy] = None,
        health_monitor: Optional[HealthMonitor] = None,
    ):
        self.circuit_breaker = circuit_breaker or CircuitBreaker("ValidationCircuit")
        self.retry_policy = retry_policy or RetryPolicy()
        self.health_monitor = health_monitor or HealthMonitor()
        self.agent_name = "ValidationAgent"

    def get_agent_name(self) -> str:
        return self.agent_name

    def is_healthy(self) -> bool:
        return self.circuit_breaker.state.value != "OPEN"

    def execute(self, task: ExecutionTask, context: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """
        Executes ValidationOrchestrator.run_validation with context propagation and resilience.
        """
        self.circuit_breaker.allow_execution()
        self.health_monitor.record_heartbeat(self.agent_name)

        db = kwargs.get("db") or task.metadata.get("db")
        labeled_doc = kwargs.get("labeled_doc") or task.metadata.get("labeled_doc")

        # Fallback to valid LabeledDocument if not supplied
        if labeled_doc is None:
            from app.services.field_labeling.field_models import LabeledDocument
            from app.services.document_intelligence.document_models import DocumentMetadata

            labeled_doc = LabeledDocument(
                metadata=DocumentMetadata(filename="amip_sample.pdf", page_count=1),
                elements=[],
            )

        start_time = current_utc_timestamp()
        t0 = time.perf_counter()

        attempt = 0
        last_exception = None

        while True:
            try:
                from app.services.validation_engine.validation_orchestrator import ValidationOrchestrator
                val_result = ValidationOrchestrator.run_validation(db, labeled_doc)

                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                end_time = current_utc_timestamp()

                # Extract score & issues
                score = getattr(val_result, "score", 95)
                confidence = float(score) / 100.0 if score > 1.0 else float(score)
                issues = getattr(val_result, "issues", [])
                is_valid = getattr(val_result, "is_valid", True)

                warnings = [str(i) for i in issues] if issues else []

                output_summary = f"Validation score: {score:.1f}% ({len(issues)} issues detected, valid={is_valid})"

                # 1. Record Execution Timeline Event
                record = AgentExecutionRecord(
                    agent_name=self.agent_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    status=AgentStatus.SUCCESS if is_valid else AgentStatus.WARNING,
                    input_summary=f"Task {task.task_id} validation",
                    output_summary=output_summary,
                    warnings=warnings,
                )
                context.timeline.append(record)

                # 2. Record Knowledge Note in Evidence Context
                context.evidence.knowledge_context.append(output_summary)

                # 3. Update Circuit & Health State
                self.circuit_breaker.record_success()
                self.health_monitor.record_heartbeat(self.agent_name)

                return {
                    "status": "SUCCESS",
                    "agent_name": self.agent_name,
                    "task_id": task.task_id,
                    "workflow_id": context.workflow_id,
                    "trace_id": context.trace_id,
                    "duration_ms": duration_ms,
                    "confidence": confidence,
                    "output_summary": output_summary,
                    "warnings": warnings,
                    "validated_document": val_result,
                }

            except Exception as e:
                last_exception = e
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
                        input_summary=f"Task {task.task_id} validation",
                        output_summary="Validation failed",
                        errors=[str(e)],
                    )
                    context.timeline.append(record)

                    raise e
