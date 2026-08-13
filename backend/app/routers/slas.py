"""Gestion des SLA (accords de niveau de service)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_admin, require_staff
from app.models.sla import SLA
from app.models.user import User
from app.schemas.common import Message
from app.schemas.sla import SLACreate, SLAOut, SLAUpdate

router = APIRouter(prefix="/api/slas", tags=["SLA"])


@router.get("", response_model=list[SLAOut])
def list_slas(current_user: User = Depends(require_staff), db: Session = Depends(get_db)):
    return db.query(SLA).options(joinedload(SLA.priority)).order_by(SLA.id).all()


@router.post("", response_model=SLAOut, status_code=status.HTTP_201_CREATED)
def create_sla(payload: SLACreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    sla = SLA(**payload.model_dump())
    db.add(sla)
    db.commit()
    db.refresh(sla)
    return sla


@router.put("/{sla_id}", response_model=SLAOut)
def update_sla(sla_id: int, payload: SLAUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    sla = db.get(SLA, sla_id)
    if sla is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sla, field, value)
    db.commit()
    db.refresh(sla)
    return sla


@router.delete("/{sla_id}", response_model=Message)
def delete_sla(sla_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    sla = db.get(SLA, sla_id)
    if sla is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLA introuvable.")
    db.delete(sla)
    db.commit()
    return Message(message="SLA supprimé avec succès.")
