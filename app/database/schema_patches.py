"""Lightweight schema patches for existing SQLite databases."""

from __future__ import annotations

import logging

from sqlalchemy import text

from app.database.session import engine

logger = logging.getLogger(__name__)


def ensure_schema_patches() -> None:
    """Add columns create_all cannot add on an existing SQLite DB."""
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as conn:
        cols = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()
        }
        if "preferred_language" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN preferred_language "
                    "VARCHAR(5) NOT NULL DEFAULT 'sw'"
                )
            )
            logger.info("Added users.preferred_language column")
