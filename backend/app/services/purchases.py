from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.problems import ResourceNotFoundError
from backend.app.models.room import Room


def get_purchase_room(session: Session, *, project_id: UUID, room_id: UUID | None) -> Room | None:
    """Возвращает комнату покупки только из указанного проекта."""
    if room_id is None:
        return None

    room = session.scalar(select(Room).where(Room.id == room_id, Room.project_id == project_id))
    if room is None:
        raise ResourceNotFoundError
    return room
