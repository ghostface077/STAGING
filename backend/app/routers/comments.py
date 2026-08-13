"""
API des commentaires de ticket. Les notes internes ne sont visibles que par le
personnel support (Technicien, Responsable IT, Administrateur).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models.comment import Comment
from app.models.role import ROLE_ADMINISTRATEUR, ROLE_RESPONSABLE_IT, ROLE_TECHNICIEN
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentOut, CommentUpdate
from app.schemas.common import Message
from app.services.history_service import log_ticket_action
from app.services.notification_service import notify_ticket_participants

router = APIRouter(tags=["Commentaires"])

STAFF_ROLES = {ROLE_TECHNICIEN, ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR}


def _get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket introuvable.")
    return ticket


def _can_access_ticket(ticket: Ticket, user: User) -> bool:
    if user.role.name in STAFF_ROLES:
        return True
    return ticket.requester_id == user.id


@router.get("/api/tickets/{ticket_id}/comments", response_model=list[CommentOut])
def list_comments(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = _get_ticket_or_404(db, ticket_id)
    if not _can_access_ticket(ticket, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à ce ticket.")

    query = db.query(Comment).options(joinedload(Comment.user), joinedload(Comment.attachments)).filter(
        Comment.ticket_id == ticket_id
    )
    if current_user.role.name not in STAFF_ROLES:
        query = query.filter(Comment.is_internal.is_(False))
    return query.order_by(Comment.created_at).all()


@router.post("/api/tickets/{ticket_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    ticket_id: int, payload: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    ticket = _get_ticket_or_404(db, ticket_id)
    if not _can_access_ticket(ticket, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à ce ticket.")

    is_internal = payload.is_internal and current_user.role.name in STAFF_ROLES

    comment = Comment(ticket_id=ticket_id, user_id=current_user.id, content=payload.content, is_internal=is_internal)
    db.add(comment)
    db.flush()

    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="commentaire", new_value="Note interne" if is_internal else "Commentaire public")

    if not is_internal:
        notify_ticket_participants(
            db, ticket=ticket, title="Nouveau commentaire",
            message=f"Un nouveau commentaire a été ajouté au ticket {ticket.reference}.",
            type="nouveau_commentaire", exclude_user_id=current_user.id,
        )

    db.commit()
    db.refresh(comment)
    return comment


@router.put("/api/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int, payload: CommentUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commentaire introuvable.")
    if comment.user_id != current_user.id and current_user.role.name != ROLE_ADMINISTRATEUR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez modifier que vos propres commentaires.")

    comment.content = payload.content
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/api/comments/{comment_id}", response_model=Message)
def delete_comment(comment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commentaire introuvable.")
    if comment.user_id != current_user.id and current_user.role.name != ROLE_ADMINISTRATEUR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez supprimer que vos propres commentaires.")

    db.delete(comment)
    db.commit()
    return Message(message="Commentaire supprimé avec succès.")
