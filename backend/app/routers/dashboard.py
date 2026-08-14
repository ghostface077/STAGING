"""
API de statistiques pour les tableaux de bord (utilisateur, technicien, responsable IT,
administrateur). Le périmètre des données est adapté au rôle de l'utilisateur connecté.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user, require_manager
from app.models.role import ROLE_ADMINISTRATEUR, ROLE_RESPONSABLE_IT, ROLE_TECHNICIEN
from app.models.satisfaction_rating import SatisfactionRating
from app.models.status import (
    CLOSED_STATUSES,
    STATUS_EN_ATTENTE,
    STATUS_EN_COURS,
    STATUS_FERME,
    STATUS_OUVERT,
    STATUS_RESOLU,
)
from app.models.priority import PRIORITY_CRITIQUE
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.dashboard import CountByLabel, DashboardStatistics, SLAOverview, TechnicianStats
from app.services.sla_service import compute_sla_progress

router = APIRouter(prefix="/api/dashboard", tags=["Tableau de bord"])


def _scoped_query(db: Session, current_user: User):
    """Restreint la portée des tickets selon le rôle : Utilisateur → ses tickets, Technicien → ses tickets assignés."""
    query = db.query(Ticket).options(
        joinedload(Ticket.status), joinedload(Ticket.priority), joinedload(Ticket.category), joinedload(Ticket.sla)
    ).filter(Ticket.deleted_at.is_(None))  # correctif #09 : exclure les tickets supprimés des statistiques
    role = current_user.role.name
    if role not in (ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR):
        if role == ROLE_TECHNICIEN:
            query = query.filter(Ticket.technician_id == current_user.id)
        else:
            query = query.filter(Ticket.requester_id == current_user.id)
    return query


@router.get("/statistics", response_model=DashboardStatistics)
def get_statistics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = _scoped_query(db, current_user).all()

    total = len(tickets)
    ouverts = sum(1 for t in tickets if t.status.name == STATUS_OUVERT)
    en_cours = sum(1 for t in tickets if t.status.name == STATUS_EN_COURS)
    en_attente = sum(1 for t in tickets if t.status.name == STATUS_EN_ATTENTE)
    resolus = sum(1 for t in tickets if t.status.name == STATUS_RESOLU)
    fermes = sum(1 for t in tickets if t.status.name == STATUS_FERME)
    critiques = sum(1 for t in tickets if t.priority.name == PRIORITY_CRITIQUE and t.status.name not in CLOSED_STATUSES)
    sla_depasse = sum(1 for t in tickets if compute_sla_progress(t).state == "depasse")

    resolved_tickets = [t for t in tickets if t.resolved_at is not None]
    temps_resolution = (
        sum((t.resolved_at - t.created_at).total_seconds() for t in resolved_tickets) / len(resolved_tickets) / 3600
        if resolved_tickets
        else None
    )
    responded_tickets = [t for t in tickets if t.first_response_at is not None]
    temps_reponse = (
        sum((t.first_response_at - t.created_at).total_seconds() for t in responded_tickets) / len(responded_tickets) / 60
        if responded_tickets
        else None
    )

    ratings = (
        db.query(func.avg(SatisfactionRating.rating))
        .join(Ticket, Ticket.id == SatisfactionRating.ticket_id)
        .filter(Ticket.id.in_([t.id for t in tickets]) if tickets else False)
        .scalar()
    )

    return DashboardStatistics(
        total_tickets=total,
        tickets_ouverts=ouverts,
        tickets_en_cours=en_cours,
        tickets_en_attente=en_attente,
        tickets_resolus=resolus,
        tickets_fermes=fermes,
        tickets_critiques=critiques,
        tickets_sla_depasse=sla_depasse,
        temps_moyen_resolution_heures=round(temps_resolution, 1) if temps_resolution is not None else None,
        temps_moyen_premiere_reponse_minutes=round(temps_reponse, 1) if temps_reponse is not None else None,
        satisfaction_moyenne=round(float(ratings), 2) if ratings is not None else None,
    )


@router.get("/tickets-by-status", response_model=list[CountByLabel])
def tickets_by_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = _scoped_query(db, current_user).all()
    counts: dict[str, int] = {}
    for t in tickets:
        counts[t.status.name] = counts.get(t.status.name, 0) + 1
    return [CountByLabel(label=label, count=count) for label, count in counts.items()]


@router.get("/tickets-by-priority", response_model=list[CountByLabel])
def tickets_by_priority(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = _scoped_query(db, current_user).all()
    counts: dict[str, int] = {}
    for t in tickets:
        counts[t.priority.name] = counts.get(t.priority.name, 0) + 1
    return [CountByLabel(label=label, count=count) for label, count in counts.items()]


@router.get("/tickets-by-category", response_model=list[CountByLabel])
def tickets_by_category(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = _scoped_query(db, current_user).all()
    counts: dict[str, int] = {}
    for t in tickets:
        counts[t.category.name] = counts.get(t.category.name, 0) + 1
    return [CountByLabel(label=label, count=count) for label, count in counts.items()]


@router.get("/tickets-by-technician", response_model=list[TechnicianStats])
def tickets_by_technician(current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    """Statistiques nominatives de tous les techniciens (charge, résolutions, temps
    moyen). Réservé aux Responsables IT et Administrateurs (correctif #06) : un
    Technicien dispose déjà de ses propres chiffres, scopés automatiquement à
    ses tickets assignés, via les autres endpoints de ce router."""
    technicians = db.query(User).join(User.role).filter(User.role.has(name=ROLE_TECHNICIEN)).all()
    results = []
    for tech in technicians:
        assigned = db.query(Ticket).filter(Ticket.technician_id == tech.id, Ticket.deleted_at.is_(None)).all()
        resolved = [t for t in assigned if t.resolved_at is not None]
        avg_hours = (
            sum((t.resolved_at - t.created_at).total_seconds() for t in resolved) / len(resolved) / 3600
            if resolved
            else None
        )
        results.append(
            TechnicianStats(
                technician_id=tech.id,
                technician_name=tech.full_name,
                tickets_assignes=len(assigned),
                tickets_resolus=len(resolved),
                temps_moyen_resolution_heures=round(avg_hours, 1) if avg_hours is not None else None,
            )
        )
    return results


@router.get("/sla", response_model=SLAOverview)
def sla_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = [t for t in _scoped_query(db, current_user).all() if t.sla_id is not None]
    total = len(tickets)
    depasses = 0
    bientot = 0
    for t in tickets:
        state = compute_sla_progress(t).state
        if state == "depasse":
            depasses += 1
        elif state in ("attention", "critique"):
            bientot += 1
    respectes = total - depasses
    taux = round((respectes / total) * 100, 1) if total else 100.0
    return SLAOverview(
        total_avec_sla=total, respectes=respectes, bientot_depasses=bientot, depasses=depasses, taux_respect_pourcent=taux
    )
