from app.tasks.domain.exceptions import TaskNotFoundError
from app.tasks.domain.task_state import TaskState


def test_task_state_enum_values():
    assert TaskState.CREATED.value == "CREATED"
    assert TaskState.RUNNING.value == "RUNNING"
    assert TaskState.DONE.value == "DONE"


def test_task_state_members():
    assert list(TaskState) == [TaskState.CREATED, TaskState.RUNNING, TaskState.DONE]


def test_task_not_found_error_message():
    exc = TaskNotFoundError(42)
    assert str(exc) == "The task with id 42 was not found."
    assert isinstance(exc, Exception)
