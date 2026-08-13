"""Enregistrement de l'historique des tickets et du journal d'audit global."""
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory


def log_ticket_action(
    db: Session,
    *,
    ticket: Ticket,
    user_id: int | None,
    action: str,
    old_value: str | None = None,
    new_value: str | None = None,
) -> None:
    """Ajoute une entrée à l'historique du ticket."""
    db.add(
        TicketHistory(
            ticket_id=ticket.id,
            user_id=user_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )
    )


def log_audit(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    ip_address: str | None = None,
) -> None:
    """Ajoute une entrée au journal d'audit global (consultable par l'administrateur)."""
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
        )
    )
