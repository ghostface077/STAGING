"""Politique de mot de passe (correctif #14), partagée entre tous les schémas
qui acceptent un mot de passe en clair (inscription, création de compte par
un manager, changement de mot de passe) — pour éviter de dupliquer la règle.

Longueur max fixée à 72 : bcrypt tronque silencieusement au-delà de 72 octets
(vérifié empiriquement — deux mots de passe ne différant qu'après le 72ᵉ
octet sont acceptés comme identiques), autoriser plus donnerait une fausse
impression de sécurité sur la partie du mot de passe au-delà de cette limite.
"""
import re
from typing import Annotated

from pydantic import AfterValidator, StringConstraints

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 72

_UPPER_RE = re.compile(r"[A-ZÀ-Ý]")
_LOWER_RE = re.compile(r"[a-zà-ÿ]")
_DIGIT_RE = re.compile(r"\d")
_SPECIAL_RE = re.compile(r"[^\w\s]", re.UNICODE)


def validate_password_complexity(password: str) -> str:
    """Exige au moins une majuscule, une minuscule, un chiffre et un caractère
    spécial, en plus de la longueur déjà contrainte par `StrongPassword`."""
    missing = []
    if not _UPPER_RE.search(password):
        missing.append("une majuscule")
    if not _LOWER_RE.search(password):
        missing.append("une minuscule")
    if not _DIGIT_RE.search(password):
        missing.append("un chiffre")
    if not _SPECIAL_RE.search(password):
        missing.append("un caractère spécial")

    if missing:
        raise ValueError("Le mot de passe doit contenir au moins " + ", ".join(missing) + ".")
    return password


StrongPassword = Annotated[
    str,
    StringConstraints(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
    AfterValidator(validate_password_complexity),
]
