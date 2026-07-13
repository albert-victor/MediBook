"""Bookable time slots for doctors - prevents duplicate bookings."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import AvailabilityStatus


class DoctorAvailability(Base, TimestampMixin):
    __tablename__ = "doctor_availability"
    __table_args__ = (
        UniqueConstraint("doctor_id", "slot_start", name="uq_doctor_availability_slot"),
        Index("ix_doctor_availability_doctor_id", "doctor_id"),
        Index("ix_doctor_availability_slot_start", "slot_start"),
        Index("ix_doctor_availability_status", "status"),
        Index("ix_doctor_availability_doctor_date", "doctor_id", "slot_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
    )
    slot_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    slot_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=AvailabilityStatus.AVAILABLE.value,
        nullable=False,
    )

    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="availability_slots")
    appointment: Mapped["Appointment | None"] = relationship(
        "Appointment",
        back_populates="availability_slot",
        uselist=False,
    )

    @property
    def is_available(self) -> bool:
        return self.status == AvailabilityStatus.AVAILABLE.value

    def __repr__(self) -> str:
        return f"<DoctorAvailability doctor_id={self.doctor_id} start={self.slot_start}>"
