"""
Database layer: engine, session factory, and base model.

SQLAlchemy is used as the ORM. The engine and session are configured once
at import time via Settings. SQLite is used locally (no external deps) and
PostgreSQL in production/Docker — the switch is transparent thanks to the
config layer.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
database_url = settings.sqlalchemy_database_url

# SQLite requires check_same_thread=False because FastAPI is multi-threaded
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args, future=True, echo=settings.db_echo)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    Every model inherits from this and is picked up by metadata.create_all().
    """
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and closes it when
    the request finishes (regardless of success or failure).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_database_connection() -> None:
    """
    Quick health check: execute SELECT 1 to verify the DB is reachable.
    Called during application startup (lifespan).
    """
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
