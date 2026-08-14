"""
Fonctions de sécurité : hachage des mots de passe et gestion des tokens JWT.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Noms des cookies d'authentification (correctif #12) — partagés entre
# app/routers/auth.py (émission/révocation) et app/deps.py (lecture), pour
# éviter de dupliquer ces littéraux.
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"


def hash_password(password: str) -> str:
    """Hache un mot de passe en clair avec bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Génère un token JWT d'accès pour l'utilisateur identifié par `subject` (son id)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire, "type": "access"}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Génère un refresh token JWT (correctif #12). Retourne (jwt, jti, expires_at) :
    `jti` (identifiant unique du token) et `expires_at` sont destinés à être
    persistés côté serveur (voir app/models/refresh_token.py), ce qui permet de
    révoquer un refresh token — contrairement à un JWT seul, toujours valide
    jusqu'à expiration naturelle quoi qu'il arrive côté serveur."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire, "type": "refresh", "jti": jti}
    token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return token, jti, expire


def decode_token(token: str) -> dict[str, Any] | None:
    """Décode et valide un token JWT. Retourne None si le token est invalide ou expiré."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
