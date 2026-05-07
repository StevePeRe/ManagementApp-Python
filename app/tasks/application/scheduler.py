"""
Application: task state scheduler.

Uses APScheduler (a lightweight cron-like library) to periodically
transition tasks through their lifecycle:
    CREATED (after 2 min) → RUNNING (after 8 min) → DONE

This simulates what would typically be a background worker or a
database-level scheduled job in production. The scheduler is started
during application startup (lifespan) and runs in background threads.

Key design decisions:
- Single DB session per tick (no shared state with request threads)
- Logging instead of silent failure
- Configurable via environment variables
"""

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.tasks.application.service import TaskService
from app.tasks.infrastructure.repository import TaskRepository

logger = logging.getLogger(__name__)


def _update_task_states() -> None:
    """
    Called periodically by the scheduler. Creates its own DB session,
    performs both state transitions, then closes the session.
    On error, rolls back and logs the exception (does NOT crash the scheduler).
    """
    settings = get_settings()
    now = datetime.utcnow()
    db = SessionLocal()

    try:
        service = TaskService(TaskRepository(db))

        moved_to_running = service.move_created_to_running(
            created_limit=now - timedelta(minutes=settings.task_created_to_running_minutes),
            now=now,
        )
        moved_to_done = service.move_running_to_done(
            running_limit=now - timedelta(minutes=settings.task_running_to_done_minutes),
        )

        if moved_to_running > 0 or moved_to_done > 0:
            logger.info(
                "Task scheduler applied transitions: CREATED->RUNNING=%s, RUNNING->DONE=%s",
                moved_to_running,
                moved_to_done,
            )
    except Exception:
        db.rollback()
        logger.exception("Task scheduler failed while updating task states.")
    finally:
        db.close()


def start_task_state_scheduler() -> BackgroundScheduler | None:
    """
    Configure and start the background scheduler.

    Returns None if the scheduler is disabled via env var (useful for tests
    or local development where you don't want automatic state transitions).
    """
    settings = get_settings()
    if not settings.scheduler_enabled:
        logger.info("Task scheduler disabled by configuration.")
        return None

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _update_task_states,
        trigger="interval",
        seconds=settings.scheduler_interval_seconds,
        id="task-state-scheduler",
        replace_existing=True,
        max_instances=1,  # Never run overlapping ticks
        coalesce=True,     # If a tick is missed, skip it — don't catch up
    )
    scheduler.start()
    logger.info("Task scheduler started with interval=%ss.", settings.scheduler_interval_seconds)
    return scheduler
