"""
AMIP Knowledge Graph Adapter.
Wraps existing GraphOrchestrator without modifying underlying business logic.
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

logger = logging.getLogger("knowledge_graph_adapter")


class KnowledgeGraphAdapter(IAdapter):
    """
    Production adapter wrapping GraphOrchestrator.
    """

    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_policy: Optional[RetryPolicy] = None,
        health_monitor: Optional[HealthMonitor] = None,
    ):
        self.circuit_breaker = circuit_breaker or CircuitBreaker("GraphCircuit")
        self.retry_policy = retry_policy or RetryPolicy()
        self.health_monitor = health_monitor or HealthMonitor()
        self.agent_name = "KnowledgeGraphAgent"

    def get_agent_name(self) -> str:
        return self.agent_name

    def is_healthy(self) -> bool:
        return self.circuit_breaker.state.value != "OPEN"

    def execute(self, task: ExecutionTask, context: ExecutionContext, **kwargs) -> Dict[str, Any]:
        """
        Executes GraphOrchestrator queries with context propagation and resilience.
        """
        self.circuit_breaker.allow_execution()
        self.health_monitor.record_heartbeat(self.agent_name)

        db = kwargs.get("db") or task.metadata.get("db")
        bill_id = kwargs.get("bill_id") or task.metadata.get("bill_id") or 0

        start_time = current_utc_timestamp()
        t0 = time.perf_counter()

        attempt = 0
        while True:
            try:
                from app.services.knowledge_graph.graph_orchestrator import GraphOrchestrator
                graph_text = ""
                if db and bill_id:
                    graph_text = GraphOrchestrator.get_copilot_graph_context(db, bill_id)

                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                end_time = current_utc_timestamp()

                output_summary = f"Retrieved Knowledge Graph context for bill_id={bill_id} ({len(graph_text)} chars)"

                record = AgentExecutionRecord(
                    agent_name=self.agent_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    status=AgentStatus.SUCCESS,
                    input_summary=f"Task {task.task_id} graph traversal",
                    output_summary=output_summary,
                )
                context.timeline.append(record)

                context.evidence.graph_context = {"summary": output_summary, "text": graph_text}

                self.circuit_breaker.record_success()
                self.health_monitor.record_heartbeat(self.agent_name)

                return {
                    "status": "SUCCESS",
                    "agent_name": self.agent_name,
                    "task_id": task.task_id,
                    "workflow_id": context.workflow_id,
                    "trace_id": context.trace_id,
                    "duration_ms": duration_ms,
                    "confidence": 0.88,
                    "output_summary": output_summary,
                    "graph_context": graph_text,
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
                        input_summary=f"Task {task.task_id} graph query",
                        output_summary="Knowledge Graph execution failed",
                        errors=[str(e)],
                    )
                    context.timeline.append(record)

                    raise e
