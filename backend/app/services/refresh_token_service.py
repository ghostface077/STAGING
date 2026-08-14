"""Gestion des sessions de rafraîchissement (correctif #12) : émission et
révocation des refresh tokens. Centralisé ici pour être réutilisé par
`routers/auth.py` (connexion, rafraîchissement, déconnexion) et
`routers/users.py` (révocation sur changement de mot de passe / désactivation
de compte), sans dupliquer la logique entre ces deux routers."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.security import create_refresh_token


def issue_refresh_token(db: Session, *, user_id: int) -> str:
    """Émet un nouveau refresh token pour l'utilisateur et persiste la session
    correspondante (nécessaire pour pouvoir la révoquer plus tard)."""
    token, jti, expires_at = create_refresh_token(subject=user_id)
    db.add(RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at))
    return token


def get_active_refresh_token(db: Session, *, jti: str, user_id: int) -> RefreshToken | None:
    """Retrouve la session correspondant à `jti`, uniquement si elle appartient
    bien à `user_id`, n'est pas révoquée et n'est pas expirée côté serveur
    (double vérification, en plus de l'expiration portée par le JWT lui-même)."""
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.jti == jti,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )


def revoke_refresh_token(db: Session, *, jti: str) -> None:
    """Révoque une session précise (déconnexion, rotation)."""
    db.query(RefreshToken).filter(RefreshToken.jti == jti, RefreshToken.revoked_at.is_(None)).update(
        {"revoked_at": datetime.now(timezone.utc)}
    )


def revoke_all_refresh_tokens_for_user(db: Session, *, user_id: int) -> None:
    """Révoque toutes les sessions actives d'un utilisateur (changement de mot
    de passe, désactivation de compte par un administrateur) : referme tout
    accès existant, pas seulement les futures tentatives de connexion."""
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)).update(
        {"revoked_at": datetime.now(timezone.utc)}
    )
