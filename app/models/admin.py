"""Admin profile - extends User with administrative metadata."""

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Admin(Base, TimestampMixin):
    __tablename__ = "admins"
    __table_args__ = (
        Index("ix_admins_department", "department"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(100), nullable=False, default="Operations")
    job_title: Mapped[str] = mapped_column(String(100), nullable=False, default="Administrator")
    created_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="admin_profile")
    created_by: Mapped["Admin | None"] = relationship(
        "Admin",
        remote_side="Admin.id",
        back_populates="created_admins",
    )
    created_admins: Mapped[list["Admin"]] = relationship(
        "Admin",
        back_populates="created_by",
    )

    def __repr__(self) -> str:
        return f"<Admin id={self.id} user_id={self.user_id}>"
