"""Gestion des catégories et sous-catégories de tickets (réservée à l'administrateur)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.common import Message

router = APIRouter(prefix="/api/categories", tags=["Catégories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retourne les catégories racines avec leurs sous-catégories imbriquées.
    Accessible à tout utilisateur connecté : nécessaire pour le formulaire de création de ticket.
    """
    return db.query(Category).filter(Category.parent_id.is_(None)).order_by(Category.name).all()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int, payload: CategoryUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catégorie introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", response_model=Message)
def delete_category(category_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catégorie introuvable.")
    if category.children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Supprimez d'abord les sous-catégories associées."
        )
    db.delete(category)
    db.commit()
    return Message(message="Catégorie supprimée avec succès.")
