from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.tasks.domain.task_state import TaskState
from app.tasks.infrastructure.models import TaskModel

TEST_DATABASE_URL = "sqlite:///./test_management.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database) -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_task(db_session: Session) -> TaskModel:
    task = TaskModel(name="Test Task", state=TaskState.CREATED)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def created_task(db_session: Session) -> TaskModel:
    task = TaskModel(
        name="Old Created Task",
        state=TaskState.CREATED,
        created_at=datetime(2020, 1, 1, 0, 0, 0),
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def running_task(db_session: Session) -> TaskModel:
    task = TaskModel(
        name="Old Running Task",
        state=TaskState.RUNNING,
        created_at=datetime(2020, 1, 1, 0, 0, 0),
        started_at=datetime(2020, 1, 1, 0, 0, 0),
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task
