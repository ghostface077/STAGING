from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Statuts possibles d'un équipement du parc informatique
EQUIPMENT_STATUS_EN_SERVICE = "En service"
EQUIPMENT_STATUS_EN_MAINTENANCE = "En maintenance"
EQUIPMENT_STATUS_HORS_SERVICE = "Hors service"
EQUIPMENT_STATUS_STOCK = "En stock"


class Equipment(Base):
    """Élément du parc informatique (poste, imprimante, téléphone, etc.)."""

    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)  # ex: Ordinateur portable, Imprimante
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(150), unique=True, nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    operating_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    warranty_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=EQUIPMENT_STATUS_EN_SERVICE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User | None"] = relationship("User", back_populates="equipment")
    department: Mapped["Department | None"] = relationship("Department", back_populates="equipment")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="equipment")
