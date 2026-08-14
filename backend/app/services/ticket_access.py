"""Règles de visibilité et d'accès à un ticket, partagées entre les routers qui
exposent des sous-ressources d'un ticket (commentaires, pièces jointes,
satisfaction), pour éviter de dupliquer cette logique (source de l'IDOR
corrigé au correctif #03)."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.role import ROLE_ADMINISTRATEUR, ROLE_RESPONSABLE_IT, ROLE_TECHNICIEN
from app.models.ticket import Ticket
from app.models.user import User


def can_view_ticket(ticket: Ticket, user: User) -> bool:
    role = user.role.name
    if role in (ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR):
        return True
    if role == ROLE_TECHNICIEN:
        return ticket.technician_id == user.id or ticket.technician_id is None
    return ticket.requester_id == user.id


def get_active_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    """Récupère un ticket non supprimé, ou lève 404 — y compris si le ticket
    existe mais a été supprimé logiquement (correctif #09) : un ticket
    supprimé doit être invisible via toutes les sous-ressources (commentaires,
    pièces jointes, satisfaction), pas seulement via /api/tickets."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket introuvable.")
    return ticket
