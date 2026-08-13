from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SLA(Base):
    """Accord de niveau de service : délais de première réponse et de résolution par priorité."""

    __tablename__ = "slas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    priority_id: Mapped[int] = mapped_column(ForeignKey("priorities.id", ondelete="CASCADE"), nullable=False)
    first_response_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    priority: Mapped["Priority"] = relationship("Priority", back_populates="slas")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="sla")
