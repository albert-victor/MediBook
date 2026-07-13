"""Specialization lookup table - single source of truth for medical specialties."""

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Specialization(Base, TimestampMixin):
    __tablename__ = "specializations"
    __table_args__ = (
        Index("ix_specializations_name", "name"),
        Index("ix_specializations_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    doctors: Mapped[list["Doctor"]] = relationship(
        "Doctor",
        back_populates="specialization",
    )

    def __repr__(self) -> str:
        return f"<Specialization {self.slug}>"
