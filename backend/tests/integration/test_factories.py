import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.account import Account
from backend.tests.factories import (
    authorization_header,
    create_account,
    project_payload,
    purchase_payload,
    room_payload,
)

pytestmark = pytest.mark.integration


def test_factories_create_isolated_accounts(db_session: Session) -> None:
    first = create_account(db_session, name="First")
    second = create_account(db_session, name="Second")
    db_session.commit()

    accounts = db_session.scalars(select(Account).order_by(Account.name)).all()

    assert [account.name for account in accounts] == ["First", "Second"]
    assert first.email != second.email
    assert authorization_header(first.id)["Authorization"].startswith("Bearer ")


def test_resource_payload_factories_are_unique() -> None:
    assert project_payload()["name"] != project_payload()["name"]
    assert room_payload()["name"] != room_payload()["name"]
    assert purchase_payload()["name"] != purchase_payload()["name"]
