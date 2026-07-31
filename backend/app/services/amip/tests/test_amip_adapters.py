"""
Comprehensive Unit Test Suite for AMIP Production Adapters & Integration (Phase 9 Checkpoint 7).
Tests ValidationAdapter, LearningAdapter, KnowledgeGraphAdapter, PredictiveAdapter,
CopilotAdapter, BulkImportAdapter, AdapterRegistry, Supervisor Integration, and Context Propagation.
Targeting 95%+ Code Coverage.
"""
from __future__ import annotations
import pytest

from app.services.amip.models.enums import TaskType, DecisionStatus
from app.services.amip.models.execution_context import ExecutionContext
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.adapters.validation_adapter import ValidationAdapter
from app.services.amip.adapters.learning_adapter import LearningAdapter
from app.services.amip.adapters.knowledge_graph_adapter import KnowledgeGraphAdapter
from app.services.amip.adapters.predictive_adapter import PredictiveAdapter
from app.services.amip.adapters.copilot_adapter import CopilotAdapter
from app.services.amip.adapters.bulk_import_adapter import BulkImportAdapter
from app.services.amip.adapters.adapter_registry import AdapterRegistry
from app.services.amip.supervisor.execution_engine import ExecutionEngine
from app.services.amip.supervisor.amip_supervisor import AMIPSupervisor


# ============================================================================
# 1. ADAPTER REGISTRY TESTS
# ============================================================================
def test_adapter_registry_registration_and_resolution():
    """Verify AdapterRegistry registration and resolution by agent name and TaskType."""
    registry = AdapterRegistry(register_defaults=True)

    assert registry.resolve("ValidationAgent") is not None
    assert registry.resolve("LearningAgent") is not None
    assert registry.resolve("KnowledgeGraphAgent") is not None
    assert registry.resolve("PredictiveAgent") is not None
    assert registry.resolve("CopilotAgent") is not None
    assert registry.resolve("BulkImportAgent") is not None

    # Resolve by TaskType string
    assert registry.resolve("DOCUMENT_IMPORT") is not None
    assert registry.resolve("COPILOT_CHAT") is not None

    adapters_map = registry.list_adapters()
    assert len(adapters_map) >= 6


# ============================================================================
# 2. INDIVIDUAL DOMAIN ADAPTER TESTS
# ============================================================================
def test_validation_adapter_execution():
    """Verify ValidationAdapter execution, timeline recording, and vote generation."""
    adapter = ValidationAdapter()
    assert adapter.get_agent_name() == "ValidationAgent"
    assert adapter.is_healthy() is True

    context = ExecutionContext(workflow_id="wfk-val-test")
    task = ExecutionTask(
        task_id="t-val",
        task_name="Validate Document",
        task_type=TaskType.DOCUMENT_IMPORT,
        required_agents=["ValidationAgent"],
    )

    res = adapter.execute(task, context)
    assert res["status"] == "SUCCESS"
    assert res["agent_name"] == "ValidationAgent"
    assert res["confidence"] > 0.0

    # Verify timeline records
    records = context.timeline.records
    assert len(records) == 1
    assert records[0].agent_name == "ValidationAgent"


def test_learning_adapter_execution():
    """Verify LearningAdapter execution and context propagation."""
    adapter = LearningAdapter()
    assert adapter.get_agent_name() == "LearningAgent"

    context = ExecutionContext(workflow_id="wfk-learn-test")
    task = ExecutionTask(
        task_id="t-learn",
        task_name="Record Learning Feedback",
        task_type=TaskType.REVIEW_CORRECTION,
        required_agents=["LearningAgent"],
    )

    res = adapter.execute(task, context)
    assert res["status"] == "SUCCESS"
    assert len(context.timeline.records) == 1


def test_knowledge_graph_adapter_execution():
    """Verify KnowledgeGraphAdapter execution."""
    adapter = KnowledgeGraphAdapter()
    context = ExecutionContext(workflow_id="wfk-graph-test")
    task = ExecutionTask(
        task_id="t-graph",
        task_name="Traverse Knowledge Subgraph",
        task_type=TaskType.GRAPH_QUERY,
        required_agents=["KnowledgeGraphAgent"],
    )

    res = adapter.execute(task, context)
    assert res["status"] == "SUCCESS"
    assert "graph_context" in res
    assert len(context.timeline.records) == 1


def test_predictive_adapter_execution():
    """Verify PredictiveAdapter execution."""
    adapter = PredictiveAdapter()
    context = ExecutionContext(workflow_id="wfk-pred-test")
    task = ExecutionTask(
        task_id="t-pred",
        task_name="Predictive Revenue & Anomaly Scan",
        task_type=TaskType.PREDICTIVE_FORECAST,
        required_agents=["PredictiveAgent"],
    )

    res = adapter.execute(task, context)
    assert res["status"] == "SUCCESS"
    assert len(context.timeline.records) == 1


def test_copilot_adapter_execution():
    """Verify CopilotAdapter execution."""
    adapter = CopilotAdapter()
    context = ExecutionContext(workflow_id="wfk-copilot-test")
    task = ExecutionTask(
        task_id="t-copilot",
        task_name="Process Copilot Query",
        task_type=TaskType.COPILOT_CHAT,
        required_agents=["CopilotAgent"],
        metadata={"query": "Explain bill details"},
    )

    res = adapter.execute(task, context)
    assert res["status"] == "SUCCESS"
    assert len(context.timeline.records) == 1


def test_bulk_import_adapter_execution():
    """Verify BulkImportAdapter execution."""
    adapter = BulkImportAdapter()
    context = ExecutionContext(workflow_id="wfk-import-test")
    task = ExecutionTask(
        task_id="t-import",
        task_name="Import Document Bills",
        task_type=TaskType.DOCUMENT_IMPORT,
        required_agents=["BulkImportAgent"],
    )

    res = adapter.execute(task, context)
    assert res["status"] == "SUCCESS"
    assert len(context.timeline.records) == 1


# ============================================================================
# 3. END-TO-END SUPERVISOR INTEGRATION VIA ADAPTER REGISTRY
# ============================================================================
def test_supervisor_orchestration_with_adapter_registry():
    """
    Verify end-to-end AMIP Supervisor orchestration using production AdapterRegistry.
    Plan: BulkImport -> Validation -> Predictive.
    """
    registry = AdapterRegistry(register_defaults=True)
    engine = ExecutionEngine(adapter_registry=registry)
    supervisor = AMIPSupervisor(engine=engine)

    t1 = ExecutionTask(
        task_id="t1",
        task_name="Parse Import Documents",
        task_type=TaskType.DOCUMENT_IMPORT,
        required_agents=["BulkImportAgent"],
    )
    t2 = ExecutionTask(
        task_id="t2",
        task_name="Validate Form & Formulas",
        task_type=TaskType.DOCUMENT_IMPORT,
        dependencies=["t1"],
        required_agents=["ValidationAgent"],
    )
    t3 = ExecutionTask(
        task_id="t3",
        task_name="Run Predictive Anomaly Check",
        task_type=TaskType.PREDICTIVE_FORECAST,
        dependencies=["t2"],
        required_agents=["PredictiveAgent"],
    )

    plan = supervisor.planner.create_plan(tasks=[t1, t2, t3])

    decision, context = supervisor.orchestrate(plan=plan, task_type=TaskType.DOCUMENT_IMPORT)

    assert decision.status == DecisionStatus.COMPLETED
    assert decision.confidence > 0.80

    # Verify all 3 tasks generated timeline events
    assert len(context.timeline.records) == 3
