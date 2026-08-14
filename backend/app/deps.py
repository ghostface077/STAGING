"""
Dépendances FastAPI communes : utilisateur courant, contrôle des rôles (RBAC).
"""
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.role import (
    ROLE_ADMINISTRATEUR,
    ROLE_RESPONSABLE_IT,
    ROLE_TECHNICIEN,
    ROLE_UTILISATEUR,
)
from app.models.user import User
from app.security import ACCESS_TOKEN_COOKIE, decode_token

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Impossible de vérifier vos identifiants. Veuillez vous reconnecter.",
)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Récupère l'utilisateur actuellement authentifié à partir du cookie
    httpOnly `access_token` (correctif #12) — auparavant l'en-tête
    `Authorization`, dont le jeton était lu depuis le localStorage du
    navigateur, accessible à tout script JavaScript exécuté sur la page."""
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if token is None:
        raise CREDENTIALS_EXCEPTION

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise CREDENTIALS_EXCEPTION

    user_id = payload.get("sub")
    if user_id is None:
        raise CREDENTIALS_EXCEPTION

    user = db.get(User, int(user_id))
    if user is None:
        raise CREDENTIALS_EXCEPTION
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Votre compte a été désactivé. Contactez un administrateur.",
        )
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def require_roles(*allowed_roles: str):
    """Fabrique une dépendance qui n'autorise que les rôles listés."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les permissions nécessaires pour effectuer cette action.",
            )
        return current_user

    return dependency


# Raccourcis courants pour les rôles autorisés à gérer le support et l'administration
require_staff = require_roles(ROLE_TECHNICIEN, ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR)
require_manager = require_roles(ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR)
require_admin = require_roles(ROLE_ADMINISTRATEUR)
require_any_role = require_roles(ROLE_UTILISATEUR, ROLE_TECHNICIEN, ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR)

# Règle métier : seul un Utilisateur (demandeur) peut créer un nouveau ticket.
# Techniciens, Responsables IT et Administrateurs traitent/supervisent des tickets déjà créés,
# mais n'en sont jamais eux-mêmes à l'origine dans le fonctionnement normal de l'application.
require_user_role = require_roles(ROLE_UTILISATEUR)
