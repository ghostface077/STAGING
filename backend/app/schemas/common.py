"""Schémas génériques réutilisés dans plusieurs endpoints."""
from pydantic import BaseModel


class Message(BaseModel):
    """Réponse simple contenant un message pour le frontend (succès ou information)."""

    message: str


class Page(BaseModel):
    """Enveloppe de pagination générique."""

    items: list
    total: int
    page: int
    page_size: int
    pages: int
