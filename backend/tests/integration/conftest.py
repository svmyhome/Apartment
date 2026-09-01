import os
from collections.abc import Generator

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from backend.app.db.testing import get_test_database_url, truncate_test_tables


@pytest.fixture(scope="session")
def test_database_url() -> str:
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL не задан: интеграционные тесты пропущены.")
    return get_test_database_url()


@pytest.fixture(scope="session")
def test_engine(test_database_url: str) -> Generator[Engine, None, None]:
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")
    engine = create_engine(test_database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def clear_test_tables(test_engine: Engine) -> Generator[None, None, None]:
    truncate_test_tables(test_engine)
    yield
    truncate_test_tables(test_engine)


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    session = sessionmaker(bind=test_engine)()
    try:
        yield session
    finally:
        session.close()
