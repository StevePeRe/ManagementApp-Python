"""
Infrastructure: data access layer (Repository pattern).

The repository abstracts all database operations behind a clean interface
so that the service/application layer never touches SQLAlchemy directly.
This makes the service layer testable with a mock or in-memory DB.
"""

from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.tasks.api.schemas import TaskCreate, TaskUpdate
from app.tasks.domain.task_state import TaskState
from app.tasks.infrastructure.models import TaskModel


class TaskRepository:
    """
    Repository for TaskModel CRUD + batch state transitions.

    Every method receives an open SQLAlchemy Session from the caller
    (the service layer or the dependency injection container).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Standard CRUD ---

    def find_all(self) -> list[TaskModel]:
        """Return all tasks ordered by creation order."""
        return self.db.query(TaskModel).order_by(TaskModel.id.asc()).all()

    def find_by_id(self, task_id: int) -> TaskModel | None:
        """Return a single task by primary key, or None."""
        return self.db.get(TaskModel, task_id)

    def create(self, payload: TaskCreate) -> TaskModel:
        """Insert a new task row and return it with DB-generated fields populated."""
        task = TaskModel(name=payload.name, state=payload.state)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)  # Load auto-generated fields (id, created_at)
        return task

    def update(self, task_id: int, payload: TaskUpdate) -> TaskModel | None:
        """Update name and/or state of an existing task. Returns None if not found."""
        task = self.db.get(TaskModel, task_id)
        if task is None:
            return None

        task.name = payload.name
        task.state = payload.state
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task_id: int) -> bool:
        """Delete a task by ID. Returns True if a row was deleted."""
        task = self.db.get(TaskModel, task_id)
        if task is None:
            return False

        self.db.delete(task)
        self.db.commit()
        return True

    # --- Batch state transitions (used by the scheduler) ---

    def move_to_running(self, created_limit: datetime, now: datetime) -> int:
        """
        Move all CREATED tasks older than `created_limit` to RUNNING.

        This is a bulk UPDATE (not entity-based), so it is efficient even
        with thousands of tasks. `started_at` is set to `now`.
        Returns the number of affected rows.
        """
        result = self.db.execute(
            update(TaskModel)
            .where(TaskModel.state == TaskState.CREATED)
            .where(TaskModel.created_at < created_limit)
            .values(state=TaskState.RUNNING, started_at=now)
        )
        self.db.commit()
        return result.rowcount or 0

    def move_to_done(self, running_limit: datetime) -> int:
        """
        Move all RUNNING tasks that started before `running_limit` to DONE.

        Only tasks with a non-null `started_at` are considered (safety guard).
        Returns the number of affected rows.
        """
        result = self.db.execute(
            update(TaskModel)
            .where(TaskModel.state == TaskState.RUNNING)
            .where(TaskModel.started_at.is_not(None))
            .where(TaskModel.started_at < running_limit)
            .values(state=TaskState.DONE)
        )
        self.db.commit()
        return result.rowcount or 0
