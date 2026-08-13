from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app.db.session import get_engine


class DatabaseUnavailableError(Exception):
    """База данных не смогла обработать проверочный запрос."""


def check_database() -> None:
    """Проверяет доступность БД лёгким запросом в рамках HTTP-запроса."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (OSError, SQLAlchemyError) as error:
        raise DatabaseUnavailableError from error
