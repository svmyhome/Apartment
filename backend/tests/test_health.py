import pytest
from fastapi.testclient import TestClient

from backend.app.db.health import DatabaseUnavailableError, check_database
from backend.app.main import app


@pytest.fixture
def client() -> TestClient:
    """Клиент вызывает FastAPI-приложение в памяти, без Uvicorn и сети."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    """Не даёт подмене зависимости одного теста повлиять на другой."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_health_returns_ok(client: TestClient) -> None:
    app.dependency_overrides[check_database] = lambda: None

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_service_unavailable_when_database_is_down(client: TestClient) -> None:
    def unavailable_database() -> None:
        raise DatabaseUnavailableError

    app.dependency_overrides[check_database] = unavailable_database

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {"status": "database_unavailable"}


def test_health_allows_vite_origin(client: TestClient) -> None:
    app.dependency_overrides[check_database] = lambda: None

    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_health_allows_vite_preflight_request(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_health_does_not_allow_unknown_origin(client: TestClient) -> None:
    app.dependency_overrides[check_database] = lambda: None

    response = client.get("/api/v1/health", headers={"Origin": "https://untrusted.example"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
