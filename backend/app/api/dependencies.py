from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.app.db.session import get_session


def get_db_session() -> Generator[Session, None, None]:
    """Создаёт сессию для одного запроса и всегда закрывает её."""
    session = get_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
