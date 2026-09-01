import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

pytestmark = pytest.mark.integration


def test_migrations_create_accounts_table(test_engine: Engine) -> None:
    """Миграции и запрос выполняются только в отдельно защищённой test database."""
    with test_engine.connect() as connection:
        assert connection.scalar(text("SELECT 1")) == 1
        assert "accounts" in inspect(connection).get_table_names()
