"""
Comprehensive Unit Test Suite for AMIP Supervisor Agent (Phase 9 Checkpoint 4).
Tests AMIPSupervisor, SupervisorState, SupervisorMetrics, ExecutionEngine,
MockTaskExecutors, Events, Exceptions, Timeouts, and Cancellation.
Targeting 95%+ Code Coverage.
"""
from __future__ import annotations
import pytest
import time

from app.services.amip.models.enums import (
    ExecutionStatus,
    DecisionStatus,
    DecisionPolicy,
    TaskType,
    Priority,
    ExecutionMode,
    AgentStatus,
)
from app.services.amip.models.execution_context import ExecutionContext
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.models.execution_plan import ExecutionPlan
from app.services.amip.supervisor.events import (
    WorkflowStarted,
    WorkflowCompleted,
    TaskStarted,
    TaskCompleted,
    TaskFailed,
    TaskCancelled,
)
from app.services.amip.supervisor.supervisor_state import SupervisorState, SupervisorMetrics
from app.services.amip.supervisor.mock_executors import (
    DocIntelMockExecutor,
    ValidationMockExecutor,
    LearningMockExecutor,
    GraphMockExecutor,
    PredictiveMockExecutor,
    CopilotMockExecutor,
)
from app.services.amip.supervisor.execution_engine import ExecutionEngine
from app.services.amip.supervisor.amip_supervisor import AMIPSupervisor
from app.services.amip.exceptions import (
    UnsupportedTask,
    TaskExecutionFailed,
    ExecutionCancelled,
    WorkflowTimeout,
)


# ============================================================================
# 1. SUPERVISOR STATE & METRICS TESTS
# ============================================================================
def test_supervisor_state_and_metrics():
    """Verify SupervisorState progress calculation and SupervisorMetrics computation."""
    state = SupervisorState(workflow_id="wfk-101")
    assert state.execution_progress == 0.0

    state.completed_tasks.append("tsk-1")
    state.update_progress(total_tasks=2)
    assert state.execution_progress == 50.0

    state.completed_tasks.append("tsk-2")
    state.update_progress(total_tasks=2)
    assert state.execution_progress == 100.0

    d_state = state.to_dict()
    assert d_state["workflow_id"] == "wfk-101"
    assert d_state["execution_progress"] == 100.0

    # Metrics test
    metrics = SupervisorMetrics(workflow_id="wfk-101")
    metrics.calculate_metrics([100.0, 200.0], total_tasks=2)
    assert metrics.tasks_completed == 2
    assert metrics.success_rate == 100.0
    assert metrics.average_task_duration_ms == 150.0


# ============================================================================
# 2. SUPERVISOR EVENTS TESTS
# ============================================================================
def test_supervisor_events():
    """Verify execution lifecycle events serialization."""
    ev_start = WorkflowStarted(workflow_id="wfk-99", total_tasks=3, request_summary="Parse Bill")
    d_start = ev_start.to_dict()
    assert d_start["event_type"] == "WorkflowStarted"
    assert d_start["total_tasks"] == 3

    ev_task = TaskCompleted(workflow_id="wfk-99", task_id="tsk-1", agent_name="DocIntelAgent", duration_ms=120.0)
    d_task = ev_task.to_dict()
    assert d_task["event_type"] == "TaskCompleted"
    assert d_task["duration_ms"] == 120.0


# ============================================================================
# 3. MOCK EXECUTORS TESTS
# ============================================================================
def test_mock_task_executors():
    """Verify mock task executors return simulated votes and artifacts without invoking external AI."""
    ctx = ExecutionContext()
    bb = ctx.timeline  # Dummy placeholder blackboard

    doc_ex = DocIntelMockExecutor()
    val_ex = ValidationMockExecutor()
    cop_ex = CopilotMockExecutor()

    t_doc = ExecutionTask(task_name="Parse OCR", task_type=TaskType.DOCUMENT_IMPORT, required_agents=["DocIntelAgent"])
    t_val = ExecutionTask(task_name="Validate Formulas", task_type=TaskType.DOCUMENT_IMPORT, required_agents=["ValidationAgent"])
    t_cop = ExecutionTask(task_name="Chat Answer", task_type=TaskType.COPILOT_CHAT, required_agents=["CopilotAgent"])

    assert doc_ex.supports(t_doc) is True
    assert val_ex.supports(t_val) is True
    assert cop_ex.supports(t_cop) is True

    vote_doc, art_doc = doc_ex.execute(t_doc, ctx, bb)
    assert vote_doc.agent_name == "DocIntelAgent"
    assert vote_doc.confidence > 0.9
    assert "ocr_text" in art_doc

    vote_val, art_val = val_ex.execute(t_val, ctx, bb)
    assert vote_val.agent_name == "ValidationAgent"
    assert "validation_report" in art_val


# ============================================================================
# 4. EXECUTION ENGINE TESTS
# ============================================================================
def test_execution_engine_plan_execution():
    """Verify ExecutionEngine sequentially executes plan tasks using registered mock adapters."""
    engine = ExecutionEngine([
        DocIntelMockExecutor(),
        ValidationMockExecutor(),
    ])

    t1 = ExecutionTask(task_id="t1", task_name="Parse OCR", task_type=TaskType.DOCUMENT_IMPORT, required_agents=["DocIntelAgent"])
    t2 = ExecutionTask(task_id="t2", task_name="Validate Formulas", task_type=TaskType.DOCUMENT_IMPORT, dependencies=["t1"], required_agents=["ValidationAgent"])

    plan = ExecutionPlan(workflow_id="wfk-engine-test", tasks=[t1, t2])
    ctx = ExecutionContext(workflow_id="wfk-engine-test")
    bb = ctx.timeline

    # Blackboard placeholder dictionary
    class DummyBB:
        def __init__(self): self.d = {}
        def put(self, k, v): self.d[k] = v
        def get(self, k, default=None): return self.d.get(k, default)

    dummy_bb = DummyBB()

    votes, state, metrics = engine.execute_plan(plan, ctx, dummy_bb)

    assert len(votes) == 2
    assert state.overall_status == ExecutionStatus.COMPLETED
    assert len(state.completed_tasks) == 2
    assert metrics.tasks_completed == 2
    assert len(ctx.timeline.records) == 2


def test_execution_engine_unsupported_task():
    """Verify UnsupportedTask exception when no executor supports the task."""
    engine = ExecutionEngine([])  # No executors registered
    t1 = ExecutionTask(task_id="t1", task_type=TaskType.DOCUMENT_IMPORT)
    plan = ExecutionPlan(tasks=[t1])
    ctx = ExecutionContext()

    class DummyBB:
        def put(self, k, v): pass
        def get(self, k, default=None): return None

    with pytest.raises(UnsupportedTask):
        engine.execute_plan(plan, ctx, DummyBB())


def test_execution_engine_cancellation():
    """Verify cancellation mechanism during plan execution."""
    engine = ExecutionEngine([DocIntelMockExecutor()])
    t1 = ExecutionTask(task_id="t1", task_type=TaskType.DOCUMENT_IMPORT, required_agents=["DocIntelAgent"])
    plan = ExecutionPlan(workflow_id="wfk-cancel", tasks=[t1])
    ctx = ExecutionContext()

    class DummyBB:
        def put(self, k, v): pass
        def get(self, k, default=None): return None

    engine.cancel("wfk-cancel")
    with pytest.raises(ExecutionCancelled):
        engine.execute_plan(plan, ctx, DummyBB())


# ============================================================================
# 5. AMIP SUPERVISOR AGENT TESTS
# ============================================================================
def test_amip_supervisor_orchestration_lifecycle():
    """Verify AMIPSupervisor end-to-end orchestration lifecycle without calling business logic."""
    engine = ExecutionEngine([
        DocIntelMockExecutor(),
        ValidationMockExecutor(),
        LearningMockExecutor(),
    ])
    supervisor = AMIPSupervisor(engine=engine)

    # 1. Create Tasks & Plan
    t1 = ExecutionTask(task_id="t1", task_name="Parse OCR", task_type=TaskType.DOCUMENT_IMPORT, required_agents=["DocIntelAgent"])
    t2 = ExecutionTask(task_id="t2", task_name="Label Fields", task_type=TaskType.DOCUMENT_IMPORT, dependencies=["t1"], required_agents=["LearningAgent"])
    t3 = ExecutionTask(task_id="t3", task_name="Validate Formulas", task_type=TaskType.DOCUMENT_IMPORT, dependencies=["t2"], required_agents=["ValidationAgent"])

    plan = supervisor.planner.create_plan(
        request_summary="Multi-Stage Document Import",
        tasks=[t1, t2, t3],
    )

    # 2. Run Orchestration
    decision, ctx = supervisor.orchestrate(
        plan=plan,
        task_type=TaskType.DOCUMENT_IMPORT,
        user_id="owner_john",
        user_role="OWNER",
    )

    # 3. Assert Decisions & Context Lifecycle
    assert decision.status == DecisionStatus.COMPLETED
    assert decision.policy == DecisionPolicy.AUTO_APPROVE
    assert decision.confidence > 0.85
    assert decision.recommended_action == "AUTO_APPROVE_WORKFLOW"

    assert ctx.overall_status == ExecutionStatus.COMPLETED
    assert ctx.current_stage == "ORCHESTRATION_COMPLETED"
    assert len(ctx.timeline.records) == 3

    # Check metrics & state getters
    assert supervisor.get_state() is not None
    assert supervisor.get_state().overall_status == ExecutionStatus.COMPLETED
    assert supervisor.get_metrics() is not None
    assert supervisor.get_metrics().tasks_completed == 3


def test_amip_supervisor_conflicting_votes_resolution():
    """Verify DecisionMatrix conflict handling when agent votes diverge."""
    class ConflictingExecutor(DocIntelMockExecutor):
        def execute(self, task, context, blackboard):
            from app.services.amip.models.agent_vote import AgentVote
            from app.services.amip.utils.time_utils import current_utc_timestamp
            return AgentVote(agent_name="DocIntelAgent", confidence=0.90, vote="REJECT", reason="Divergent vote"), {}

    engine = ExecutionEngine([
        ConflictingExecutor(),
        ValidationMockExecutor(),
    ])
    supervisor = AMIPSupervisor(engine=engine)

    t1 = ExecutionTask(task_id="t1", task_type=TaskType.DOCUMENT_IMPORT, required_agents=["DocIntelAgent"])
    t2 = ExecutionTask(task_id="t2", task_type=TaskType.DOCUMENT_IMPORT, required_agents=["ValidationAgent"])
    plan = supervisor.planner.create_plan(tasks=[t1, t2])

    decision, ctx = supervisor.orchestrate(plan=plan)

    assert decision.status == DecisionStatus.REVIEW_REQUIRED
    assert decision.policy == DecisionPolicy.AUTO_REVIEW
    assert decision.recommended_action == "FLAG_FOR_REVIEW"
    assert "conflicting votes" in decision.reason
