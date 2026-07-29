"""
Comprehensive Unit Test Suite for AMIP Planning Layer (Phase 9 Checkpoint 3).
Tests ExecutionTask, PlanningPolicy, TaskDependencyGraph, ExecutionPlan, PlannerUtils,
ExecutionPlanner, Serialization, Topological Sorting, Cycle Detection, and Exceptions.
Targeting 95%+ Code Coverage.
"""
from __future__ import annotations
import pytest
from app.services.amip.models.enums import (
    TaskType,
    Priority,
    ExecutionMode,
    PlanningStrategy,
    AgentStatus,
)
from app.services.amip.models.execution_task import ExecutionTask, generate_task_id
from app.services.amip.models.planning_policy import PlanningPolicy
from app.services.amip.models.execution_plan import ExecutionPlan, generate_plan_id
from app.services.amip.planner.dependency_graph import TaskDependencyGraph
from app.services.amip.planner.planner_utils import (
    validate_plan,
    validate_task_dependencies,
    estimate_plan_duration,
)
from app.services.amip.planner.execution_planner import ExecutionPlanner
from app.services.amip.exceptions import (
    InvalidExecutionPlan,
    DependencyCycleDetected,
    TaskDependencyMissing,
)


# ============================================================================
# 1. EXECUTION TASK TESTS
# ============================================================================
def test_execution_task_model():
    """Verify ExecutionTask model creation, defaults, and dictionary serialization."""
    tid = generate_task_id()
    assert tid.startswith("tsk-")

    task = ExecutionTask(
        task_id=tid,
        task_name="Extract Document",
        task_type=TaskType.DOCUMENT_IMPORT,
        priority=Priority.HIGH,
        dependencies=[],
        estimated_duration_ms=250.0,
        required_agents=["DocIntelAgent", "LabelerAgent"],
        status=AgentStatus.IDLE,
        metadata={"file_name": "sample.docx"},
    )

    d = task.to_dict()
    assert d["task_id"] == tid
    assert d["task_name"] == "Extract Document"
    assert d["task_type"] == "DOCUMENT_IMPORT"
    assert d["priority"] == "HIGH"
    assert d["required_agents"] == ["DocIntelAgent", "LabelerAgent"]

    restored = ExecutionTask.from_dict(d)
    assert restored.task_id == tid
    assert restored.task_type == TaskType.DOCUMENT_IMPORT
    assert restored.priority == Priority.HIGH
    assert restored.estimated_duration_ms == 250.0
    assert restored.metadata["file_name"] == "sample.docx"


# ============================================================================
# 2. PLANNING POLICY TESTS
# ============================================================================
def test_planning_policy_model():
    """Verify PlanningPolicy defaults and dictionary serialization."""
    policy = PlanningPolicy(strict_order=True, allow_parallel=False)
    d = policy.to_dict()
    assert d["strict_order"] is True
    assert d["allow_parallel"] is False

    restored = PlanningPolicy.from_dict(d)
    assert restored.strict_order is True
    assert restored.allow_parallel is False


# ============================================================================
# 3. TASK DEPENDENCY GRAPH TESTS
# ============================================================================
def test_dependency_graph_topological_sort_and_independent_tasks():
    """Verify DAG topological sorting and independent node identification."""
    t1 = ExecutionTask(task_id="t1", task_name="Parse OCR", estimated_duration_ms=100.0)
    t2 = ExecutionTask(task_id="t2", task_name="Label Fields", dependencies=["t1"], estimated_duration_ms=150.0)
    t3 = ExecutionTask(task_id="t3", task_name="Validate Formulas", dependencies=["t2"], estimated_duration_ms=80.0)
    t4 = ExecutionTask(task_id="t4", task_name="Sync Graph", dependencies=["t1"], estimated_duration_ms=50.0)

    graph = TaskDependencyGraph([t1, t2, t3, t4])

    # Independent tasks
    indep = graph.independent_tasks()
    assert len(indep) == 1
    assert indep[0].task_id == "t1"

    # Topological sort order
    ordered = graph.topological_sort()
    ordered_ids = [t.task_id for t in ordered]

    # t1 must appear before t2, t3, t4. t2 must appear before t3.
    assert ordered_ids.index("t1") < ordered_ids.index("t2")
    assert ordered_ids.index("t1") < ordered_ids.index("t4")
    assert ordered_ids.index("t2") < ordered_ids.index("t3")
    assert len(ordered) == 4


def test_dependency_graph_cycle_detection():
    """Verify cycle detection algorithm and DependencyCycleDetected exception."""
    t1 = ExecutionTask(task_id="t1", dependencies=["t2"])
    t2 = ExecutionTask(task_id="t2", dependencies=["t1"])

    graph = TaskDependencyGraph([t1, t2])
    assert graph.detect_cycles() is True

    with pytest.raises(DependencyCycleDetected):
        graph.topological_sort()


def test_dependency_graph_missing_dependency():
    """Verify TaskDependencyMissing exception when referencing non-existent task."""
    t1 = ExecutionTask(task_id="t1", dependencies=["missing_t99"])
    graph = TaskDependencyGraph([t1])

    with pytest.raises(TaskDependencyMissing):
        graph.topological_sort()

    with pytest.raises(TaskDependencyMissing):
        graph.add_dependency("t1", "missing_t88")


def test_dependency_graph_remove_dependency():
    """Verify removing dependency relationship."""
    t1 = ExecutionTask(task_id="t1")
    t2 = ExecutionTask(task_id="t2", dependencies=["t1"])
    graph = TaskDependencyGraph([t1, t2])

    assert graph.remove_dependency("t2", "t1") is True
    assert graph.remove_dependency("t2", "t1") is False
    assert len(graph.get_node("t2").dependencies) == 0


# ============================================================================
# 4. EXECUTION PLAN TESTS
# ============================================================================
def test_execution_plan_operations_and_serialization():
    """Verify ExecutionPlan task manipulation, ordering, duration calculation, and serialization."""
    plan_id = generate_plan_id()
    assert plan_id.startswith("pln-")

    t1 = ExecutionTask(task_id="task_ocr", task_name="Parse OCR", estimated_duration_ms=100.0)
    t2 = ExecutionTask(task_id="task_label", task_name="Label Fields", dependencies=["task_ocr"], estimated_duration_ms=200.0)

    plan = ExecutionPlan(
        plan_id=plan_id,
        request_summary="Batch Invoice Ingestion",
        planning_strategy=PlanningStrategy.SEQUENTIAL,
    )
    plan.add_task(t1)
    plan.add_task(t2)

    assert len(plan.tasks) == 2
    assert plan.find_task("task_ocr").task_name == "Parse OCR"
    assert plan.find_task("missing") is None

    # Ordered tasks
    ordered = plan.ordered_tasks()
    assert [t.task_id for t in ordered] == ["task_ocr", "task_label"]
    assert plan.validate_dependencies() is True

    # Sequential duration = 100 + 200 = 300
    assert plan.estimated_total_duration == 300.0

    # Summary
    summ = plan.summary()
    assert summ["plan_id"] == plan_id
    assert summ["total_tasks"] == 2
    assert summ["is_valid"] is True

    # Serialization test
    d = plan.to_dict()
    assert d["request_summary"] == "Batch Invoice Ingestion"

    restored = ExecutionPlan.from_dict(d)
    assert restored.plan_id == plan_id
    assert len(restored.tasks) == 2
    assert restored.estimated_total_duration == 300.0

    # Remove task
    assert plan.remove_task("task_label") is True
    assert plan.remove_task("task_label") is False
    assert len(plan.tasks) == 1


# ============================================================================
# 5. PLANNER UTILITIES TESTS
# ============================================================================
def test_planner_utils_duration_estimation():
    """Verify duration estimation algorithms across SEQUENTIAL, PARALLEL, and HYBRID strategies."""
    # Graph structure:
    # t1 (100ms) -> t2 (200ms) -> t4 (50ms)
    # t1 (100ms) -> t3 (300ms) -> t4 (50ms)
    t1 = ExecutionTask(task_id="t1", estimated_duration_ms=100.0)
    t2 = ExecutionTask(task_id="t2", dependencies=["t1"], estimated_duration_ms=200.0)
    t3 = ExecutionTask(task_id="t3", dependencies=["t1"], estimated_duration_ms=300.0)
    t4 = ExecutionTask(task_id="t4", dependencies=["t2", "t3"], estimated_duration_ms=50.0)

    tasks = [t1, t2, t3, t4]

    # Sequential: 100 + 200 + 300 + 50 = 650ms
    dur_seq = estimate_plan_duration(tasks, PlanningStrategy.SEQUENTIAL)
    assert dur_seq == 650.0

    # Parallel Critical Path: max(t1->t2->t4, t1->t3->t4) = max(350ms, 450ms) = 450ms
    dur_par = estimate_plan_duration(tasks, PlanningStrategy.PARALLEL)
    assert dur_par == 450.0

    # Validation helper test
    is_valid, errors = validate_task_dependencies(tasks)
    assert is_valid is True
    assert len(errors) == 0


# ============================================================================
# 6. EXECUTION PLANNER TESTS
# ============================================================================
def test_execution_planner():
    """Verify ExecutionPlanner plan creation, validation, duration estimation, and exceptions."""
    planner = ExecutionPlanner()

    t1 = ExecutionTask(task_id="t1", estimated_duration_ms=120.0)
    t2 = ExecutionTask(task_id="t2", dependencies=["t1"], estimated_duration_ms=180.0)

    plan = planner.create_plan(
        request_summary="Financial Forecast Workflow",
        tasks=[t1, t2],
        strategy=PlanningStrategy.SEQUENTIAL,
        execution_mode=ExecutionMode.SYNCHRONOUS,
    )

    assert plan.request_summary == "Financial Forecast Workflow"
    assert plan.estimated_total_duration == 300.0

    # Validation
    assert planner.validate_plan(plan) is True

    # Dependency graph construction
    graph = planner.build_dependency_graph(plan)
    assert len(graph.list_nodes()) == 2

    # Null plan exception
    with pytest.raises(InvalidExecutionPlan):
        planner.validate_plan(None)

    with pytest.raises(InvalidExecutionPlan):
        planner.build_dependency_graph(None)
