"""Utilitaires de gestion sécurisée des pièces jointes envoyées par les utilisateurs."""
import os
import uuid

from fastapi import HTTPException, UploadFile, status

from app.config import settings

# Extensions et types MIME autorisés pour les pièces jointes
ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv",
    ".txt", ".log",
}
ALLOWED_MIME_TYPES = {
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "text/plain",
}


def _safe_filename(original_name: str) -> tuple[str, str]:
    """Retourne (nom_stocké_unique, extension) à partir du nom de fichier d'origine."""
    ext = os.path.splitext(original_name)[1].lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    return stored_name, ext


async def save_upload(file: UploadFile) -> dict:
    """
    Valide (extension, type MIME, taille) puis enregistre un fichier envoyé par un utilisateur.
    Retourne un dictionnaire prêt à être persisté dans la table `attachments`.
    """
    stored_name, ext = _safe_filename(file.filename or "fichier")

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le type de fichier '{ext}' n'est pas autorisé.",
        )
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le type MIME de ce fichier n'est pas autorisé.",
        )

    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le fichier dépasse la taille maximale autorisée ({settings.max_upload_size_mb} Mo).",
        )
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le fichier envoyé est vide.")

    os.makedirs(settings.upload_dir, exist_ok=True)
    destination_path = os.path.join(settings.upload_dir, stored_name)
    with open(destination_path, "wb") as buffer:
        buffer.write(content)

    return {
        "file_name": file.filename or stored_name,
        "file_path": destination_path,
        "file_type": file.content_type or "application/octet-stream",
        "file_size": len(content),
    }
