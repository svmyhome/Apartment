from os import getenv

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine, make_url


def get_test_database_url() -> str:
    """Возвращает безопасно проверенный URL отдельной тестовой БД."""
    database_url = getenv("TEST_DATABASE_URL")
    if not database_url:
        raise RuntimeError("Для интеграционных тестов задайте TEST_DATABASE_URL.")

    database_name = make_url(database_url).database
    if not database_name or not database_name.endswith("_test"):
        raise RuntimeError(
            "TEST_DATABASE_URL должен указывать на БД с именем, оканчивающимся на '_test'."
        )

    return database_url


def truncate_test_tables(engine: Engine) -> None:
    """Очищает все прикладные таблицы только в БД из TEST_DATABASE_URL."""
    test_url = make_url(get_test_database_url())
    if engine.url != test_url:
        raise RuntimeError("Очистка разрешена только для TEST_DATABASE_URL.")

    table_names = [
        table_name
        for table_name in inspect(engine).get_table_names()
        if table_name != "alembic_version"
    ]
    if not table_names:
        return

    quote = engine.dialect.identifier_preparer.quote
    tables = ", ".join(quote(table_name) for table_name in table_names)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
