from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.account import Account


def create_account(session: Session, *, name: str = "Test User") -> Account:
    """Создаёт и сохраняет уникальный аккаунт для интеграционного теста."""
    account = Account(
        id=uuid4(),
        name=name,
        email=f"{uuid4()}@example.test",
        password_hash=hash_password("test-password"),
    )
    session.add(account)
    session.flush()
    return account


def authorization_header(account_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(account_id)}"}


def project_payload() -> dict[str, str]:
    return {
        "name": f"Project {uuid4()}",
        "property_type": "apartment",
        "address": "Test address",
        "planned_budget": "100000.00",
    }


def room_payload() -> dict[str, str]:
    return {"name": f"Room {uuid4()}"}


def purchase_payload() -> dict[str, str | None]:
    return {
        "name": f"Purchase {uuid4()}",
        "room_id": None,
        "category": "materials",
        "planned_amount": "1000.00",
        "actual_amount": None,
        "status": "planned",
        "note": None,
        "purchased_on": None,
    }
