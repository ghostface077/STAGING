from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Statuts du cycle de vie d'un ticket
STATUS_NOUVEAU = "Nouveau"
STATUS_OUVERT = "Ouvert"
STATUS_EN_COURS = "En cours"
STATUS_EN_ATTENTE = "En attente"
STATUS_RESOLU = "Résolu"
STATUS_FERME = "Fermé"
STATUS_REOUVERT = "Réouvert"
STATUS_ANNULE = "Annulé"

# Statuts considérés comme "clos" (ne comptent plus dans les tickets actifs)
CLOSED_STATUSES = {STATUS_FERME, STATUS_ANNULE}


class Status(Base):
    """Statut d'un ticket (Nouveau, Ouvert, En cours, En attente, Résolu, Fermé, Réouvert, Annulé)."""

    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="status")
