"""Patient appointments with doctors."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import AppointmentStatus


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("doctor_id", "scheduled_start", name="uq_appointment_doctor_slot"),
        UniqueConstraint("availability_id", name="uq_appointment_availability"),
        Index("ix_appointments_patient_id", "patient_id"),
        Index("ix_appointments_doctor_id", "doctor_id"),
        Index("ix_appointments_status", "status"),
        Index("ix_appointments_scheduled_start", "scheduled_start"),
        Index("ix_appointments_patient_status", "patient_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    availability_id: Mapped[int | None] = mapped_column(
        ForeignKey("doctor_availability.id", ondelete="SET NULL"),
        nullable=True,
    )
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=AppointmentStatus.PENDING.value,
        nullable=False,
    )
    patient_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    patient: Mapped["User"] = relationship("User", back_populates="patient_appointments")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="appointments")
    availability_slot: Mapped["DoctorAvailability | None"] = relationship(
        "DoctorAvailability",
        back_populates="appointment",
    )
    status_history: Mapped[list["AppointmentStatusHistory"]] = relationship(
        "AppointmentStatusHistory",
        back_populates="appointment",
        cascade="all, delete-orphan",
        order_by="AppointmentStatusHistory.created_at",
    )
    payment: Mapped["Payment | None"] = relationship(
        "Payment",
        back_populates="appointment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="appointment",
    )

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} status={self.status}>"
