from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.api.problems import RoomHasPurchasesError
from backend.app.models.purchase import Purchase
from backend.app.models.room import Room


def delete_room(session: Session, room: Room) -> None:
    """Удаляет комнату, только если к ней не привязаны покупки."""
    if session.scalar(select(exists().where(Purchase.room_id == room.id))):
        raise RoomHasPurchasesError

    try:
        session.delete(room)
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise RoomHasPurchasesError from error
