from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.api.problems import ResourceNotFoundError, RoomHasPurchasesError
from backend.app.models.project import Project
from backend.app.models.purchase import Purchase
from backend.app.models.room import Room
from backend.app.services.purchases import get_purchase_room
from backend.app.services.rooms import delete_room
from backend.tests.factories import create_account

pytestmark = pytest.mark.integration


def _project_with_room(session: Session) -> tuple[Project, Room]:
    account = create_account(session)
    project = Project(
        owner_id=account.id,
        name="Test project",
        property_type="apartment",
        planned_budget=Decimal("1000.00"),
    )
    room = Room(project=project, name="Kitchen")
    session.add_all((project, room))
    session.flush()
    return project, room


def _purchase(project: Project, room: Room | None, **values: object) -> Purchase:
    fields: dict[str, object] = {
        "project_id": project.id,
        "room_id": room.id if room else None,
        "name": "Test purchase",
        "category": "materials",
        "planned_amount": Decimal("10.00"),
        "actual_amount": None,
        "status": "planned",
        "note": None,
        "purchased_on": None,
    }
    fields.update(values)
    return Purchase(**fields)  # type: ignore[arg-type]


def test_purchase_migration_creates_table_constraints_and_indexes(test_engine: Engine) -> None:
    inspector = inspect(test_engine)
    assert "purchases" in inspector.get_table_names()
    assert {constraint["name"] for constraint in inspector.get_check_constraints("purchases")} == {
        "ck_purchases_planned_amount_nonnegative",
        "ck_purchases_actual_amount_nonnegative",
        "ck_purchases_status",
        "ck_purchases_category",
        "ck_purchases_purchase_details_for_status",
    }
    assert {index["name"] for index in inspector.get_indexes("purchases")} == {
        "ix_purchases_project_id",
        "ix_purchases_room_id",
        "ix_purchases_project_id_status",
        "ix_purchases_project_id_purchased_on",
    }


@pytest.mark.parametrize(
    "values",
    [
        {"planned_amount": Decimal("-0.01")},
        {"actual_amount": Decimal("-0.01"), "status": "purchased"},
        {"status": "unknown"},
        {"category": "unknown"},
        {"actual_amount": Decimal("1.00")},
    ],
)
def test_purchase_check_constraints(db_session: Session, values: dict[str, object]) -> None:
    project, room = _project_with_room(db_session)
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(_purchase(project, room, **values))
            db_session.flush()


def test_purchase_room_must_belong_to_project(db_session: Session) -> None:
    project, _ = _project_with_room(db_session)
    _, foreign_room = _project_with_room(db_session)

    assert get_purchase_room(db_session, project_id=project.id, room_id=None) is None
    with pytest.raises(ResourceNotFoundError):
        get_purchase_room(db_session, project_id=project.id, room_id=foreign_room.id)


def test_room_with_purchase_cannot_be_deleted(db_session: Session) -> None:
    project, room = _project_with_room(db_session)
    db_session.add(_purchase(project, room))
    db_session.flush()

    with pytest.raises(RoomHasPurchasesError):
        delete_room(db_session, room)

    assert db_session.get(Room, room.id) is not None
