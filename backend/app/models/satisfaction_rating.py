from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SatisfactionRating(Base):
    """Évaluation de satisfaction laissée par le demandeur après résolution d'un ticket (note de 1 à 5)."""

    __tablename__ = "satisfaction_ratings"
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="ck_satisfaction_rating_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="satisfaction_rating")
    user: Mapped["User"] = relationship("User")
