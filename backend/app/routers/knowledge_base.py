"""API de la base de connaissances."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user, require_staff
from app.models.knowledge_base import KB_STATUS_PUBLIE, KnowledgeBaseArticle
from app.models.role import ROLE_ADMINISTRATEUR, ROLE_RESPONSABLE_IT, ROLE_TECHNICIEN
from app.models.user import User
from app.schemas.common import Message
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseOut, KnowledgeBaseUpdate

router = APIRouter(prefix="/api/knowledge-base", tags=["Base de connaissances"])

STAFF_ROLES = {ROLE_TECHNICIEN, ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR}


def _base_query(db: Session):
    return db.query(KnowledgeBaseArticle).options(
        joinedload(KnowledgeBaseArticle.category), joinedload(KnowledgeBaseArticle.author)
    )


@router.get("", response_model=list[KnowledgeBaseOut])
def list_articles(
    category_id: int | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les articles publiés (le personnel support voit également les brouillons)."""
    query = _base_query(db)
    if current_user.role.name not in STAFF_ROLES:
        query = query.filter(KnowledgeBaseArticle.status == KB_STATUS_PUBLIE)
    if category_id:
        query = query.filter(KnowledgeBaseArticle.category_id == category_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (KnowledgeBaseArticle.title.ilike(like)) | (KnowledgeBaseArticle.content.ilike(like))
        )
    return query.order_by(KnowledgeBaseArticle.updated_at.desc()).all()


@router.get("/{article_id}", response_model=KnowledgeBaseOut)
def get_article(article_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    article = _base_query(db).filter(KnowledgeBaseArticle.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article introuvable.")
    if article.status != KB_STATUS_PUBLIE and current_user.role.name not in STAFF_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cet article n'est pas publié.")
    article.views += 1
    db.commit()
    db.refresh(article)
    return article


@router.post("", response_model=KnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
def create_article(payload: KnowledgeBaseCreate, current_user: User = Depends(require_staff), db: Session = Depends(get_db)):
    article = KnowledgeBaseArticle(author_id=current_user.id, **payload.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.put("/{article_id}", response_model=KnowledgeBaseOut)
def update_article(
    article_id: int, payload: KnowledgeBaseUpdate, current_user: User = Depends(require_staff), db: Session = Depends(get_db)
):
    article = db.get(KnowledgeBaseArticle, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(article, field, value)
    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}", response_model=Message)
def delete_article(article_id: int, current_user: User = Depends(require_staff), db: Session = Depends(get_db)):
    article = db.get(KnowledgeBaseArticle, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article introuvable.")
    db.delete(article)
    db.commit()
    return Message(message="Article supprimé avec succès.")
