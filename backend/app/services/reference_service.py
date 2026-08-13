"""Génération de la référence unique d'un ticket : TCK-AAAA-NNNNN."""
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ticket import Ticket


def generate_ticket_reference(db: Session) -> str:
    """Génère la prochaine référence de ticket pour l'année en cours (ex : TCK-2026-00001)."""
    year = datetime.now(timezone.utc).year
    prefix = f"TCK-{year}-"

    count = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.reference.like(f"{prefix}%"))
        .scalar()
        or 0
    )

    next_number = count + 1
    reference = f"{prefix}{next_number:05d}"

    # Sécurité anti-collision (au cas où une référence aurait été supprimée puis recréée)
    while db.query(Ticket).filter(Ticket.reference == reference).first() is not None:
        next_number += 1
        reference = f"{prefix}{next_number:05d}"

    return reference
