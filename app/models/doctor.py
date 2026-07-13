"""Doctor profile - extends User (auth) with professional data."""

import json
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Doctor(Base, TimestampMixin):
    __tablename__ = "doctors"
    __table_args__ = (
        Index("ix_doctors_specialization_id", "specialization_id"),
        Index("ix_doctors_is_verified", "is_verified"),
        Index("ix_doctors_is_accepting", "is_accepting_patients"),
        Index("ix_doctors_gender", "gender"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    specialization_id: Mapped[int] = mapped_column(
        ForeignKey("specializations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    license_number: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    hospital_name: Mapped[str] = mapped_column(String(200), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_bio: Mapped[str | None] = mapped_column(String(280), nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(200), nullable=True)
    education: Mapped[str | None] = mapped_column(Text, nullable=True)
    languages: Mapped[str | None] = mapped_column(String(200), nullable=True)
    working_days: Mapped[str | None] = mapped_column(String(120), nullable=True)
    working_hours: Mapped[str | None] = mapped_column(String(60), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    consultation_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TZS", nullable=False)
    experience_years: Mapped[int] = mapped_column(nullable=False, default=0)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("4.80"), nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_accepting_patients: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="doctor_profile")
    specialization: Mapped["Specialization"] = relationship(
        "Specialization",
        back_populates="doctors",
    )
    availability_slots: Mapped[list["DoctorAvailability"]] = relationship(
        "DoctorAvailability",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="doctor",
    )
    reviews: Mapped[list["DoctorReview"]] = relationship(
        "DoctorReview",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )

    @property
    def display_name(self) -> str:
        return self.user.full_name if self.user else f"Doctor #{self.id}"

    @property
    def education_list(self) -> list[str]:
        if not self.education:
            return []
        try:
            data = json.loads(self.education)
            return data if isinstance(data, list) else [self.education]
        except json.JSONDecodeError:
            return [self.education]

    @property
    def languages_list(self) -> list[str]:
        if not self.languages:
            return []
        return [lang.strip() for lang in self.languages.split(",") if lang.strip()]

    @property
    def working_days_list(self) -> list[str]:
        if not self.working_days:
            return []
        return [day.strip() for day in self.working_days.split(",") if day.strip()]

    def __repr__(self) -> str:
        return f"<Doctor id={self.id} user_id={self.user_id}>"
