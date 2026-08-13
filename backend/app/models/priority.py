from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Niveaux de priorité utilisés pour trier et calculer les SLA
PRIORITY_BASSE = "Basse"
PRIORITY_NORMALE = "Normale"
PRIORITY_HAUTE = "Haute"
PRIORITY_CRITIQUE = "Critique"


class Priority(Base):
    """Priorité d'un ticket (Basse, Normale, Haute, Critique)."""

    __tablename__ = "priorities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = plus basse, 4 = plus critique
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="priority")
    slas: Mapped[list["SLA"]] = relationship("SLA", back_populates="priority")
