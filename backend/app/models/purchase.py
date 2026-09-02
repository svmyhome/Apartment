import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.project import Project
    from backend.app.models.room import Room


class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint("planned_amount >= 0", name="ck_purchases_planned_amount_nonnegative"),
        CheckConstraint(
            "actual_amount IS NULL OR actual_amount >= 0",
            name="ck_purchases_actual_amount_nonnegative",
        ),
        CheckConstraint(
            "status IN ('planned', 'purchased', 'cancelled')",
            name="ck_purchases_status",
        ),
        CheckConstraint(
            "category IN ('materials', 'plumbing', 'electrical', 'furniture', "
            "'appliances', 'decor', 'services', 'tools', 'delivery', 'other')",
            name="ck_purchases_category",
        ),
        CheckConstraint(
            "status = 'purchased' OR (actual_amount IS NULL AND purchased_on IS NULL)",
            name="ck_purchases_purchase_details_for_status",
        ),
        Index("ix_purchases_project_id_status", "project_id", "status"),
        Index("ix_purchases_project_id_purchased_on", "project_id", "purchased_on"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rooms.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    actual_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchased_on: Mapped[date | None] = mapped_column(Date(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    project: Mapped["Project"] = relationship(back_populates="purchases")
    room: Mapped["Room | None"] = relationship(back_populates="purchases")
