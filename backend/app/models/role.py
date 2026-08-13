from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Noms de rôles disponibles dans l'application (voir app/seed.py)
ROLE_UTILISATEUR = "Utilisateur"
ROLE_TECHNICIEN = "Technicien"
ROLE_RESPONSABLE_IT = "Responsable IT"
ROLE_ADMINISTRATEUR = "Administrateur"


class Role(Base):
    """Rôle applicatif (Utilisateur, Technicien, Responsable IT, Administrateur)."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users: Mapped[list["User"]] = relationship("User", back_populates="role")
