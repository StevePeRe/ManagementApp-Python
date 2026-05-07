"""
Application: TaskService (use-case orchestration).

The service layer sits between the API router and the repository.
It is a thin facade that:
1. Delegates data access to the repository.
2. Translates "not found" DB responses into domain exceptions
   (which the API layer catches and maps to HTTP 404).
"""

from datetime import datetime

from app.tasks.api.schemas import TaskCreate, TaskUpdate
from app.tasks.domain.exceptions import TaskNotFoundError
from app.tasks.infrastructure.models import TaskModel
from app.tasks.infrastructure.repository import TaskRepository


class TaskService:
    """
    Orchestrates business operations for tasks.

    Note: the service does not inject the repository via an abstract interface
    (no Repository ABC/Protocol). For this project's scope it's fine, but in a
    larger codebase you would define a TaskRepository protocol in the domain
    layer to keep the service fully decoupled from infrastructure details.
    """

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def get_all_tasks(self) -> list[TaskModel]:
        """Return all tasks. No pagination yet."""
        return self.repository.find_all()

    def get_task_by_id(self, task_id: int) -> TaskModel:
        """Return a task, or raise TaskNotFoundError."""
        task = self.repository.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def create_task(self, payload: TaskCreate) -> TaskModel:
        """Persist a new task and return it with auto-generated fields."""
        return self.repository.create(payload)

    def update_task(self, task_id: int, payload: TaskUpdate) -> TaskModel:
        """Update task fields, or raise TaskNotFoundError."""
        task = self.repository.update(task_id, payload)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def delete_task(self, task_id: int) -> None:
        """Delete a task, or raise TaskNotFoundError."""
        deleted = self.repository.delete(task_id)
        if not deleted:
            raise TaskNotFoundError(task_id)

    # --- Methods used by the scheduler ---

    def move_created_to_running(self, created_limit: datetime, now: datetime) -> int:
        """Transition tasks stuck in CREATED to RUNNING."""
        return self.repository.move_to_running(created_limit=created_limit, now=now)

    def move_running_to_done(self, running_limit: datetime) -> int:
        """Transition tasks stuck in RUNNING to DONE."""
        return self.repository.move_to_done(running_limit=running_limit)
