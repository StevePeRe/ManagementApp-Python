"""
FastAPI application entry point.

Architecture overview:
- Lifespan: runs DB verification and scheduler startup on boot, graceful
  shutdown on exit.
- Routers: currently only the task router under /api/tasks.
- Exception handlers: global handlers for 404 (TaskNotFoundError) and 400
  (RequestValidationError) that return consistent JSON error responses.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import Base, engine, verify_database_connection
from app.tasks.api.router import router as task_router
from app.tasks.application.scheduler import start_task_state_scheduler
from app.tasks.domain.exceptions import TaskNotFoundError

# Force-load models so SQLAlchemy registers them with Base.metadata
from app.tasks.infrastructure import models as task_models  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle:
    - Startup: verify DB connection, create tables if needed, start scheduler.
    - Shutdown: gracefully stop the scheduler (if running).
    """
    verify_database_connection()
    logger.info("Database connection check successful.")
    Base.metadata.create_all(bind=engine)
    scheduler = start_task_state_scheduler()
    try:
        yield
    finally:
        if scheduler is not None and scheduler.running:
            scheduler.shutdown(wait=False)


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(task_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Simple health-check endpoint. Returns {"status": "ok"}."""
    return {"status": "ok"}


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(
    request: Request, exc: TaskNotFoundError,
) -> JSONResponse:
    """
    Global handler for TaskNotFoundError → 404 JSON response.
    Format matches the original Java project's error contract.
    """
    return JSONResponse(
        status_code=404,
        content={
            "message": str(exc),
            "exception": exc.__class__.__name__,
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(
    request: Request, exc: RequestValidationError,
) -> JSONResponse:
    """
    Global handler for Pydantic validation errors → 400 JSON response.
    Extracts field-level errors so the frontend can display per-field messages.
    """
    errors: dict[str, str] = {}
    for error in exc.errors():
        location = error.get("loc", [])
        if len(location) >= 2 and location[0] == "body":
            errors[str(location[-1])] = error.get("msg", "Invalid value")

    return JSONResponse(
        status_code=400,
        content={
            "message": "Validation failed",
            "exception": exc.__class__.__name__,
            "path": request.url.path,
            "errors": errors,
        },
    )
