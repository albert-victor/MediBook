"""Patient reviews for doctor profiles."""

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class DoctorReview(Base, TimestampMixin):
    __tablename__ = "doctor_reviews"
    __table_args__ = (
        Index("ix_doctor_reviews_doctor_id", "doctor_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_name: Mapped[str] = mapped_column(String(120), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)

    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<DoctorReview doctor_id={self.doctor_id} rating={self.rating}>"
