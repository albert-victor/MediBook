"""Simulated payment records - one payment per appointment."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import PaymentMethod, PaymentStatus


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("appointment_id", name="uq_payments_appointment"),
        UniqueConstraint("reference_number", name="uq_payments_reference"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_method", "payment_method"),
        Index("ix_payments_paid_at", "paid_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TZS", nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(30),
        default=PaymentMethod.MPESA.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=PaymentStatus.PENDING.value,
        nullable=False,
    )
    reference_number: Mapped[str] = mapped_column(String(64), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    appointment: Mapped["Appointment"] = relationship("Appointment", back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} ref={self.reference_number} status={self.status}>"
