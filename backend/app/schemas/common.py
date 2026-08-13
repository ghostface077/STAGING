"""Schémas génériques réutilisés dans plusieurs endpoints."""
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class Message(BaseModel):
    """Réponse simple contenant un message pour le frontend (succès ou information)."""

    message: str


class Page(BaseModel, Generic[T]):
    """Enveloppe de pagination générique (correctif #07)."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, page: int, page_size: int) -> "Page[T]":
        pages = max(1, -(-total // page_size)) if page_size else 1
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class PaginationParams:
    """Dépendance FastAPI partagée pour les paramètres `page`/`page_size`, avec les
    mêmes bornes sur tous les endpoints paginés (page ≥ 1, 1 ≤ page_size ≤ 100)."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Numéro de page (1-indexé)."),
        page_size: int = Query(
            default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Nombre d'éléments par page."
        ),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
