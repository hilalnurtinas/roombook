"""bookings schema: users, rooms, bookings + overlap exclusion constraint

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
    )

    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'rejected', 'cancelled', 'skipped_conflict')",
            name="ck_bookings_status",
        ),
        sa.CheckConstraint("end_at > start_at", name="ck_bookings_end_after_start"),
    )
    op.create_index("ix_bookings_start_at", "bookings", ["start_at"])

    # BR-1's DB-level backstop: no two non-cancelled/non-rejected bookings on the same room
    # may have overlapping [start_at, end_at) ranges. Half-open range matches the service
    # layer's overlap check so back-to-back bookings are never treated as conflicting.
    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT ex_bookings_no_room_overlap
        EXCLUDE USING gist (
            room_id WITH =,
            tstzrange(start_at, end_at, '[)') WITH &&
        )
        WHERE (status NOT IN ('cancelled', 'rejected'))
        """
    )


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_table("rooms")
    op.drop_table("users")
