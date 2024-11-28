from collections import defaultdict, deque
from typing import Callable, Dict, List, Set
import API.STU_Common as STU

class Task:
    def __init__(self, task_id: str, command : STU.Command):
        """
        Initialize a task.

        param task_id: A unique identifier for the task.

        param command: A STU command that will be sent on starting this task. The command completing/failing will end this task.
        """
        # Metadata
        self.task_id = task_id
        self.completed = False
        self.failed = False
        # Contents
        self.command = command
        self.started = False

    def __repr__(self):
        status = 'Completed' if self.completed else ('Failed' if self.failed else 'Pending')
        return f"<Task {self.task_id} - {status}>"


class TaskGraph:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.pending_tasks: Set[str] = set()
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()

    def add_task(self, task: Task, depends_on: List[str] = None):
        """
        Add a task to the task graph.

        param task: The Task object to be added.

        param depends_on: List of task_ids that this task depends on.
        """
        task_id = task.task_id
        self.tasks[task_id] = task
        if depends_on:
            self.dependencies[task_id].update(depends_on)
            for dep in depends_on:
                self.reverse_dependencies[dep].add(task_id)
        else:
            # If no dependencies, mark the task as pending
            self.pending_tasks.add(task_id)

    def get_task(self, task_id: str) -> Task:
        """
        Get a task by its id.

        param task_id: The id of the task.

        return: The Task object.
        """
        return self.tasks[task_id]

    def mark_started(self, task_id: str):
        """
        Mark a task as started.

        param task_id: The id of the started task.
        """
        self.tasks[task_id].started = True

    def mark_completed(self, task_id: str):
        """
        Mark a task as completed and update the dependencies.

        param task_id: The id of the completed task.
        """
        self.completed_tasks.add(task_id)
        self.pending_tasks.discard(task_id)

        # Check for reverse dependencies to see if other tasks are unblocked
        for dependent in self.reverse_dependencies[task_id]:
            self.dependencies[dependent].remove(task_id)
            if not self.dependencies[dependent]:
                self.pending_tasks.add(dependent)

    def mark_failed(self, task_id: str):
        """
        Mark a task as failed and handle propagation if necessary.

        param task_id: The id of the failed task.
        """
        self.failed_tasks.add(task_id)
        self.pending_tasks.discard(task_id)
        # For now, do not propagate failure, but this could be added as a feature later.

    def clear_all(self):
        """
        Clear all tasks and dependencies.

        May result in unexpected behavior if commands are still active.
        """
        self.tasks.clear()
        self.dependencies.clear()
        self.reverse_dependencies.clear()
        self.pending_tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()

    def get_status(self):
        """
        Get the status of all tasks.
        """
        status_report = {
            'Pending': [task_id for task_id in self.pending_tasks],
            'Completed': [task_id for task_id in self.completed_tasks],
            'Failed': [task_id for task_id in self.failed_tasks],
        }
        return status_report

    def __repr__(self):
        return f"<TaskGraph | Pending: {len(self.pending_tasks)}, Completed: {len(self.completed_tasks)}, Failed: {len(self.failed_tasks)}>"