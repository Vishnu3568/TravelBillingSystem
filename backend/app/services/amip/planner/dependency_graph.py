"""
AMIP Task Dependency Graph.
Directed Acyclic Graph (DAG) for task dependency tracking, topological sorting, and cycle detection.
"""
from __future__ import annotations
import threading
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque
from app.services.amip.models.execution_task import ExecutionTask
from app.services.amip.exceptions import DependencyCycleDetected, TaskDependencyMissing


class TaskDependencyGraph:
    """
    DAG data structure managing tasks and dependency constraints.
    Thread-safe implementation backed by RLock.
    """

    def __init__(self, tasks: Optional[List[ExecutionTask]] = None):
        self._nodes: Dict[str, ExecutionTask] = {}
        self._lock: threading.RLock = threading.RLock()

        if tasks:
            for t in tasks:
                self.add_node(t)

    def add_node(self, task: ExecutionTask) -> None:
        """Adds a task node to the graph (thread-safe)."""
        if not task or not task.task_id:
            raise ValueError("Task must have a valid task_id.")
        with self._lock:
            self._nodes[task.task_id] = task

    def add_dependency(self, task_id: str, depends_on_task_id: str) -> None:
        """Adds a dependency relationship: task_id depends on depends_on_task_id."""
        with self._lock:
            if task_id not in self._nodes:
                raise TaskDependencyMissing(task_id, task_id)
            if depends_on_task_id not in self._nodes:
                raise TaskDependencyMissing(task_id, depends_on_task_id)

            task = self._nodes[task_id]
            if depends_on_task_id not in task.dependencies:
                task.dependencies.append(depends_on_task_id)

    def remove_dependency(self, task_id: str, depends_on_task_id: str) -> bool:
        """Removes a dependency relationship. Returns True if existed."""
        with self._lock:
            if task_id in self._nodes:
                task = self._nodes[task_id]
                if depends_on_task_id in task.dependencies:
                    task.dependencies.remove(depends_on_task_id)
                    return True
            return False

    def detect_cycles(self) -> bool:
        """
        Detects if there is any cycle in the dependency graph using DFS coloring algorithm.
        WHITE (0): Unvisited, GRAY (1): Visiting (on current stack), BLACK (2): Visited.
        Returns True if a cycle exists, False otherwise.
        """
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

    def independent_tasks(self) -> List[ExecutionTask]:
        """Returns a list of tasks that have zero dependencies in the graph (thread-safe)."""
        with self._lock:
            return [task for task in self._nodes.values() if not task.dependencies]

    def topological_sort(self) -> List[ExecutionTask]:
        """
        Performs topological sorting (Kahn's Algorithm) to determine valid task execution sequence.
        Raises TaskDependencyMissing if any dependency ID is not in the graph.
        Raises DependencyCycleDetected if a cyclic dependency is detected.
        """
        with self._lock:
            # 1. Validate dependencies exist
            for task_id, task in self._nodes.items():
                for dep_id in task.dependencies:
                    if dep_id not in self._nodes:
                        raise TaskDependencyMissing(task_id, dep_id)

            # 2. Build in-degree mapping and adjacency graph
            # Note: dependency 'dep_id -> task_id' means dep_id must run BEFORE task_id.
            in_degree: Dict[str, int] = {node_id: 0 for node_id in self._nodes}
            adj: Dict[str, List[str]] = defaultdict(list)

            for task_id, task in self._nodes.items():
                in_degree[task_id] = len(task.dependencies)
                for dep_id in task.dependencies:
                    adj[dep_id].append(task_id)

            # 3. Process zero in-degree queue
            queue = deque([node_id for node_id, deg in in_degree.items() if deg == 0])
            sorted_tasks: List[ExecutionTask] = []

            while queue:
                current_id = queue.popleft()
                sorted_tasks.append(self._nodes[current_id])

                for neighbor_id in adj[current_id]:
                    in_degree[neighbor_id] -= 1
                    if in_degree[neighbor_id] == 0:
                        queue.append(neighbor_id)

            # 4. Check cycle condition
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
