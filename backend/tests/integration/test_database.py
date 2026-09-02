import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

pytestmark = pytest.mark.integration


def test_migrations_create_accounts_table(test_engine: Engine) -> None:
    """Миграции и запрос выполняются только в отдельно защищённой test database."""
    with test_engine.connect() as connection:
        assert connection.scalar(text("SELECT 1")) == 1
        assert "accounts" in inspect(connection).get_table_names()


def test_migrations_create_rooms_table_and_project_index(test_engine: Engine) -> None:
    with test_engine.connect() as connection:
        inspector = inspect(connection)
        assert "rooms" in inspector.get_table_names()
        assert "ix_rooms_project_id" in {index["name"] for index in inspector.get_indexes("rooms")}
