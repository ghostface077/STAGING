"""Gestion des rôles applicatifs (réservée à l'administrateur)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin, require_staff
from app.models.role import Role
from app.models.user import User
from app.schemas.common import Message
from app.schemas.role import RoleCreate, RoleOut, RoleUpdate

router = APIRouter(prefix="/api/roles", tags=["Rôles"])


@router.get("", response_model=list[RoleOut])
def list_roles(current_user: User = Depends(require_staff), db: Session = Depends(get_db)):
    """Liste les rôles disponibles (utile pour peupler les formulaires d'attribution)."""
    return db.query(Role).order_by(Role.id).all()


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(Role).filter(Role.name == payload.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce rôle existe déjà.")
    role = Role(**payload.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: int, payload: RoleUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}", response_model=Message)
def delete_role(role_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle introuvable.")
    if role.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer un rôle encore attribué à des utilisateurs.",
        )
    db.delete(role)
    db.commit()
    return Message(message="Rôle supprimé avec succès.")
