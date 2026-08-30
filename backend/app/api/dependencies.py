from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.api.problems import UnauthorizedError
from backend.app.core.security import _InvalidAccessToken, decode_access_token
from backend.app.db.session import get_session
from backend.app.models.account import Account

_bearer_scheme = HTTPBearer(auto_error=False)


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


def get_current_account(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[Session, Depends(get_db_session)],
) -> Account:
    """Возвращает аккаунт из Bearer JWT или единый нейтральный ответ 401."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError

    try:
        claims = decode_access_token(credentials.credentials)
        account_id = UUID(str(claims["sub"]))
    except (_InvalidAccessToken, KeyError, TypeError, ValueError) as error:
        raise UnauthorizedError from error

    account = session.get(Account, account_id)
    if account is None:
        raise UnauthorizedError

    return account
