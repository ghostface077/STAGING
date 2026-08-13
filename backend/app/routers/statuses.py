"""Gestion des statuts de tickets (réservée à l'administrateur)."""
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.status import Status
from app.models.user import User
from app.schemas.common import Message
from app.schemas.status import StatusCreate, StatusOut, StatusUpdate

router = APIRouter(prefix="/api/statuses", tags=["Statuts"])


@router.get("", response_model=list[StatusOut])
def list_statuses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Accessible à tout utilisateur connecté : nécessaire pour les filtres de recherche des tickets."""
    return db.query(Status).order_by(Status.id).all()


@router.post("", response_model=StatusOut, status_code=http_status.HTTP_201_CREATED)
def create_status(payload: StatusCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    new_status = Status(**payload.model_dump())
    db.add(new_status)
    db.commit()
    db.refresh(new_status)
    return new_status


@router.put("/{status_id}", response_model=StatusOut)
def update_status(
    status_id: int, payload: StatusUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    db_status = db.get(Status, status_id)
    if db_status is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Statut introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(db_status, field, value)
    db.commit()
    db.refresh(db_status)
    return db_status


@router.delete("/{status_id}", response_model=Message)
def delete_status(status_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    db_status = db.get(Status, status_id)
    if db_status is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Statut introuvable.")
    if db_status.tickets:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Des tickets utilisent encore ce statut.")
    db.delete(db_status)
    db.commit()
    return Message(message="Statut supprimé avec succès.")
