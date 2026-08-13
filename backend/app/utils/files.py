"""Utilitaires de gestion sécurisée des pièces jointes envoyées par les utilisateurs.

La validation ne fait confiance à aucune donnée déclarée par le client
(extension du nom de fichier, Content-Type, taille annoncée) : le contenu
binaire réel est inspecté (signature / magic bytes) pour les formats qui en
possèdent une, et le nom physique du fichier n'est jamais dérivé du nom fourni
par l'utilisateur (correctif #05 — validation des pièces jointes).
"""
import os
import re
import uuid

import filetype
from fastapi import HTTPException, UploadFile, status

from app.config import settings

# MIME type(s) attendu(s) pour chaque extension autorisée. Utilisé à la fois
# pour valider le Content-Type déclaré par le client ET, quand c'est possible,
# la signature binaire réellement détectée dans le fichier — les deux doivent
# être cohérents avec l'extension annoncée.
EXTENSION_MIME_TYPES: dict[str, set[str]] = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".gif": {"image/gif"},
    ".webp": {"image/webp"},
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".xls": {"application/vnd.ms-excel"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".csv": {"text/csv"},
    ".txt": {"text/plain"},
    ".log": {"text/plain"},
}
ALLOWED_EXTENSIONS = set(EXTENSION_MIME_TYPES.keys())
ALLOWED_MIME_TYPES = set().union(*EXTENSION_MIME_TYPES.values())

# MIME générique que certains clients (scripts, anciens navigateurs) envoient
# quand ils ne savent pas déterminer le type exact du fichier sélectionné. On
# l'accepte comme déclaration, mais la décision finale revient toujours à la
# vérification du contenu réel (signature binaire ou heuristique texte).
GENERIC_MIME_TYPE = "application/octet-stream"

# Extensions dont le format possède une signature binaire (magic bytes)
# vérifiable par la bibliothèque `filetype`.
BINARY_VERIFIABLE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".doc", ".docx", ".xls", ".xlsx"}
# Extensions texte : aucune signature binaire fiable n'existe pour ces formats ;
# elles sont validées par une heuristique "ressemble à du texte" (voir plus bas).
TEXT_EXTENSIONS = {".csv", ".txt", ".log"}

CHUNK_SIZE = 1024 * 1024  # 1 Mo — taille de bloc pour la lecture en flux
MAX_FILENAME_LENGTH = 255  # aligné sur la colonne `attachments.file_name` (String(255))
MAX_STORED_NAME_ATTEMPTS = 5  # tentatives de génération d'un nom physique unique

_FILENAME_UNSAFE_CHARS = re.compile(r"[\x00-\x1f\x7f/\\]")  # caractères de contrôle + séparateurs de chemin


def _extract_extension(original_name: str) -> str:
    return os.path.splitext(original_name)[1].lower()


def _sanitize_display_filename(original_name: str) -> str:
    """Nettoie le nom de fichier d'origine avant de le conserver en base comme
    simple métadonnée d'affichage : jamais utilisé pour construire un chemin
    physique, mais assaini quand même par défense en profondeur (caractères
    de contrôle, séparateurs de répertoire, longueur)."""
    name = os.path.basename((original_name or "fichier").strip())
    name = _FILENAME_UNSAFE_CHARS.sub("_", name).strip()
    return (name or "fichier")[:MAX_FILENAME_LENGTH]


def _looks_like_binary_garbage(content: bytes) -> bool:
    """Heuristique pour les formats texte (.csv/.txt/.log), qui n'ont pas de
    signature binaire vérifiable : la présence d'un octet NUL est un indicateur
    fiable et peu sujet aux faux positifs qu'il ne s'agit pas de texte (c'est
    la même heuristique qu'utilisent `git` ou la commande `file`)."""
    return b"\x00" in content


def _resolve_storage_path(stored_name: str) -> str:
    """Construit le chemin physique de destination et vérifie qu'il reste
    strictement à l'intérieur du répertoire d'upload (défense en profondeur :
    `stored_name` est toujours généré par le serveur, jamais par le client,
    mais on ne fait pas confiance implicitement à cette seule garantie)."""
    upload_dir = os.path.abspath(settings.upload_dir)
    destination_path = os.path.abspath(os.path.join(upload_dir, stored_name))
    if os.path.commonpath([upload_dir, destination_path]) != upload_dir:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chemin de destination invalide pour la pièce jointe.",
        )
    return destination_path


async def _read_upload_content(file: UploadFile, max_size_bytes: int) -> bytes:
    """Lit le fichier envoyé par blocs, en rejetant dès que la taille maximale
    est dépassée — le fichier n'est jamais chargé intégralement en mémoire
    avant d'être potentiellement rejeté (protection contre un envoi
    volontairement surdimensionné)."""
    chunks: list[bytes] = []
    total_size = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le fichier dépasse la taille maximale autorisée ({settings.max_upload_size_mb} Mo).",
            )
        chunks.append(chunk)
    return b"".join(chunks)


async def save_upload(file: UploadFile) -> dict:
    """
    Valide un fichier envoyé par un utilisateur puis l'enregistre. Retourne un
    dictionnaire prêt à être persisté dans la table `attachments`.

    Contrôles appliqués, dans l'ordre :
      1. Extension autorisée.
      2. Content-Type déclaré cohérent avec l'extension (ou générique).
      3. Taille (contrôlée en flux, jamais après lecture complète).
      4. Fichier non vide.
      5. Contenu réel : signature binaire pour les formats qui en ont une,
         heuristique "texte" pour les autres — dans les deux cas, incohérence
         ou contenu non reconnu => rejet (couvre fichier falsifié, corrompu,
         ou dont l'extension ne correspond pas au contenu réel).
    """
    ext = _extract_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le type de fichier '{ext or '(sans extension)'}' n'est pas autorisé.",
        )

    expected_mime_types = EXTENSION_MIME_TYPES[ext]
    if file.content_type not in expected_mime_types and file.content_type != GENERIC_MIME_TYPE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le type MIME déclaré ne correspond pas à l'extension du fichier.",
        )

    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    content = await _read_upload_content(file, max_size_bytes)

    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le fichier envoyé est vide.")

    if ext in BINARY_VERIFIABLE_EXTENSIONS:
        detected = filetype.guess(content)
        if detected is None or detected.mime not in expected_mime_types:
            # Couvre : extension falsifiée, contenu corrompu (signature non
            # reconnaissable) et incohérence extension/contenu réel.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le contenu du fichier ne correspond pas au type annoncé.",
            )
    elif ext in TEXT_EXTENSIONS and _looks_like_binary_garbage(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le contenu du fichier ne correspond pas à un fichier texte valide.",
        )

    os.makedirs(os.path.abspath(settings.upload_dir), exist_ok=True)

    destination_path = None
    for _ in range(MAX_STORED_NAME_ATTEMPTS):
        candidate_name = f"{uuid.uuid4().hex}{ext}"
        candidate_path = _resolve_storage_path(candidate_name)
        if not os.path.exists(candidate_path):
            destination_path = candidate_path
            break
    if destination_path is None:
        # Statistiquement quasi impossible (collision UUID répétée) — filet de
        # sécurité pour ne jamais écraser un fichier existant en cas de bug.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de générer un nom de stockage unique pour cette pièce jointe.",
        )

    with open(destination_path, "wb") as buffer:
        buffer.write(content)

    return {
        "file_name": _sanitize_display_filename(file.filename or "fichier"),
        "file_path": destination_path,
        "file_type": file.content_type or GENERIC_MIME_TYPE,
        "file_size": len(content),
    }
