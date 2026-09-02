from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import SecretStr

import backend.app.api.dependencies as dependencies
import backend.app.core.security as security
from backend.app.api.problems import UnauthorizedError, problem_response
from backend.app.models.account import Account


@pytest.fixture
def jwt_settings(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    settings = SimpleNamespace(
        jwt_secret_key=SecretStr("a" * 64),
        jwt_algorithm="HS256",
        jwt_issuer="apartment-api",
        jwt_audience="apartment-web",
        access_token_expire_seconds=900,
    )
    monkeypatch.setattr(security, "get_settings", lambda: settings)
    return settings


def test_password_hash_is_verified_and_wrong_password_is_rejected() -> None:
    password_hash = security.hash_password("correct password")

    assert security.verify_password("correct password", password_hash) is True
    assert security.verify_password("wrong password", password_hash) is False


def test_access_token_contains_only_contract_claims_and_is_decoded(
    jwt_settings: SimpleNamespace,
) -> None:
    account_id = uuid4()

    token = security.create_access_token(account_id)
    claims = security.decode_access_token(token)

    assert set(claims) == {"sub", "iat", "exp", "iss", "aud", "jti"}
    assert claims["sub"] == str(account_id)
    assert claims["iss"] == jwt_settings.jwt_issuer
    assert claims["aud"] == jwt_settings.jwt_audience
    assert UUID(str(claims["jti"]))


@pytest.mark.parametrize("kind", ["expired", "wrong_audience", "tampered"])
def test_invalid_access_tokens_are_rejected(jwt_settings: SimpleNamespace, kind: str) -> None:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "iss": jwt_settings.jwt_issuer,
        "aud": jwt_settings.jwt_audience,
        "jti": str(uuid4()),
    }
    if kind == "expired":
        claims["exp"] = now - timedelta(seconds=1)
    if kind == "wrong_audience":
        claims["aud"] = "another-audience"

    token = jwt.encode(
        claims,
        jwt_settings.jwt_secret_key.get_secret_value(),
        algorithm=jwt_settings.jwt_algorithm,
    )
    if kind == "tampered":
        token = f"{token}changed"

    with pytest.raises(security._InvalidAccessToken, match="Invalid access token"):
        security.decode_access_token(token)


class _FakeSession:
    def __init__(self, account: Account | None) -> None:
        self.account = account

    def get(self, model: type[Account], account_id: UUID) -> Account | None:
        return self.account if self.account is not None and self.account.id == account_id else None


def _protected_app() -> FastAPI:
    test_app = FastAPI()

    @test_app.exception_handler(UnauthorizedError)
    def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
        return problem_response(exc, headers={"WWW-Authenticate": "Bearer"})

    @test_app.get("/protected")
    def protected(account: Account = Depends(dependencies.get_current_account)) -> dict[str, str]:
        return {"account_id": str(account.id)}

    return test_app


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Basic credentials"}])
def test_missing_or_wrong_authorization_scheme_returns_neutral_problem(
    headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(dependencies, "decode_access_token", lambda token: {})
    test_app = _protected_app()
    test_app.dependency_overrides[dependencies.get_db_session] = lambda: _FakeSession(None)

    response = TestClient(test_app).get("/protected", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "Недействительные данные авторизации."


def test_invalid_token_and_deleted_account_return_the_same_problem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account_id = uuid4()
    test_app = _protected_app()
    test_app.dependency_overrides[dependencies.get_db_session] = lambda: _FakeSession(None)
    client = TestClient(test_app)

    def invalid_token(token: str) -> dict[str, object]:
        raise security._InvalidAccessToken("Invalid access token")

    monkeypatch.setattr(dependencies, "decode_access_token", invalid_token)
    invalid_response = client.get("/protected", headers={"Authorization": "Bearer invalid"})
    monkeypatch.setattr(dependencies, "decode_access_token", lambda token: {"sub": str(account_id)})
    deleted_response = client.get("/protected", headers={"Authorization": "Bearer valid"})

    assert invalid_response.status_code == deleted_response.status_code == 401
    assert invalid_response.headers["www-authenticate"] == "Bearer"
    assert deleted_response.headers["www-authenticate"] == "Bearer"
    assert invalid_response.json() == deleted_response.json()


def test_current_account_is_returned_for_a_valid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    account = Account(id=uuid4(), name="Test", email="test@example.com", password_hash="hash")
    test_app = _protected_app()
    test_app.dependency_overrides[dependencies.get_db_session] = lambda: _FakeSession(account)
    monkeypatch.setattr(dependencies, "decode_access_token", lambda token: {"sub": str(account.id)})

    response = TestClient(test_app).get("/protected", headers={"Authorization": "Bearer valid"})

    assert response.status_code == 200
    assert response.json() == {"account_id": str(account.id)}
