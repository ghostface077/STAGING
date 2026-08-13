"""Authentification : connexion, inscription, utilisateur courant, déconnexion."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.role import ROLE_UTILISATEUR, Role
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.common import Message
from app.schemas.user import UserOut
from app.security import create_access_token, hash_password, verify_password
from app.services.history_service import log_audit

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authentifie un utilisateur par e-mail / mot de passe et retourne un token JWT."""
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou mot de passe incorrect.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte a été désactivé. Contactez un administrateur.",
        )

    token = create_access_token(subject=user.id, extra_claims={"role": user.role.name})
    log_audit(
        db,
        user_id=user.id,
        action="connexion",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Crée un nouveau compte avec le rôle « Utilisateur » (auto-inscription)."""
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte existe déjà avec cette adresse e-mail.",
        )

    role = db.query(Role).filter(Role.name == ROLE_UTILISATEUR).first()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Le rôle par défaut est introuvable. Contactez un administrateur.",
        )

    user = User(
        role_id=role.id,
        department_id=payload.department_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, extra_claims={"role": user.role.name})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Retourne les informations de l'utilisateur actuellement connecté."""
    return current_user


@router.post("/logout", response_model=Message)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Déconnexion côté serveur : journalise l'action. Le token JWT étant sans état,
    la suppression effective se fait côté client (suppression du token stocké).
    """
    log_audit(db, user_id=current_user.id, action="deconnexion", entity_type="user", entity_id=current_user.id)
    db.commit()
    return Message(message="Déconnexion réussie.")
