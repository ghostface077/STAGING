"""Gestion du parc informatique (équipements)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user, require_manager
from app.models.equipment import Equipment
from app.models.role import ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR, ROLE_TECHNICIEN
from app.models.user import User
from app.schemas.common import Message
from app.schemas.equipment import EquipmentCreate, EquipmentOut, EquipmentUpdate
from app.schemas.ticket import TicketListItem

router = APIRouter(prefix="/api/equipment", tags=["Équipements"])

STAFF_ROLES = {ROLE_TECHNICIEN, ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR}


def _base_query(db: Session):
    return db.query(Equipment).options(joinedload(Equipment.user), joinedload(Equipment.department))


@router.get("", response_model=list[EquipmentOut])
def list_equipment(
    department_id: int | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Liste les équipements du parc, avec filtres optionnels.
    Le personnel support voit tout le parc ; un simple utilisateur ne voit que son propre matériel
    (nécessaire notamment pour sélectionner l'équipement concerné lors de la création d'un ticket).
    """
    query = _base_query(db)
    if current_user.role.name not in STAFF_ROLES:
        query = query.filter(Equipment.user_id == current_user.id)
    if department_id:
        query = query.filter(Equipment.department_id == department_id)
    if status_filter:
        query = query.filter(Equipment.status == status_filter)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Equipment.asset_number.ilike(like))
            | (Equipment.brand.ilike(like))
            | (Equipment.model.ilike(like))
            | (Equipment.serial_number.ilike(like))
        )
    return query.order_by(Equipment.asset_number).all()


def _can_view_equipment(equipment: Equipment, user: User) -> bool:
    return user.role.name in STAFF_ROLES or equipment.user_id == user.id


@router.get("/{equipment_id}", response_model=EquipmentOut)
def get_equipment(equipment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    equipment = _base_query(db).filter(Equipment.id == equipment_id).first()
    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipement introuvable.")
    if not _can_view_equipment(equipment, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à cet équipement.")
    return equipment


@router.get("/{equipment_id}/tickets", response_model=list[TicketListItem])
def get_equipment_tickets(equipment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retourne l'historique des tickets associés à cet équipement."""
    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipement introuvable.")
    if not _can_view_equipment(equipment, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à cet équipement.")
    return equipment.tickets


@router.post("", response_model=EquipmentOut, status_code=status.HTTP_201_CREATED)
def create_equipment(payload: EquipmentCreate, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    if db.query(Equipment).filter(Equipment.asset_number == payload.asset_number).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce numéro d'actif existe déjà.")
    equipment = Equipment(**payload.model_dump())
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.put("/{equipment_id}", response_model=EquipmentOut)
def update_equipment(
    equipment_id: int, payload: EquipmentUpdate, current_user: User = Depends(require_manager), db: Session = Depends(get_db)
):
    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipement introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(equipment, field, value)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.delete("/{equipment_id}", response_model=Message)
def delete_equipment(equipment_id: int, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipement introuvable.")
    db.delete(equipment)
    db.commit()
    return Message(message="Équipement supprimé avec succès.")
