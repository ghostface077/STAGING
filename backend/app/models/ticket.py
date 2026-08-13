from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Ticket(Base):
    """Ticket d'incident ou de demande informatique : cœur de l'application."""

    __tablename__ = "tickets"
    __table_args__ = (
        # Cas combiné le plus fréquent : liste filtrée par statut, triée par date (correctif #08).
        Index("ix_tickets_status_created_at", "status_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)  # TCK-2026-00001
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    technician_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    priority_id: Mapped[int] = mapped_column(ForeignKey("priorities.id", ondelete="RESTRICT"), nullable=False, index=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id", ondelete="RESTRICT"), nullable=False, index=True)
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True)
    sla_id: Mapped[int | None] = mapped_column(ForeignKey("slas.id", ondelete="SET NULL"), nullable=True)

    solution: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id], back_populates="tickets_created")
    technician: Mapped["User | None"] = relationship("User", foreign_keys=[technician_id], back_populates="tickets_assigned")
    team: Mapped["Team | None"] = relationship("Team", back_populates="tickets")
    category: Mapped["Category"] = relationship("Category", back_populates="tickets")
    priority: Mapped["Priority"] = relationship("Priority", back_populates="tickets")
    status: Mapped["Status"] = relationship("Status", back_populates="tickets")
    equipment: Mapped["Equipment | None"] = relationship("Equipment", back_populates="tickets")
    sla: Mapped["SLA | None"] = relationship("SLA", back_populates="tickets")

    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="ticket", cascade="all, delete-orphan", order_by="Comment.created_at"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="ticket", cascade="all, delete-orphan"
    )
    history: Mapped[list["TicketHistory"]] = relationship(
        "TicketHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketHistory.created_at"
    )
    satisfaction_rating: Mapped["SatisfactionRating | None"] = relationship(
        "SatisfactionRating", back_populates="ticket", uselist=False, cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="ticket")
