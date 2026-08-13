"""Envoi et téléchargement sécurisés des pièces jointes liées aux tickets."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.attachment import Attachment
from app.models.role import ROLE_ADMINISTRATEUR, ROLE_RESPONSABLE_IT, ROLE_TECHNICIEN
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.comment import AttachmentOut
from app.schemas.common import Message
from app.services.history_service import log_ticket_action
from app.utils.files import save_upload

router = APIRouter(tags=["Pièces jointes"])

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


@router.post("/api/tickets/{ticket_id}/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    ticket_id: int,
    file: UploadFile,
    comment_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Téléverse une pièce jointe (image, PDF, document, fichier de log) sur un ticket."""
    ticket = _get_ticket_or_404(db, ticket_id)
    if not _can_access_ticket(ticket, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à ce ticket.")

    saved = await save_upload(file)
    attachment = Attachment(
        ticket_id=ticket_id,
        comment_id=comment_id,
        user_id=current_user.id,
        **saved,
    )
    db.add(attachment)
    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="ajout_piece_jointe", new_value=saved["file_name"])
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/api/attachments/{attachment_id}/download")
def download_attachment(attachment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Télécharge une pièce jointe si l'utilisateur a accès au ticket associé."""
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pièce jointe introuvable.")

    ticket = db.get(Ticket, attachment.ticket_id)
    if ticket is None or not _can_access_ticket(ticket, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à cette pièce jointe.")

    return FileResponse(path=attachment.file_path, filename=attachment.file_name, media_type=attachment.file_type)


@router.delete("/api/attachments/{attachment_id}", response_model=Message)
def delete_attachment(attachment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    attachment = db.get(Attachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pièce jointe introuvable.")
    if attachment.user_id != current_user.id and current_user.role.name != ROLE_ADMINISTRATEUR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez supprimer que vos propres pièces jointes.")

    db.delete(attachment)
    db.commit()
    return Message(message="Pièce jointe supprimée avec succès.")
