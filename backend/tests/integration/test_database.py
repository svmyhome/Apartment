import os

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command
from backend.app.db.testing import get_test_database_url

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def test_database_url() -> str:
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("TEST_DATABASE_URL не задан: интеграционные тесты пропущены.")
    return get_test_database_url()


def test_migrations_create_accounts_table(test_database_url: str) -> None:
    """Миграции и запрос выполняются только в отдельно защищённой test database."""
    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")

    engine = create_engine(test_database_url)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT 1")) == 1
            assert "accounts" in inspect(connection).get_table_names()
    finally:
        engine.dispose()
