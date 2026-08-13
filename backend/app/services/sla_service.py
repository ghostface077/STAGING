"""
Calcul du respect des SLA (Service Level Agreement) pour un ticket :
délai de première réponse, délai de résolution, temps restant, état visuel.
"""
from datetime import datetime, timedelta, timezone

from app.models.status import CLOSED_STATUSES, STATUS_RESOLU
from app.models.ticket import Ticket
from app.schemas.sla import SLAProgress

# Seuils d'affichage (en pourcentage du délai de résolution écoulé)
SEUIL_ATTENTION = 70
SEUIL_CRITIQUE = 90


def _aware(dt: datetime | None) -> datetime | None:
    """S'assure qu'une date est bien "timezone-aware" (UTC) pour permettre les comparaisons."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def compute_sla_progress(ticket: Ticket) -> SLAProgress:
    """Calcule l'état du SLA d'un ticket : délais, temps restant, indicateur visuel."""
    if ticket.sla is None:
        return SLAProgress(
            sla_id=None,
            sla_name=None,
            first_response_deadline=None,
            resolution_deadline=None,
            first_response_met=None,
            minutes_remaining=None,
            percent_elapsed=None,
            state="aucun",
        )

    created_at = _aware(ticket.created_at)
    now = datetime.now(timezone.utc)

    first_response_deadline = created_at + timedelta(minutes=ticket.sla.first_response_minutes)
    resolution_deadline = created_at + timedelta(minutes=ticket.sla.resolution_minutes)

    first_response_at = _aware(ticket.first_response_at)
    if first_response_at is not None:
        first_response_met = first_response_at <= first_response_deadline
    elif now > first_response_deadline and ticket.status.name not in CLOSED_STATUSES:
        first_response_met = False
    else:
        first_response_met = None  # pas encore de réponse, délai pas encore dépassé

    is_closed = ticket.status.name in CLOSED_STATUSES or ticket.status.name == STATUS_RESOLU
    reference_point = _aware(ticket.resolved_at) if (is_closed and ticket.resolved_at) else now

    total_seconds = (resolution_deadline - created_at).total_seconds()
    elapsed_seconds = (reference_point - created_at).total_seconds()
    percent_elapsed = round(min(max(elapsed_seconds / total_seconds * 100, 0), 999), 1) if total_seconds > 0 else 0.0

    minutes_remaining = int((resolution_deadline - reference_point).total_seconds() // 60)

    if is_closed:
        state = "normal" if reference_point <= resolution_deadline else "depasse"
    elif reference_point > resolution_deadline:
        state = "depasse"
    elif percent_elapsed >= SEUIL_CRITIQUE:
        state = "critique"
    elif percent_elapsed >= SEUIL_ATTENTION:
        state = "attention"
    else:
        state = "normal"

    return SLAProgress(
        sla_id=ticket.sla.id,
        sla_name=ticket.sla.name,
        first_response_deadline=first_response_deadline,
        resolution_deadline=resolution_deadline,
        first_response_met=first_response_met,
        minutes_remaining=minutes_remaining,
        percent_elapsed=percent_elapsed,
        state=state,
    )


def is_sla_breached(ticket: Ticket) -> bool:
    """Indique si le SLA de résolution est dépassé pour ce ticket (utilisé pour les statistiques)."""
    progress = compute_sla_progress(ticket)
    return progress.state == "depasse"
