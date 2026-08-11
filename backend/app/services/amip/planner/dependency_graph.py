"""
Task dependency graph implementation using DAG algorithms for topological sorting and cycle detection.
"""
from __future__ import annotations
import threading
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.exceptions import DependencyCycleDetected, TaskDependencyMissing


class TaskDependencyGraph:
    """DAG data structure for scheduling tasks and enforcing dependency order."""

    def __init__(self, tasks: Optional[List[ExecutionTask]] = None):
        self._nodes: Dict[str, ExecutionTask] = {}
        self._lock: threading.RLock = threading.RLock()

        if tasks:
            for t in tasks:
                self.add_node(t)

    def add_node(self, task: ExecutionTask) -> None:
        """Adds a task node to the graph."""
        if not task or not task.task_id:
            raise ValueError("Task must have a valid task_id.")
        with self._lock:
            self._nodes[task.task_id] = task

    def build_graph(self) -> None:
        """Validates dependencies exist in the graph."""
        with self._lock:
            for task_id, task in self._nodes.items():
                for dep_id in task.dependencies:
                    if dep_id not in self._nodes:
                        raise TaskDependencyMissing(task_id, dep_id)

    def add_dependency(self, task_id: str, depends_on_task_id: str) -> None:
        """Adds a dependency relationship."""
        with self._lock:
            if task_id not in self._nodes:
                raise TaskDependencyMissing(task_id, task_id)
            if depends_on_task_id not in self._nodes:
                raise TaskDependencyMissing(task_id, depends_on_task_id)

            task = self._nodes[task_id]
            if depends_on_task_id not in task.dependencies:
                task.dependencies.append(depends_on_task_id)

    def remove_dependency(self, task_id: str, depends_on_task_id: str) -> bool:
        """Removes a dependency relationship."""
        with self._lock:
            if task_id in self._nodes:
                task = self._nodes[task_id]
                if depends_on_task_id in task.dependencies:
                    task.dependencies.remove(depends_on_task_id)
                    return True
            return False

    def detect_cycles(self) -> bool:
        """Detects if any cycle exists in the dependency graph."""
        with self._lock:
            color: Dict[str, int] = {node_id: 0 for node_id in self._nodes}

            def dfs(node_id: str) -> bool:
                color[node_id] = 1
                task = self._nodes[node_id]
                for dep_id in task.dependencies:
                    if dep_id not in self._nodes:
                        continue
                    if color[dep_id] == 1:
                        return True
                    if color[dep_id] == 0 and dfs(dep_id):
                        return True
                color[node_id] = 2
                return False

            for node_id in self._nodes:
                if color[node_id] == 0:
                    if dfs(node_id):
                        return True
            return False

    has_cycle = detect_cycles

    def get_independent_tasks(self) -> List[ExecutionTask]:
        """Returns tasks that have no dependencies."""
        with self._lock:
            return [task for task in self._nodes.values() if not task.dependencies]

    independent_tasks = get_independent_tasks

    def topological_sort(self) -> List[ExecutionTask]:
        """Performs topological sort (Kahn's Algorithm) to return ordered execution sequence."""
        with self._lock:
            for task_id, task in self._nodes.items():
                for dep_id in task.dependencies:
                    if dep_id not in self._nodes:
                        raise TaskDependencyMissing(task_id, dep_id)

            in_degree: Dict[str, int] = {node_id: 0 for node_id in self._nodes}
            adj: Dict[str, List[str]] = defaultdict(list)

            for task_id, task in self._nodes.items():
                in_degree[task_id] = len(task.dependencies)
                for dep_id in task.dependencies:
                    adj[dep_id].append(task_id)

            queue = deque([node_id for node_id, deg in in_degree.items() if deg == 0])
            sorted_tasks: List[ExecutionTask] = []

            while queue:
                current_id = queue.popleft()
                sorted_tasks.append(self._nodes[current_id])

                for neighbor_id in adj[current_id]:
                    in_degree[neighbor_id] -= 1
                    if in_degree[neighbor_id] == 0:
                        queue.append(neighbor_id)

            if len(sorted_tasks) != len(self._nodes):
                unprocessed = [node_id for node_id, deg in in_degree.items() if deg > 0]
                raise DependencyCycleDetected("TaskDependencyGraph", unprocessed)

            return sorted_tasks

    def get_node(self, task_id: str) -> Optional[ExecutionTask]:
        """Retrieves a node by task_id."""
        with self._lock:
            return self._nodes.get(task_id)

    def list_nodes(self) -> List[ExecutionTask]:
        """Returns all nodes in graph."""
        with self._lock:
            return list(self._nodes.values())


DependencyGraph = TaskDependencyGraph
