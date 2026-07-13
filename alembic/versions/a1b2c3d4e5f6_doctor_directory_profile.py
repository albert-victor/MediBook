"""Add extended doctor profile fields and reviews table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "d643373921a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("doctors", sa.Column("short_bio", sa.String(length=280), nullable=True))
    op.add_column("doctors", sa.Column("qualification", sa.String(length=200), nullable=True))
    op.add_column("doctors", sa.Column("education", sa.Text(), nullable=True))
    op.add_column("doctors", sa.Column("languages", sa.String(length=200), nullable=True))
    op.add_column("doctors", sa.Column("working_days", sa.String(length=120), nullable=True))
    op.add_column("doctors", sa.Column("working_hours", sa.String(length=60), nullable=True))
    op.add_column("doctors", sa.Column("gender", sa.String(length=10), nullable=True))
    op.add_column(
        "doctors",
        sa.Column("rating", sa.Numeric(precision=3, scale=2), server_default="4.80", nullable=False),
    )
    op.add_column(
        "doctors",
        sa.Column("review_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("ix_doctors_gender", "doctors", ["gender"], unique=False)

    op.create_table(
        "doctor_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("patient_name", sa.String(length=120), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_reviews_doctor_id", "doctor_reviews", ["doctor_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_doctor_reviews_doctor_id", table_name="doctor_reviews")
    op.drop_table("doctor_reviews")
    op.drop_index("ix_doctors_gender", table_name="doctors")
    op.drop_column("doctors", "review_count")
    op.drop_column("doctors", "rating")
    op.drop_column("doctors", "gender")
    op.drop_column("doctors", "working_hours")
    op.drop_column("doctors", "working_days")
    op.drop_column("doctors", "languages")
    op.drop_column("doctors", "education")
    op.drop_column("doctors", "qualification")
    op.drop_column("doctors", "short_bio")
