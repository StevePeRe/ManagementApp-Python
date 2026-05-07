"""
Domain: TaskState enum.

This is the purest layer of the hexagonal architecture — zero dependencies
on frameworks or infrastructure. The enum defines the lifecycle of a task:
CREATED -> RUNNING -> DONE (unidirectional, no rollback).
"""

from enum import Enum


class TaskState(str, Enum):
    """
    Task lifecycle states.
    Inheriting from `str` makes each member JSON-serializable by default
    (no custom encoder needed). Inheriting from `Enum` guarantees type safety.
    """
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    DONE = "DONE"
