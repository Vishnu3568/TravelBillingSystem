"""
AMIP Copilot Adapter.
Wraps existing CopilotOrchestrator without modifying underlying business logic.
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

logger = logging.getLogger("copilot_adapter")


class CopilotAdapter(IAdapter):
    """
    Production adapter wrapping CopilotOrchestrator.
    """

    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_policy: Optional[RetryPolicy] = None,
        health_monitor: Optional[HealthMonitor] = None,
    ):
        self.circuit_breaker = circuit_breaker or CircuitBreaker("CopilotCircuit")
        self.retry_policy = retry_policy or RetryPolicy()
        self.health_monitor = health_monitor or HealthMonitor()
        self.agent_name = "CopilotAgent"

    def get_agent_name(self) -> str:
        return self.agent_name

    def is_healthy(self) -> bool:
        return self.circuit_breaker.state.value != "OPEN"

    def execute(self, task: ExecutionTask, context: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """
        Executes CopilotOrchestrator.process_chat with context propagation and resilience.
        """
        self.circuit_breaker.allow_execution()
        self.health_monitor.record_heartbeat(self.agent_name)

        db = kwargs.get("db") or task.metadata.get("db")
        request = kwargs.get("request") or task.metadata.get("request")
        user_role = kwargs.get("user_role") or task.metadata.get("user_role") or "ADMIN"
        username = kwargs.get("username") or task.metadata.get("username") or "amip_copilot"

        start_time = current_utc_timestamp()
        t0 = time.perf_counter()

        attempt = 0
        while True:
            try:
                from app.services.enterprise_copilot.copilot_orchestrator import CopilotOrchestrator
                from app.services.enterprise_copilot.copilot_models import CopilotChatRequest

                if request is None:
                    query = task.metadata.get("query", "Summarize system status")
                    request = CopilotChatRequest(query=query, sessionId=context.workflow_id)

                copilot_res = None
                if db and request:
                    copilot_res = CopilotOrchestrator.process_chat(db, request, user_role, username)
                    answer_text = getattr(copilot_res, "answer", "Copilot chat executed.")
                    output_summary = f"Copilot chat answered: {answer_text[:100]}..."
                else:
                    output_summary = "Skipped direct CopilotOrchestrator chat (db metadata absent)"

                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                end_time = current_utc_timestamp()

                record = AgentExecutionRecord(
                    agent_name=self.agent_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    status=AgentStatus.SUCCESS,
                    input_summary=f"Task {task.task_id} copilot query",
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
                    "confidence": 0.85,
                    "output_summary": output_summary,
                    "copilot_response": copilot_res,
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
                        input_summary=f"Task {task.task_id} copilot chat",
                        output_summary="Copilot execution failed",
                        errors=[str(e)],
                    )
                    context.timeline.append(record)

                    raise e
