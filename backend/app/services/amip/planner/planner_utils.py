"""
AMIP Planner Utilities.
Provides validation helpers and duration estimation algorithms for plans and tasks.
"""
from __future__ import annotations
from typing import List, Tuple, Dict, Optional
from app.services.amip.models.enums import PlanningStrategy
from app.services.amip.models.execution_task import ExecutionTask


def validate_task_dependencies(tasks: List[ExecutionTask]) -> Tuple[bool, List[str]]:
    """
    Validates task dependency relationships across a list of tasks.
    Returns Tuple[is_valid: bool, errors: List[str]].
    Checks for missing task references and cyclic dependencies.
    """
    errors: List[str] = []
    if not tasks:
        return True, errors

    task_map: Dict[str, ExecutionTask] = {t.task_id: t for t in tasks}

    # 1. Check for missing dependency IDs
    for t in tasks:
        for dep_id in t.dependencies:
            if dep_id not in task_map:
                errors.append(f"Task '{t.task_name}' ({t.task_id}) depends on non-existent task '{dep_id}'")

    # 2. Check for cycles using TaskDependencyGraph
    if not errors:
        from app.services.amip.planner.dependency_graph import TaskDependencyGraph
        try:
            graph = TaskDependencyGraph(tasks)
            if graph.detect_cycles():
                errors.append("Cyclic dependency detected in task graph.")
            else:
                graph.topological_sort()
        except Exception as e:
            errors.append(f"Dependency validation failed: {str(e)}")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_plan(plan) -> List[str]:
    """
    Validates an ExecutionPlan instance.
    Returns a list of error strings (empty list if plan is valid).
    """
    errors: List[str] = []
    if not plan:
        return ["ExecutionPlan cannot be null."]

    if not plan.plan_id or not plan.plan_id.strip():
        errors.append("ExecutionPlan must have a non-empty plan_id.")

    if not plan.tasks:
        errors.append("ExecutionPlan contains zero tasks.")

    _, dep_errors = validate_task_dependencies(plan.tasks)
    errors.extend(dep_errors)

    return errors


def estimate_plan_duration(
    tasks: List[ExecutionTask],
    strategy: PlanningStrategy = PlanningStrategy.SEQUENTIAL
) -> float:
    """
    Estimates total execution duration in milliseconds based on planning strategy.
    - SEQUENTIAL: Sum of all task estimated durations.
    - PARALLEL: Max duration along the critical dependency path.
    - HYBRID: Max duration across independent execution chains.
    """
    if not tasks:
        return 0.0

    if strategy == PlanningStrategy.SEQUENTIAL:
        return sum(t.estimated_duration_ms for t in tasks)

    # For PARALLEL / HYBRID, compute critical path duration using DAG traversal
    task_map: Dict[str, ExecutionTask] = {t.task_id: t for t in tasks}
    memo: Dict[str, float] = {}

    def get_critical_path_duration(task_id: str) -> float:
        if task_id in memo:
            return memo[task_id]

        task = task_map.get(task_id)
        if not task:
            return 0.0

        max_dep_duration = 0.0
        for dep_id in task.dependencies:
            if dep_id in task_map:
                dep_dur = get_critical_path_duration(dep_id)
                if dep_dur > max_dep_duration:
                    max_dep_duration = dep_dur

        total_dur = task.estimated_duration_ms + max_dep_duration
        memo[task_id] = total_dur
        return total_dur

    max_overall_duration = 0.0
    for t in tasks:
        dur = get_critical_path_duration(t.task_id)
        if dur > max_overall_duration:
            max_overall_duration = dur

    return max_overall_duration
