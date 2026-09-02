"""create purchases table

Revision ID: 5f3c2d1a9e8b
Revises: 77560e38cf8c
Create Date: 2026-09-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5f3c2d1a9e8b"
down_revision: Union[str, Sequence[str], None] = "77560e38cf8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "purchases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("planned_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("actual_amount", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("purchased_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("planned_amount >= 0", name="ck_purchases_planned_amount_nonnegative"),
        sa.CheckConstraint(
            "actual_amount IS NULL OR actual_amount >= 0",
            name="ck_purchases_actual_amount_nonnegative",
        ),
        sa.CheckConstraint(
            "status IN ('planned', 'purchased', 'cancelled')", name="ck_purchases_status"
        ),
        sa.CheckConstraint(
            "category IN ('materials', 'plumbing', 'electrical', 'furniture', "
            "'appliances', 'decor', 'services', 'tools', 'delivery', 'other')",
            name="ck_purchases_category",
        ),
        sa.CheckConstraint(
            "status = 'purchased' OR (actual_amount IS NULL AND purchased_on IS NULL)",
            name="ck_purchases_purchase_details_for_status",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_purchases_project_id"), "purchases", ["project_id"], unique=False)
    op.create_index(op.f("ix_purchases_room_id"), "purchases", ["room_id"], unique=False)
    op.create_index("ix_purchases_project_id_status", "purchases", ["project_id", "status"], unique=False)
    op.create_index(
        "ix_purchases_project_id_purchased_on",
        "purchases",
        ["project_id", "purchased_on"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_purchases_project_id_purchased_on", table_name="purchases")
    op.drop_index("ix_purchases_project_id_status", table_name="purchases")
    op.drop_index(op.f("ix_purchases_room_id"), table_name="purchases")
    op.drop_index(op.f("ix_purchases_project_id"), table_name="purchases")
    op.drop_table("purchases")
