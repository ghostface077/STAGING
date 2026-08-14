"""
API de rapports : synthèse chiffrée sur une période et export CSV.
L'export PDF/Excel n'est pas encore implémenté ; l'architecture (fonction
`build_report_rows`) est prévue pour être réutilisée par un futur exporteur.
"""
import csv
import io
from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_manager
from app.models.satisfaction_rating import SatisfactionRating
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.dashboard import DashboardStatistics
from app.services.sla_service import compute_sla_progress

router = APIRouter(prefix="/api/reports", tags=["Rapports"])


def _period_query(db: Session, date_from: date | None, date_to: date | None):
    query = db.query(Ticket).options(
        joinedload(Ticket.requester), joinedload(Ticket.technician), joinedload(Ticket.category),
        joinedload(Ticket.priority), joinedload(Ticket.status),
    ).filter(Ticket.deleted_at.is_(None))  # correctif #09 : exclure les tickets supprimés des rapports
    if date_from:
        query = query.filter(Ticket.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        query = query.filter(Ticket.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))
    return query


@router.get("/summary", response_model=DashboardStatistics)
def report_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    """Synthèse chiffrée des tickets sur une période donnée (réservé Responsable IT / Administrateur)."""
    tickets = _period_query(db, date_from, date_to).all()

    total = len(tickets)
    resolved_tickets = [t for t in tickets if t.resolved_at is not None]
    responded_tickets = [t for t in tickets if t.first_response_at is not None]

    temps_resolution = (
        sum((t.resolved_at - t.created_at).total_seconds() for t in resolved_tickets) / len(resolved_tickets) / 3600
        if resolved_tickets else None
    )
    temps_reponse = (
        sum((t.first_response_at - t.created_at).total_seconds() for t in responded_tickets) / len(responded_tickets) / 60
        if responded_tickets else None
    )
    sla_depasse = sum(1 for t in tickets if compute_sla_progress(t).state == "depasse")

    ticket_ids = [t.id for t in tickets]
    ratings = (
        db.query(SatisfactionRating).filter(SatisfactionRating.ticket_id.in_(ticket_ids)).all() if ticket_ids else []
    )
    satisfaction_moyenne = round(sum(r.rating for r in ratings) / len(ratings), 2) if ratings else None

    return DashboardStatistics(
        total_tickets=total,
        tickets_ouverts=sum(1 for t in tickets if t.status.name == "Ouvert"),
        tickets_en_cours=sum(1 for t in tickets if t.status.name == "En cours"),
        tickets_en_attente=sum(1 for t in tickets if t.status.name == "En attente"),
        tickets_resolus=sum(1 for t in tickets if t.status.name == "Résolu"),
        tickets_fermes=sum(1 for t in tickets if t.status.name == "Fermé"),
        tickets_critiques=sum(1 for t in tickets if t.priority.name == "Critique"),
        tickets_sla_depasse=sla_depasse,
        temps_moyen_resolution_heures=round(temps_resolution, 1) if temps_resolution is not None else None,
        temps_moyen_premiere_reponse_minutes=round(temps_reponse, 1) if temps_reponse is not None else None,
        satisfaction_moyenne=satisfaction_moyenne,
    )


@router.get("/export.csv")
def export_csv(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
):
    """Exporte la liste des tickets de la période au format CSV (compatible Excel)."""
    tickets = _period_query(db, date_from, date_to).order_by(Ticket.created_at).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([
        "Référence", "Titre", "Statut", "Priorité", "Catégorie", "Demandeur", "Technicien",
        "Date de création", "Date de résolution",
    ])
    for t in tickets:
        writer.writerow([
            t.reference,
            t.title,
            t.status.name,
            t.priority.name,
            t.category.name,
            t.requester.full_name,
            t.technician.full_name if t.technician else "",
            t.created_at.strftime("%Y-%m-%d %H:%M"),
            t.resolved_at.strftime("%Y-%m-%d %H:%M") if t.resolved_at else "",
        ])

    buffer.seek(0)
    filename = f"rapport_tickets_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
