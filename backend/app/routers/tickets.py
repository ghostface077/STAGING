"""
API des tickets : cycle de vie complet (création, attribution, prise en charge,
changement de statut/priorité, résolution, fermeture, réouverture, escalade).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_admin, require_staff, require_user_role, get_current_user
from app.models.role import ROLE_ADMINISTRATEUR, ROLE_RESPONSABLE_IT, ROLE_TECHNICIEN, ROLE_UTILISATEUR
from app.models.status import (
    STATUS_FERME,
    STATUS_NOUVEAU,
    STATUS_REOUVERT,
    STATUS_RESOLU,
)
from app.models.status import Status as StatusModel
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.common import Message, Page, PaginationParams
from app.schemas.ticket_history import TicketHistoryOut
from app.schemas.ticket import (
    TicketAssignRequest,
    TicketCreate,
    TicketEscalateRequest,
    TicketListItem,
    TicketOut,
    TicketPriorityRequest,
    TicketResolveRequest,
    TicketStatusRequest,
    TicketUpdate,
)
from app.services.history_service import log_audit, log_ticket_action
from app.services.notification_service import notify_ticket_participants, notify_user
from app.services.reference_service import generate_ticket_reference
from app.services.sla_service import compute_sla_progress
from app.services.ticket_service import find_active_sla_for_priority
from app.services.ticket_state_machine import describe_invalid_transition

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


def _ticket_query(db: Session):
    return db.query(Ticket).options(
        joinedload(Ticket.requester),
        joinedload(Ticket.technician),
        joinedload(Ticket.team),
        joinedload(Ticket.category),
        joinedload(Ticket.priority),
        joinedload(Ticket.status),
        joinedload(Ticket.sla),
        joinedload(Ticket.deleted_by),
    )


def _get_status_by_name(db: Session, name: str) -> StatusModel:
    db_status = db.query(StatusModel).filter(StatusModel.name == name).first()
    if db_status is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statut de référence « {name} » introuvable. Vérifiez les données de base (seed).",
        )
    return db_status


def _to_out(ticket: Ticket) -> TicketOut:
    data = TicketOut.model_validate(ticket)
    data.sla_progress = compute_sla_progress(ticket)
    return data


def _to_list_item(ticket: Ticket) -> TicketListItem:
    data = TicketListItem.model_validate(ticket)
    data.sla_progress = compute_sla_progress(ticket)
    return data


def _can_view_ticket(ticket: Ticket, user: User) -> bool:
    role = user.role.name
    if role in (ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR):
        return True
    if role == ROLE_TECHNICIEN:
        return ticket.technician_id == user.id or ticket.technician_id is None
    return ticket.requester_id == user.id


def _get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    """Ticket actif uniquement (correctif #09) — un ticket supprimé logiquement
    n'est plus accessible via aucune de ces routes (consultation, modification,
    attribution, changement de statut, etc.)."""
    ticket = _ticket_query(db).filter(Ticket.id == ticket_id, Ticket.deleted_at.is_(None)).first()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket introuvable.")
    return ticket


def _get_ticket_any_state_or_404(db: Session, ticket_id: int) -> Ticket:
    """Récupère un ticket qu'il soit actif ou supprimé — réservé aux deux seules
    routes qui doivent pouvoir agir sur un ticket déjà supprimé : la suppression
    elle-même (pour détecter un doublon) et la restauration."""
    ticket = _ticket_query(db).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket introuvable.")
    return ticket


def _mark_first_response_if_needed(ticket: Ticket) -> None:
    if ticket.first_response_at is None:
        ticket.first_response_at = datetime.now(timezone.utc)


def _apply_ticket_filters(
    query,
    *,
    current_user: User,
    status_id: int | None,
    priority_id: int | None,
    category_id: int | None,
    technician_id: int | None,
    team_id: int | None,
    requester_id: int | None,
    unassigned: bool | None,
    search: str | None,
    include_deleted: bool = False,
):
    """Applique les règles de portée par rôle et les filtres de recherche à une
    requête de tickets. Extrait de `list_tickets` pour être appliqué à la fois
    à la requête de comptage (COUNT) et à la requête de page (correctif #07),
    sans dupliquer la logique entre les deux.

    include_deleted=True (correctif #09, réservé Administrateur) retourne
    exclusivement les tickets supprimés (la « corbeille »), jamais un mélange
    actifs/supprimés."""
    query = query.filter(Ticket.deleted_at.is_not(None) if include_deleted else Ticket.deleted_at.is_(None))

    role = current_user.role.name

    if role == ROLE_UTILISATEUR:
        query = query.filter(Ticket.requester_id == current_user.id)
    elif role == ROLE_TECHNICIEN:
        if unassigned:
            query = query.filter(Ticket.technician_id.is_(None))
        else:
            query = query.filter(
                or_(Ticket.technician_id == current_user.id, Ticket.technician_id.is_(None))
            )
    # Responsable IT et Administrateur voient tous les tickets

    if status_id:
        query = query.filter(Ticket.status_id == status_id)
    if priority_id:
        query = query.filter(Ticket.priority_id == priority_id)
    if category_id:
        query = query.filter(Ticket.category_id == category_id)
    if technician_id:
        query = query.filter(Ticket.technician_id == technician_id)
    if team_id:
        query = query.filter(Ticket.team_id == team_id)
    if requester_id:
        query = query.filter(Ticket.requester_id == requester_id)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Ticket.reference.ilike(like), Ticket.title.ilike(like)))

    return query


@router.get("", response_model=Page[TicketListItem])
def list_tickets(
    status_id: int | None = None,
    priority_id: int | None = None,
    category_id: int | None = None,
    technician_id: int | None = None,
    team_id: int | None = None,
    requester_id: int | None = None,
    unassigned: bool | None = None,
    search: str | None = None,
    include_deleted: bool = False,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste paginée des tickets visibles par l'utilisateur connecté, avec filtres
    de recherche avancée. include_deleted=true (réservé Administrateur, correctif
    #09) affiche exclusivement les tickets supprimés (la « corbeille »)."""
    if include_deleted and current_user.role.name != ROLE_ADMINISTRATEUR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Seul un administrateur peut consulter les tickets supprimés."
        )

    filters = dict(
        current_user=current_user, status_id=status_id, priority_id=priority_id, category_id=category_id,
        technician_id=technician_id, team_id=team_id, requester_id=requester_id,
        unassigned=unassigned, search=search, include_deleted=include_deleted,
    )

    total = _apply_ticket_filters(db.query(func.count(Ticket.id)), **filters).scalar()

    tickets = (
        _apply_ticket_filters(_ticket_query(db), **filters)
        .order_by(Ticket.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )

    return Page.build(
        items=[_to_list_item(t) for t in tickets], total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = _get_ticket_or_404(db, ticket_id)
    if not _can_view_ticket(ticket, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à ce ticket.")
    return _to_out(ticket)


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, current_user: User = Depends(require_user_role), db: Session = Depends(get_db)):
    """
    Crée un nouveau ticket. Réservé au rôle Utilisateur : un ticket est toujours créé par la
    personne qui rencontre le problème. Techniciens, Responsables IT et Administrateurs
    traitent ou supervisent des tickets déjà existants, mais n'en créent jamais eux-mêmes.
    Le demandeur est toujours l'utilisateur connecté.
    """
    nouveau_status = _get_status_by_name(db, STATUS_NOUVEAU)
    sla = find_active_sla_for_priority(db, payload.priority_id)

    ticket = Ticket(
        reference=generate_ticket_reference(db),
        title=payload.title,
        description=payload.description,
        requester_id=current_user.id,
        category_id=payload.category_id,
        priority_id=payload.priority_id,
        equipment_id=payload.equipment_id,
        status_id=nouveau_status.id,
        sla_id=sla.id if sla else None,
    )
    db.add(ticket)
    db.flush()

    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="creation", new_value=ticket.reference)
    db.commit()
    db.refresh(ticket)
    return _to_out(_get_ticket_or_404(db, ticket.id))


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int, payload: TicketUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Met à jour les champs éditoriaux d'un ticket (titre, description, catégorie, équipement)."""
    ticket = _get_ticket_or_404(db, ticket_id)
    role = current_user.role.name
    is_owner = ticket.requester_id == current_user.id
    is_staff = role in (ROLE_TECHNICIEN, ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR)

    if not (is_staff or (is_owner and ticket.status.name == STATUS_NOUVEAU)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce ticket ne peut plus être modifié par le demandeur (il a déjà été pris en charge).",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)

    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="modification")
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.delete("/{ticket_id}", response_model=Message)
def delete_ticket(
    ticket_id: int,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Supprime logiquement un ticket (correctif #09) : rien n'est physiquement
    effacé (commentaires, pièces jointes, historique, évaluation de satisfaction
    conservés intégralement) — le ticket devient simplement invisible dans les
    vues métier normales, et un administrateur peut le restaurer.
    Réservé aux Responsables IT et Administrateurs."""
    if current_user.role.name == ROLE_TECHNICIEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seuls les responsables IT et administrateurs peuvent supprimer un ticket.")
    ticket = _get_ticket_any_state_or_404(db, ticket_id)
    if ticket.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce ticket a déjà été supprimé.")

    ticket.deleted_at = datetime.now(timezone.utc)
    ticket.deleted_by_id = current_user.id

    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="suppression", old_value=ticket.reference)
    log_audit(db, user_id=current_user.id, action="suppression_ticket", entity_type="ticket", entity_id=ticket.id)
    db.commit()
    return Message(message="Ticket supprimé avec succès.")


@router.post("/{ticket_id}/restore", response_model=TicketOut)
def restore_ticket(
    ticket_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Restaure un ticket précédemment supprimé (correctif #09). Réservé à
    l'administrateur : une restauration réintroduit dans les vues métier des
    données volontairement retirées — opération plus sensible que la
    suppression elle-même (réservée à Responsable IT + Administrateur)."""
    ticket = _get_ticket_any_state_or_404(db, ticket_id)
    if ticket.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce ticket n'est pas supprimé.")

    previous_deleted_by = ticket.deleted_by_id
    ticket.deleted_at = None
    ticket.deleted_by_id = None

    log_ticket_action(
        db, ticket=ticket, user_id=current_user.id, action="restauration",
        old_value=str(previous_deleted_by) if previous_deleted_by else None,
    )
    log_audit(db, user_id=current_user.id, action="restauration_ticket", entity_type="ticket", entity_id=ticket.id)
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.get("/{ticket_id}/history", response_model=list[TicketHistoryOut])
def get_ticket_history(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retourne l'historique complet des actions effectuées sur un ticket."""
    ticket = _get_ticket_or_404(db, ticket_id)
    if not _can_view_ticket(ticket, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à ce ticket.")
    return ticket.history


@router.post("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    ticket_id: int, payload: TicketAssignRequest, current_user: User = Depends(require_staff), db: Session = Depends(get_db)
):
    """
    Attribue un ticket à un technicien et/ou une équipe.
    Un technicien peut « prendre en charge » un ticket non assigné en s'auto-désignant.
    """
    ticket = _get_ticket_or_404(db, ticket_id)
    role = current_user.role.name

    if role == ROLE_TECHNICIEN:
        if payload.technician_id not in (current_user.id, None):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Un technicien ne peut prendre en charge un ticket que pour lui-même.",
            )
        if ticket.technician_id is not None and ticket.technician_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ce ticket est déjà pris en charge par un autre technicien.")

    old_technician = ticket.technician_id
    if payload.technician_id is not None:
        technician = db.get(User, payload.technician_id)
        if technician is None or technician.role.name != ROLE_TECHNICIEN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Technicien invalide.")
    ticket.technician_id = payload.technician_id
    if payload.team_id is not None:
        ticket.team_id = payload.team_id

    if ticket.status.name == STATUS_NOUVEAU and ticket.technician_id is not None:
        ticket.status = _get_status_by_name(db, "Ouvert")

    action = "prise_en_charge" if role == ROLE_TECHNICIEN else "attribution"
    log_ticket_action(
        db, ticket=ticket, user_id=current_user.id, action=action,
        old_value=str(old_technician) if old_technician else None,
        new_value=str(ticket.technician_id) if ticket.technician_id else None,
    )
    if ticket.technician_id:
        notify_user(
            db, user_id=ticket.technician_id, ticket=ticket,
            title="Nouveau ticket attribué",
            message=f"Le ticket {ticket.reference} vous a été attribué.",
            type="attribution",
        )
    notify_user(
        db, user_id=ticket.requester_id, ticket=ticket,
        title="Votre ticket a été attribué",
        message=f"Votre ticket {ticket.reference} a été attribué à un technicien.",
        type="attribution",
    )
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.post("/{ticket_id}/status", response_model=TicketOut)
def change_status(
    ticket_id: int, payload: TicketStatusRequest, current_user: User = Depends(require_staff), db: Session = Depends(get_db)
):
    """
    Change le statut d'un ticket parmi les statuts actifs (membre du personnel
    support uniquement). Résolu et Fermé restent exclusivement accessibles via
    les actions dédiées « Résoudre »/« Fermer »/« Réouvrir » (correctif #13) :
    ce sont les seules à synchroniser correctement resolved_at/closed_at,
    évitant qu'un ticket redevienne actif tout en gardant une date de
    résolution non nulle.
    """
    ticket = _get_ticket_or_404(db, ticket_id)
    new_status = db.get(StatusModel, payload.status_id)
    if new_status is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide.")

    old_status_name = ticket.status.name
    invalid_reason = describe_invalid_transition(current_status_name=old_status_name, target_status_name=new_status.name)
    if invalid_reason is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=invalid_reason)

    ticket.status = new_status
    _mark_first_response_if_needed(ticket)

    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="changement_statut", old_value=old_status_name, new_value=new_status.name)
    notify_ticket_participants(
        db, ticket=ticket, title="Statut du ticket modifié",
        message=f"Le ticket {ticket.reference} est passé au statut « {new_status.name} ».",
        type="changement_statut", exclude_user_id=current_user.id,
    )
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.post("/{ticket_id}/priority", response_model=TicketOut)
def change_priority(
    ticket_id: int, payload: TicketPriorityRequest, current_user: User = Depends(require_staff), db: Session = Depends(get_db)
):
    """Change la priorité d'un ticket et réévalue le SLA applicable en conséquence."""
    ticket = _get_ticket_or_404(db, ticket_id)
    old_priority_name = ticket.priority.name
    ticket.priority_id = payload.priority_id

    sla = find_active_sla_for_priority(db, payload.priority_id)
    ticket.sla_id = sla.id if sla else None

    db.flush()
    db.refresh(ticket)
    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="changement_priorite", old_value=old_priority_name, new_value=ticket.priority.name)
    notify_ticket_participants(
        db, ticket=ticket, title="Priorité du ticket modifiée",
        message=f"La priorité du ticket {ticket.reference} est désormais « {ticket.priority.name} ».",
        type="changement_priorite", exclude_user_id=current_user.id,
    )
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.post("/{ticket_id}/resolve", response_model=TicketOut)
def resolve_ticket(
    ticket_id: int, payload: TicketResolveRequest, current_user: User = Depends(require_staff), db: Session = Depends(get_db)
):
    """Marque un ticket comme résolu et enregistre la solution apportée."""
    ticket = _get_ticket_or_404(db, ticket_id)
    resolu_status = _get_status_by_name(db, STATUS_RESOLU)
    old_status_name = ticket.status.name

    ticket.solution = payload.solution
    ticket.status = resolu_status
    ticket.resolved_at = datetime.now(timezone.utc)
    _mark_first_response_if_needed(ticket)

    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="resolution", old_value=old_status_name, new_value=STATUS_RESOLU)
    notify_user(
        db, user_id=ticket.requester_id, ticket=ticket,
        title="Votre ticket a été résolu",
        message=f"Le ticket {ticket.reference} a été marqué comme résolu. Merci de confirmer la résolution.",
        type="resolution",
    )
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.post("/{ticket_id}/close", response_model=TicketOut)
def close_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Ferme un ticket. Le demandeur peut fermer/confirmer un ticket résolu ;
    le personnel support peut fermer un ticket à tout moment.
    """
    ticket = _get_ticket_or_404(db, ticket_id)
    role = current_user.role.name
    is_owner = ticket.requester_id == current_user.id
    is_staff = role in (ROLE_TECHNICIEN, ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR)

    if not (is_staff or is_owner):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez pas fermer ce ticket.")

    ferme_status = _get_status_by_name(db, STATUS_FERME)
    old_status_name = ticket.status.name
    ticket.status = ferme_status
    ticket.closed_at = datetime.now(timezone.utc)
    if ticket.resolved_at is None:
        ticket.resolved_at = ticket.closed_at

    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="fermeture", old_value=old_status_name, new_value=STATUS_FERME)
    notify_ticket_participants(
        db, ticket=ticket, title="Ticket fermé",
        message=f"Le ticket {ticket.reference} a été fermé.",
        type="fermeture", exclude_user_id=current_user.id,
    )
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.post("/{ticket_id}/reopen", response_model=TicketOut)
def reopen_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Réouvre un ticket précédemment résolu ou fermé."""
    ticket = _get_ticket_or_404(db, ticket_id)
    role = current_user.role.name
    is_owner = ticket.requester_id == current_user.id
    is_staff = role in (ROLE_TECHNICIEN, ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR)

    if not (is_staff or is_owner):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez pas réouvrir ce ticket.")
    if ticket.status.name not in {STATUS_RESOLU, STATUS_FERME}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seul un ticket résolu ou fermé peut être réouvert.")

    reouvert_status = _get_status_by_name(db, STATUS_REOUVERT)
    old_status_name = ticket.status.name
    ticket.status = reouvert_status
    ticket.resolved_at = None
    ticket.closed_at = None

    log_ticket_action(db, ticket=ticket, user_id=current_user.id, action="reouverture", old_value=old_status_name, new_value=STATUS_REOUVERT)
    notify_ticket_participants(
        db, ticket=ticket, title="Ticket réouvert",
        message=f"Le ticket {ticket.reference} a été réouvert.",
        type="reouverture", exclude_user_id=current_user.id,
    )
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.post("/{ticket_id}/escalate", response_model=TicketOut)
def escalate_ticket(
    ticket_id: int, payload: TicketEscalateRequest, current_user: User = Depends(require_staff), db: Session = Depends(get_db)
):
    """Escalade un ticket vers une autre équipe ou un autre technicien (avec motif optionnel)."""
    ticket = _get_ticket_or_404(db, ticket_id)
    old_technician = ticket.technician_id

    if payload.team_id is not None:
        ticket.team_id = payload.team_id
    if payload.technician_id is not None:
        technician = db.get(User, payload.technician_id)
        if technician is None or technician.role.name != ROLE_TECHNICIEN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Technicien invalide.")
        ticket.technician_id = payload.technician_id

    log_ticket_action(
        db, ticket=ticket, user_id=current_user.id, action="escalade",
        old_value=str(old_technician) if old_technician else None,
        new_value=payload.reason or "Escalade sans motif précisé",
    )
    if ticket.technician_id:
        notify_user(
            db, user_id=ticket.technician_id, ticket=ticket,
            title="Ticket escaladé vers vous",
            message=f"Le ticket {ticket.reference} vous a été escaladé.",
            type="attribution",
        )
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)
