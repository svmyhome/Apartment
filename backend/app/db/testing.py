from os import getenv

from sqlalchemy.engine import make_url


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
