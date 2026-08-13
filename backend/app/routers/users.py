"""Gestion des utilisateurs (réservée aux Responsables IT et Administrateurs)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user, require_manager
from app.models.role import Role
from app.models.user import User
from app.schemas.common import Message, Page, PaginationParams
from app.schemas.user import ChangePassword, SelfProfileUpdate, UserCreate, UserOut, UserUpdate
from app.security import hash_password, verify_password
from app.services.history_service import log_audit

router = APIRouter(prefix="/api/users", tags=["Utilisateurs"])


def _base_query(db: Session):
    return db.query(User).options(joinedload(User.role), joinedload(User.department))


def _apply_user_filters(query, *, role: str | None, department_id: int | None, search: str | None):
    if role:
        query = query.join(Role).filter(Role.name == role)
    if department_id:
        query = query.filter(User.department_id == department_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.first_name.ilike(like)) | (User.last_name.ilike(like)) | (User.email.ilike(like))
        )
    return query


@router.get("", response_model=Page[UserOut])
def list_users(
    role: str | None = None,
    department_id: int | None = None,
    search: str | None = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    """Liste paginée des utilisateurs, avec filtres optionnels par rôle, service ou recherche texte."""
    filters = dict(role=role, department_id=department_id, search=search)

    total = _apply_user_filters(db.query(func.count(User.id)), **filters).scalar()
    users = (
        _apply_user_filters(_base_query(db), **filters)
        .order_by(User.last_name)
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )
    return Page.build(items=users, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    user = _base_query(db).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    return user


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    """Crée un utilisateur. La gestion des rôles administrateur reste réservée à l'administrateur."""
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette adresse e-mail est déjà utilisée.")

    role = db.get(Role, payload.role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rôle invalide.")
    if role.name == "Administrateur" and current_user.role.name != "Administrateur":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul un administrateur peut créer un compte administrateur.",
        )

    user = User(
        role_id=payload.role_id,
        department_id=payload.department_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        is_active=payload.is_active,
    )
    db.add(user)
    db.flush()
    log_audit(db, user_id=current_user.id, action="creation_utilisateur", entity_type="user", entity_id=user.id)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int, payload: UserUpdate, current_user: User = Depends(require_manager), db: Session = Depends(get_db)
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"]:
        data["email"] = data["email"].lower()
        existing = db.query(User).filter(User.email == data["email"], User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette adresse e-mail est déjà utilisée.")
    if "password" in data and data["password"]:
        user.password_hash = hash_password(data.pop("password"))
    else:
        data.pop("password", None)

    for field, value in data.items():
        setattr(user, field, value)

    log_audit(db, user_id=current_user.id, action="modification_utilisateur", entity_type="user", entity_id=user.id)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=Message)
def delete_user(user_id: int, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez pas supprimer votre propre compte.")

    # Désactivation plutôt que suppression physique, pour préserver l'intégrité de l'historique des tickets
    user.is_active = False
    log_audit(db, user_id=current_user.id, action="desactivation_utilisateur", entity_type="user", entity_id=user.id)
    db.commit()
    return Message(message="Utilisateur désactivé avec succès.")


@router.put("/moi/profil", response_model=UserOut)
def update_my_profile(payload: SelfProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Permet à l'utilisateur connecté de modifier ses propres informations personnelles (prénom, nom, téléphone)."""
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value)

    log_audit(db, user_id=current_user.id, action="modification_profil", entity_type="user", entity_id=current_user.id)
    db.commit()
    db.refresh(current_user)
    return _base_query(db).filter(User.id == current_user.id).first()


@router.put("/moi/mot-de-passe", response_model=Message)
def change_my_password(payload: ChangePassword, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Permet à l'utilisateur connecté de changer son propre mot de passe."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le mot de passe actuel est incorrect.")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return Message(message="Mot de passe mis à jour avec succès.")
