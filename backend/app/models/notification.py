from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Types de notifications émises par le système
NOTIF_CREATION = "creation_ticket"
NOTIF_ATTRIBUTION = "attribution"
NOTIF_COMMENTAIRE = "nouveau_commentaire"
NOTIF_STATUT = "changement_statut"
NOTIF_PRIORITE = "changement_priorite"
NOTIF_RESOLUTION = "resolution"
NOTIF_FERMETURE = "fermeture"
NOTIF_REOUVERTURE = "reouverture"
NOTIF_SLA_BIENTOT_DEPASSE = "sla_bientot_depasse"
NOTIF_SLA_DEPASSE = "sla_depasse"


class Notification(Base):
    """Notification adressée à un utilisateur (cloche de notifications)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")
    ticket: Mapped["Ticket | None"] = relationship("Ticket", back_populates="notifications")
