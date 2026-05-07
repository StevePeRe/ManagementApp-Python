"""
API: Pydantic schemas (request/response models).

Separating schemas from domain models means the API contract can evolve
independently of the internal data model. Pydantic handles validation,
serialization, and OpenAPI documentation generation automatically.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.tasks.domain.task_state import TaskState


class TaskBase(BaseModel):
    """
    Shared fields for create, update, and read operations.
    - `name` is validated: stripped of whitespace and checked for emptiness.
    - `state` defaults to CREATED so the client can omit it on creation.
    """
    name: str = Field(min_length=1, max_length=255)
    state: TaskState = TaskState.CREATED

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Strip whitespace and reject blank names (e.g. '   ')."""
        clean = value.strip()
        if not clean:
            raise ValueError("name must not be blank")
        return clean


class TaskCreate(TaskBase):
    """Schema for POST /api/tasks (request body)."""
    pass


class TaskUpdate(TaskBase):
    """Schema for PUT /api/tasks/{id} (request body)."""
    pass


class TaskRead(TaskBase):
    """
    Schema for GET /api/tasks (response).

    `model_config = ConfigDict(from_attributes=True)` enables automatic
    conversion from SQLAlchemy model instances to this Pydantic model
    without manual mapping.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    started_at: datetime | None = None
