import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.account import Account
    from backend.app.models.purchase import Purchase
    from backend.app.models.room import Room


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(
            "property_type IN ('apartment', 'house', 'other')",
            name="ck_projects_property_type",
        ),
        CheckConstraint(
            "planned_budget >= 0",
            name="ck_projects_planned_budget_nonnegative",
        ),
        Index("ix_projects_owner_id_is_archived", "owner_id", "is_archived"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    property_type: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    planned_budget: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_archived: Mapped[bool] = mapped_column(nullable=False, server_default=false())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    owner: Mapped["Account"] = relationship(back_populates="projects")

    rooms: Mapped[list["Room"]] = relationship(back_populates="project")
    purchases: Mapped[list["Purchase"]] = relationship(back_populates="project")
