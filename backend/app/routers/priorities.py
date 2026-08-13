"""Gestion des priorités de tickets (réservée à l'administrateur)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.priority import Priority
from app.models.user import User
from app.schemas.common import Message
from app.schemas.priority import PriorityCreate, PriorityOut, PriorityUpdate

router = APIRouter(prefix="/api/priorities", tags=["Priorités"])


@router.get("", response_model=list[PriorityOut])
def list_priorities(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Accessible à tout utilisateur connecté : nécessaire pour le formulaire de création de ticket."""
    return db.query(Priority).order_by(Priority.level).all()


@router.post("", response_model=PriorityOut, status_code=status.HTTP_201_CREATED)
def create_priority(payload: PriorityCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    priority = Priority(**payload.model_dump())
    db.add(priority)
    db.commit()
    db.refresh(priority)
    return priority


@router.put("/{priority_id}", response_model=PriorityOut)
def update_priority(
    priority_id: int, payload: PriorityUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    priority = db.get(Priority, priority_id)
    if priority is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Priorité introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(priority, field, value)
    db.commit()
    db.refresh(priority)
    return priority


@router.delete("/{priority_id}", response_model=Message)
def delete_priority(priority_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    priority = db.get(Priority, priority_id)
    if priority is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Priorité introuvable.")
    if priority.tickets:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Des tickets utilisent encore cette priorité.")
    db.delete(priority)
    db.commit()
    return Message(message="Priorité supprimée avec succès.")
