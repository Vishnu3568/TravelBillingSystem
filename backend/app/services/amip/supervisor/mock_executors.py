"""
AMIP Mock Task Executors.
Simulated task executor adapters for testing Supervisor orchestration without invoking actual domain services.
Pure simulated outputs - DO NOT call existing services or AI models.
"""
from __future__ import annotations
from typing import Dict, Any, Tuple
from app.services.amip.interfaces.supervisor_interfaces import ITaskExecutor
from app.services.amip.models.agent_vote import AgentVote
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.models.enums import AgentStatus, TaskType
from app.services.amip.utils.time_utils import current_utc_timestamp


class BaseMockExecutor(ITaskExecutor):
    """Base class for mock task executors."""
    def __init__(self, agent_name: str, supported_types: list[TaskType]):
        self.agent_name = agent_name
        self.supported_types = supported_types
        self._statuses: Dict[str, AgentStatus] = {}

    def cancel(self, task_id: str) -> bool:
        self._statuses[task_id] = AgentStatus.SKIPPED
        return True

    def status(self, task_id: str) -> AgentStatus:
        return self._statuses.get(task_id, AgentStatus.IDLE)

    def supports(self, task: ExecutionTask) -> bool:
        if not task:
            return False
        if task.required_agents:
            return self.agent_name in task.required_agents
        return task.task_type in self.supported_types


class DocIntelMockExecutor(BaseMockExecutor):
    """Simulates Document Intelligence document structural parsing."""
    def __init__(self):
        super().__init__("DocIntelAgent", [TaskType.DOCUMENT_IMPORT])

    def execute(self, task: ExecutionTask, context: Any, blackboard: Any) -> Tuple[AgentVote, Dict[str, Any]]:
        self._statuses[task.task_id] = AgentStatus.SUCCESS
        vote = AgentVote(
            agent_name=self.agent_name,
            confidence=0.96,
            vote="APPROVE",
            reason="Simulated OCR structural parsing completed for 1 page",
            execution_time=current_utc_timestamp(),
        )
        artifacts = {
            "document_structure": {"pages": 1, "tables": 1, "paragraphs": 12},
            "ocr_text": "Simulated invoice text content for testing",
        }
        return vote, artifacts


class ValidationMockExecutor(BaseMockExecutor):
    """Simulates Validation Engine formula and coordinate checks."""
    def __init__(self):
        super().__init__("ValidationAgent", [TaskType.DOCUMENT_IMPORT, TaskType.REVIEW_CORRECTION])

    def execute(self, task: ExecutionTask, context: Any, blackboard: Any) -> Tuple[AgentVote, Dict[str, Any]]:
        self._statuses[task.task_id] = AgentStatus.SUCCESS
        vote = AgentVote(
            agent_name=self.agent_name,
            confidence=0.92,
            vote="APPROVE",
            reason="Simulated mathematical formula & duplicate checks passed",
            execution_time=current_utc_timestamp(),
        )
        artifacts = {
            "validation_report": {"score": 95, "issues": [], "is_valid": True},
        }
        return vote, artifacts


class LearningMockExecutor(BaseMockExecutor):
    """Simulates Self-Learning pattern retrieval and correction feedback."""
    def __init__(self):
        super().__init__("LearningAgent", [TaskType.DOCUMENT_IMPORT, TaskType.REVIEW_CORRECTION])

    def execute(self, task: ExecutionTask, context: Any, blackboard: Any) -> Tuple[AgentVote, Dict[str, Any]]:
        self._statuses[task.task_id] = AgentStatus.SUCCESS
        vote = AgentVote(
            agent_name=self.agent_name,
            confidence=0.88,
            vote="APPROVE",
            reason="Simulated company layout pattern matched with 88% confidence",
            execution_time=current_utc_timestamp(),
        )
        artifacts = {
            "learned_context": {"company": "Portescap", "layout_confidence": 0.88},
        }
        return vote, artifacts


class GraphMockExecutor(BaseMockExecutor):
    """Simulates Knowledge Graph entity relationship linking."""
    def __init__(self):
        super().__init__("GraphAgent", [TaskType.GRAPH_QUERY, TaskType.DOCUMENT_IMPORT])

    def execute(self, task: ExecutionTask, context: Any, blackboard: Any) -> Tuple[AgentVote, Dict[str, Any]]:
        self._statuses[task.task_id] = AgentStatus.SUCCESS
        vote = AgentVote(
            agent_name=self.agent_name,
            confidence=0.90,
            vote="APPROVE",
            reason="Simulated entity nodes and relationships linked in graph",
            execution_time=current_utc_timestamp(),
        )
        artifacts = {
            "graph_summary": {"nodes_added": 3, "edges_added": 2},
        }
        return vote, artifacts


class PredictiveMockExecutor(BaseMockExecutor):
    """Simulates Predictive Intelligence forecasting and anomaly detection."""
    def __init__(self):
        super().__init__("PredictiveAgent", [TaskType.PREDICTIVE_FORECAST])

    def execute(self, task: ExecutionTask, context: Any, blackboard: Any) -> Tuple[AgentVote, Dict[str, Any]]:
        self._statuses[task.task_id] = AgentStatus.SUCCESS
        vote = AgentVote(
            agent_name=self.agent_name,
            confidence=0.85,
            vote="APPROVE",
            reason="Simulated revenue forecast and risk evaluation complete",
            execution_time=current_utc_timestamp(),
        )
        artifacts = {
            "predictive_summary": {"monthly_forecast": 450000.0, "risk_level": "LOW"},
        }
        return vote, artifacts


class CopilotMockExecutor(BaseMockExecutor):
    """Simulates Conversational Copilot assistant dialogue."""
    def __init__(self):
        super().__init__("CopilotAgent", [TaskType.COPILOT_CHAT, TaskType.GENERAL_QUERY])

    def execute(self, task: ExecutionTask, context: Any, blackboard: Any) -> Tuple[AgentVote, Dict[str, Any]]:
        self._statuses[task.task_id] = AgentStatus.SUCCESS
        vote = AgentVote(
            agent_name=self.agent_name,
            confidence=0.94,
            vote="APPROVE",
            reason="Simulated copilot response formulated",
            execution_time=current_utc_timestamp(),
        )
        artifacts = {
            "answer_markdown": "### Copilot Response\nSimulated answer for testing.",
        }
        return vote, artifacts
