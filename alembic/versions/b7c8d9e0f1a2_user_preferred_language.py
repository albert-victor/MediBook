"""Add users.preferred_language for SMS / notification locale."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "preferred_language",
            sa.String(length=5),
            nullable=False,
            server_default="sw",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "preferred_language")
