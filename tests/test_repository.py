from datetime import datetime

from app.tasks.api.schemas import TaskCreate, TaskUpdate
from app.tasks.domain.task_state import TaskState
from app.tasks.infrastructure.models import TaskModel
from app.tasks.infrastructure.repository import TaskRepository


def test_find_all_empty(db_session):
    repo = TaskRepository(db_session)
    assert repo.find_all() == []


def test_find_all(sample_task, db_session):
    repo = TaskRepository(db_session)
    tasks = repo.find_all()
    assert len(tasks) == 1
    assert tasks[0].name == "Test Task"


def test_find_by_id(sample_task, db_session):
    repo = TaskRepository(db_session)
    task = repo.find_by_id(sample_task.id)
    assert task is not None
    assert task.name == "Test Task"


def test_find_by_id_not_found(db_session):
    repo = TaskRepository(db_session)
    assert repo.find_by_id(999) is None


def test_create(db_session):
    repo = TaskRepository(db_session)
    payload = TaskCreate(name="New Task")
    task = repo.create(payload)
    assert task.name == "New Task"
    assert task.state == TaskState.CREATED
    assert task.id is not None


def test_create_with_running_state(db_session):
    repo = TaskRepository(db_session)
    payload = TaskCreate(name="Running Task", state=TaskState.RUNNING)
    task = repo.create(payload)
    assert task.state == TaskState.RUNNING


def test_update(sample_task, db_session):
    repo = TaskRepository(db_session)
    payload = TaskUpdate(name="Updated", state=TaskState.RUNNING)
    updated = repo.update(sample_task.id, payload)
    assert updated is not None
    assert updated.name == "Updated"
    assert updated.state == TaskState.RUNNING


def test_update_not_found(db_session):
    repo = TaskRepository(db_session)
    payload = TaskUpdate(name="Nope", state=TaskState.CREATED)
    assert repo.update(999, payload) is None


def test_delete(sample_task, db_session):
    repo = TaskRepository(db_session)
    assert repo.delete(sample_task.id) is True
    assert repo.find_by_id(sample_task.id) is None


def test_delete_not_found(db_session):
    repo = TaskRepository(db_session)
    assert repo.delete(999) is False


def test_move_to_running(db_session):
    repo = TaskRepository(db_session)
    task1 = TaskModel(name="Old", state=TaskState.CREATED, created_at=datetime(2020, 1, 1))
    task2 = TaskModel(name="Recent", state=TaskState.CREATED, created_at=datetime(2030, 1, 1))
    db_session.add_all([task1, task2])
    db_session.commit()

    now = datetime(2025, 1, 1)
    count = repo.move_to_running(created_limit=datetime(2024, 1, 1), now=now)
    assert count == 1

    updated = repo.find_by_id(task1.id)
    assert updated.state == TaskState.RUNNING
    assert updated.started_at == now


def test_move_to_done(db_session):
    repo = TaskRepository(db_session)
    task1 = TaskModel(
        name="Running Old",
        state=TaskState.RUNNING,
        started_at=datetime(2020, 1, 1),
    )
    task2 = TaskModel(
        name="Running Recent",
        state=TaskState.RUNNING,
        started_at=datetime(2030, 1, 1),
    )
    task3 = TaskModel(
        name="Created Task",
        state=TaskState.CREATED,
    )
    db_session.add_all([task1, task2, task3])
    db_session.commit()

    count = repo.move_to_done(running_limit=datetime(2025, 1, 1))
    assert count == 1

    updated = repo.find_by_id(task1.id)
    assert updated.state == TaskState.DONE
