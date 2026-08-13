"""API des évaluations de satisfaction laissées par les demandeurs après résolution."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.satisfaction_rating import SatisfactionRating
from app.models.status import STATUS_FERME, STATUS_RESOLU
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.satisfaction import SatisfactionCreate, SatisfactionOut

router = APIRouter(prefix="/api/tickets/{ticket_id}/satisfaction", tags=["Satisfaction"])


@router.get("", response_model=SatisfactionOut | None)
def get_satisfaction(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SatisfactionRating).filter(SatisfactionRating.ticket_id == ticket_id).first()


@router.post("", response_model=SatisfactionOut, status_code=status.HTTP_201_CREATED)
def create_satisfaction(
    ticket_id: int, payload: SatisfactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Le demandeur évalue le support une fois son ticket résolu ou fermé."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket introuvable.")
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
