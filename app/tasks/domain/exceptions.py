"""
Domain: custom exceptions.

Defined in the domain layer so that application and infrastructure code
can reference them without coupling to a framework.
"""


class TaskNotFoundError(Exception):
    """
    Raised when a task ID does not exist in the database.
    Caught by FastAPI's exception handler (in app/main.py) and mapped
    to a 404 JSON response.
    """
    def __init__(self, task_id: int) -> None:
        super().__init__(f"The task with id {task_id} was not found.")
