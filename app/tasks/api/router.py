"""
API: HTTP router for /api/tasks endpoints.

Follows RESTful conventions:
- GET /api/tasks        → list all tasks
- GET /api/tasks/{id}   → get one task (404 if not found)
- POST /api/tasks       → create a task (201 + Location header)
- PUT /api/tasks/{id}   → update task (202)
- DELETE /api/tasks/{id} → delete task (202)

Note: 202 (Accepted) is used instead of 200 for update/delete because
the original Java project did so. This is a design choice that the
frontend must match on the consuming side.
"""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.tasks.api.schemas import TaskCreate, TaskRead, TaskUpdate
from app.tasks.application.service import TaskService
from app.tasks.infrastructure.repository import TaskRepository

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    """
    Factory function wired into FastAPI's dependency injection.
    Every request gets a fresh DB session and a service + repository instance.
    """
    return TaskService(TaskRepository(db))


@router.get("", response_model=list[TaskRead])
def get_all_tasks(
    page_size: str | None = Query(default=None, alias="pageSize"),
    service: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    # page_size is accepted for API compatibility with the Java project
    # but pagination is not yet implemented — everything is returned.
    _ = page_size
    return service.get_all_tasks()


@router.get("/{task_id}", response_model=TaskRead)
def get_task_by_id(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    """Returns a single task. Raises 404 (TaskNotFoundError) if missing."""
    return service.get_task_by_id(task_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> Response:
    """
    Create a task and return 201 with a Location header pointing to the
    new resource. The response body is intentionally empty (matching the
    original Java API convention).
    """
    task = service.create_task(payload)
    return Response(
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"/api/tasks/{task.id}"},
    )


@router.put("/{task_id}", status_code=status.HTTP_202_ACCEPTED)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> Response:
    """Update task name and/or state. Raises 404 if not found."""
    service.update_task(task_id, payload)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.delete("/{task_id}", status_code=status.HTTP_202_ACCEPTED)
def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> Response:
    """Delete a task. Raises 404 if not found."""
    service.delete_task(task_id)
    return Response(status_code=status.HTTP_202_ACCEPTED)
