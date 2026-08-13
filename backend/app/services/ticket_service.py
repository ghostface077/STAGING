"""Logique métier partagée pour la gestion du cycle de vie d'un ticket."""
from sqlalchemy.orm import Session

from app.models.sla import SLA


def find_active_sla_for_priority(db: Session, priority_id: int) -> SLA | None:
    """Retourne le SLA actif correspondant à une priorité donnée (le plus récent si plusieurs)."""
    return (
        db.query(SLA)
        .filter(SLA.priority_id == priority_id, SLA.is_active.is_(True))
        .order_by(SLA.id.desc())
        .first()
    )
