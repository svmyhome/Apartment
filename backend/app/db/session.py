from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Создаёт пул соединений только при первом обращении к БД."""
    return create_engine(get_settings().database_url)


def get_session() -> Session:
    return sessionmaker(bind=get_engine())()
