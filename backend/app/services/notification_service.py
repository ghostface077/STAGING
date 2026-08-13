"""Création des notifications applicatives (cloche de notifications)."""
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.ticket import Ticket


def notify_user(db: Session, *, user_id: int, ticket: Ticket | None, title: str, message: str, type: str) -> None:
    """Crée une notification pour un utilisateur donné. Ne fait rien si user_id est None."""
    if user_id is None:
        return
    notification = Notification(
        user_id=user_id,
        ticket_id=ticket.id if ticket else None,
        title=title,
        message=message,
        type=type,
    )
    db.add(notification)


def notify_ticket_participants(
    db: Session, *, ticket: Ticket, title: str, message: str, type: str, exclude_user_id: int | None = None
) -> None:
    """Notifie le demandeur et le technicien assigné d'un ticket, en excluant éventuellement l'auteur de l'action."""
    recipients = {ticket.requester_id}
    if ticket.technician_id:
        recipients.add(ticket.technician_id)
    if exclude_user_id in recipients:
        recipients.discard(exclude_user_id)
    for user_id in recipients:
        notify_user(db, user_id=user_id, ticket=ticket, title=title, message=message, type=type)
