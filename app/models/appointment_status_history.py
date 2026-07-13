"""Audit trail for appointment status changes."""

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class AppointmentStatusHistory(Base, TimestampMixin):
    __tablename__ = "appointment_status_history"
    __table_args__ = (
        Index("ix_appointment_status_history_appointment_id", "appointment_id"),
        Index("ix_appointment_status_history_status", "status"),
        Index("ix_appointment_status_history_changed_by", "changed_by_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    appointment: Mapped["Appointment"] = relationship(
        "Appointment",
        back_populates="status_history",
    )
    changed_by: Mapped["User | None"] = relationship("User", back_populates="status_changes")

    def __repr__(self) -> str:
        return f"<AppointmentStatusHistory appointment_id={self.appointment_id} status={self.status}>"
