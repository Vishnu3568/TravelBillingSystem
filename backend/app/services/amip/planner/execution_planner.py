"""
AMIP Execution Planner.
Pure planning engine responsible for plan creation, validation, graph construction, and duration estimation.
Zero AI, zero routing, zero execution, zero supervision.
"""
from __future__ import annotations
from typing import List, Optional
from app.services.amip.models.enums import PlanningStrategy, Priority, ExecutionMode
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.models.planning_policy import PlanningPolicy
from app.services.amip.models.execution_plan import ExecutionPlan
from app.services.amip.planner.dependency_graph import TaskDependencyGraph
from app.services.amip.planner.planner_utils import validate_plan, estimate_plan_duration
from app.services.amip.exceptions import InvalidExecutionPlan
from app.services.amip.interfaces.planner_interfaces import IExecutionPlanner


class ExecutionPlanner(IExecutionPlanner):
    """
    Pure execution planner managing creation, validation, graph building, and estimation.
    """

    def create_plan(
        self,
        request_summary: str = "Execution Plan",
        tasks: Optional[List[ExecutionTask]] = None,
        strategy: PlanningStrategy = PlanningStrategy.SEQUENTIAL,
        policy: Optional[PlanningPolicy] = None,
        execution_mode: ExecutionMode = ExecutionMode.SYNCHRONOUS,
        priority: Priority = Priority.NORMAL,
        workflow_id: Optional[str] = None,
    ) -> ExecutionPlan:
        """
        Creates a new ExecutionPlan, calculates estimated duration, and returns it.
        """
        task_list = list(tasks) if tasks else []
        policy_obj = policy or PlanningPolicy()

        plan = ExecutionPlan(
            request_summary=request_summary,
            execution_mode=execution_mode,
            planning_strategy=strategy,
            policy=policy_obj,
            tasks=task_list,
            overall_priority=priority,
        )
        if workflow_id:
            plan.workflow_id = workflow_id

        plan.recalculate_estimated_duration()
        return plan

    def validate_plan(self, plan: ExecutionPlan) -> bool:
        """
        Validates an ExecutionPlan. Returns True if valid, raises InvalidExecutionPlan if invalid.
        """
        errors = validate_plan(plan)
        if errors:
            raise InvalidExecutionPlan(plan.plan_id if plan else "null", errors)
        return True

    def estimate_duration(self, plan: ExecutionPlan) -> float:
        """Estimates total execution duration in milliseconds for a plan."""
        if not plan:
            return 0.0
        return estimate_plan_duration(plan.tasks, plan.planning_strategy)

    def build_dependency_graph(self, plan: ExecutionPlan) -> TaskDependencyGraph:
        """
        Constructs and returns a TaskDependencyGraph for the given plan.
        Raises InvalidExecutionPlan if plan is null or missing tasks.
        """
        if not plan:
            raise InvalidExecutionPlan("null", ["ExecutionPlan cannot be null."])
        return TaskDependencyGraph(plan.tasks)
