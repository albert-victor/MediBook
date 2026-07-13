"""Password reset token ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class PasswordResetToken(Base, TimestampMixin):
  __tablename__ = "password_reset_tokens"

  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  token: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
  expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
  used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

  user: Mapped["User"] = relationship("User", back_populates="password_resets")

  @property
  def is_valid(self) -> bool:
      from app.utils.helpers import utcnow

      return self.used_at is None and self.expires_at > utcnow()
