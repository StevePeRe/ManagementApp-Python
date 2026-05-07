from datetime import datetime

import pytest

from app.tasks.api.schemas import TaskCreate, TaskUpdate
from app.tasks.application.service import TaskService
from app.tasks.domain.exceptions import TaskNotFoundError
from app.tasks.domain.task_state import TaskState
from app.tasks.infrastructure.models import TaskModel
from app.tasks.infrastructure.repository import TaskRepository


@pytest.fixture
def service(db_session):
    return TaskService(TaskRepository(db_session))


def test_get_all_tasks_empty(service):
    assert service.get_all_tasks() == []


def test_get_all_tasks(service, sample_task):
    tasks = service.get_all_tasks()
    assert len(tasks) == 1


def test_get_task_by_id(service, sample_task):
    task = service.get_task_by_id(sample_task.id)
    assert task.name == "Test Task"


def test_get_task_by_id_not_found(service):
    with pytest.raises(TaskNotFoundError) as exc:
        service.get_task_by_id(999)
    assert "999" in str(exc.value)


def test_create_task(service):
    payload = TaskCreate(name="Service Task")
    task = service.create_task(payload)
    assert task.name == "Service Task"
    assert task.state == TaskState.CREATED


def test_update_task(service, sample_task):
    payload = TaskUpdate(name="Updated", state=TaskState.DONE)
    updated = service.update_task(sample_task.id, payload)
    assert updated.name == "Updated"
    assert updated.state == TaskState.DONE


def test_update_task_not_found(service):
    with pytest.raises(TaskNotFoundError):
        service.update_task(999, TaskUpdate(name="Nope", state=TaskState.CREATED))


def test_delete_task(service, sample_task):
    service.delete_task(sample_task.id)
    assert service.get_all_tasks() == []


def test_delete_task_not_found(service):
    with pytest.raises(TaskNotFoundError):
        service.delete_task(999)


def test_move_created_to_running(service, created_task):
    now = datetime(2025, 1, 1)
    count = service.move_created_to_running(created_limit=datetime(2024, 1, 1), now=now)
    assert count == 1


def test_move_running_to_done(service, running_task):
    count = service.move_running_to_done(running_limit=datetime(2025, 1, 1))
    assert count == 1
