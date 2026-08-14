"""API des évaluations de satisfaction laissées par les demandeurs après résolution."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.satisfaction_rating import SatisfactionRating
from app.models.status import STATUS_FERME, STATUS_RESOLU
from app.models.user import User
# Réutilisation de la règle de visibilité déjà appliquée sur GET /api/tickets/{id}
# (Utilisateur -> ses tickets, Technicien -> ses tickets assignés/non-assignés,
# Responsable IT/Administrateur -> tout) : on évite de dupliquer cette logique
# d'autorisation, source de l'IDOR corrigé ici (correctif #03 de l'audit).
from app.routers.tickets import _can_view_ticket
from app.schemas.satisfaction import SatisfactionCreate, SatisfactionOut
from app.services.ticket_access import get_active_ticket_or_404 as _get_ticket_or_404

router = APIRouter(prefix="/api/tickets/{ticket_id}/satisfaction", tags=["Satisfaction"])


@router.get("", response_model=SatisfactionOut | None)
def get_satisfaction(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Consulte l'évaluation de satisfaction d'un ticket. Réservé aux personnes
    autorisées à consulter le ticket lui-même (voir _can_view_ticket) : le
    demandeur, le technicien assigné (ou tout technicien si non assigné), et
    le staff d'encadrement (Responsable IT / Administrateur)."""
    ticket = _get_ticket_or_404(db, ticket_id)
    if not _can_view_ticket(ticket, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à ce ticket.")
    return db.query(SatisfactionRating).filter(SatisfactionRating.ticket_id == ticket_id).first()


@router.post("", response_model=SatisfactionOut, status_code=status.HTTP_201_CREATED)
def create_satisfaction(
    ticket_id: int, payload: SatisfactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Le demandeur évalue le support une fois son ticket résolu ou fermé."""
    ticket = _get_ticket_or_404(db, ticket_id)
    if ticket.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul le demandeur peut évaluer ce ticket.")
    if ticket.status.name not in {STATUS_RESOLU, STATUS_FERME}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le ticket doit être résolu ou fermé avant d'être évalué.")

    existing = db.query(SatisfactionRating).filter(SatisfactionRating.ticket_id == ticket_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce ticket a déjà été évalué.")

    rating = SatisfactionRating(ticket_id=ticket_id, user_id=current_user.id, rating=payload.rating, comment=payload.comment)
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating
