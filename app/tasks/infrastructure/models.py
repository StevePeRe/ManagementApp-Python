"""
Infrastructure: SQLAlchemy ORM model for the "tasks" table.

This is the database representation of a Task. It maps directly to the
domain concept but adds infrastructure concerns (column types, defaults, etc.).
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum as SqlEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.tasks.domain.task_state import TaskState


class TaskModel(Base):
    """
    Database model for tasks.

    Key decisions:
    - `native_enum=False` stores the enum as a string (varchar) in the DB,
      making it portable across SQLite and PostgreSQL without custom types.
    - `created_at` uses `server_default=func.now()` so the timestamp is set
      by the DB, not the application — avoids clock-drift issues.
    - `started_at` is nullable because it is set only when the task transitions
      from CREATED -> RUNNING.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[TaskState] = mapped_column(
        SqlEnum(TaskState, name="task_state", native_enum=False),
        nullable=False,
        default=TaskState.CREATED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
