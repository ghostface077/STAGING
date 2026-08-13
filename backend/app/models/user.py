from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Utilisateur de l'application (utilisateur final, technicien, responsable IT ou administrateur)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    department: Mapped["Department | None"] = relationship("Department", back_populates="users")

    tickets_created: Mapped[list["Ticket"]] = relationship(
        "Ticket", foreign_keys="Ticket.requester_id", back_populates="requester"
    )
    tickets_assigned: Mapped[list["Ticket"]] = relationship(
        "Ticket", foreign_keys="Ticket.technician_id", back_populates="technician"
    )
    teams: Mapped[list["Team"]] = relationship("Team", secondary="team_users", back_populates="members")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="user")
    equipment: Mapped[list["Equipment"]] = relationship("Equipment", back_populates="user")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
