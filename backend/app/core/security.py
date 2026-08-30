from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from backend.app.core.config import get_settings

_password_hasher = PasswordHash.recommended()


class _InvalidAccessToken(Exception):
    """Нейтральная внутренняя ошибка недействительного access-токена."""


def hash_password(password: str) -> str:
    """Возвращает Argon2-хеш пароля."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Проверяет пароль, не раскрывая причину неверного хеша."""
    try:
        return _password_hasher.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(account_id: UUID) -> str:
    """Выпускает короткоживущий JWT для аккаунта."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(account_id),
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_expire_seconds),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": str(uuid4()),
    }
    return jwt.encode(
        claims,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, object]:
    """Проверяет JWT и возвращает claims либо нейтральную ошибку."""
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "iat", "exp", "iss", "aud", "jti"]},
        )
        UUID(str(claims["sub"]))
        if not str(claims["jti"]).strip():
            raise ValueError("Empty token identifier")
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
        raise _InvalidAccessToken("Invalid access token") from error

    return dict(claims)
