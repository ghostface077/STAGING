"""Tests unitaires du calcul de respect des SLA."""
from datetime import datetime, timedelta, timezone

from app.models.category import Category
from app.models.priority import Priority
from app.models.sla import SLA
from app.models.status import Status
from app.models.ticket import Ticket
from app.services.sla_service import compute_sla_progress
from tests.conftest import create_user


def _make_ticket(db_session, created_at, status_name="Ouvert", resolved_at=None):
    requester = create_user(db_session, "sla-user@test.example", "Utilisateur")
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    sla = db_session.query(SLA).filter_by(priority_id=priority.id).first()
    status = db_session.query(Status).filter_by(name=status_name).first()

    ticket = Ticket(
        reference="TCK-2026-99999",
        title="Ticket de test SLA",
        description="Description de test.",
        requester_id=requester.id,
        category_id=category.id,
        priority_id=priority.id,
        status_id=status.id,
        sla_id=sla.id,
        created_at=created_at,
        resolved_at=resolved_at,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


def test_sla_state_is_normal_when_recently_created(db_session):
    ticket = _make_ticket(db_session, created_at=datetime.now(timezone.utc) - timedelta(minutes=10))
    progress = compute_sla_progress(ticket)
    assert progress.state == "normal"
    assert progress.minutes_remaining > 0


def test_sla_state_is_depasse_when_deadline_passed(db_session):
    # SLA « Normale » = 480 minutes de résolution : on simule un ticket créé il y a 10 heures
    ticket = _make_ticket(db_session, created_at=datetime.now(timezone.utc) - timedelta(hours=10))
    progress = compute_sla_progress(ticket)
    assert progress.state == "depasse"
    assert progress.minutes_remaining < 0


def test_sla_respected_for_closed_ticket_resolved_in_time(db_session):
    created_at = datetime.now(timezone.utc) - timedelta(hours=10)
    ticket = _make_ticket(db_session, created_at=created_at, status_name="Résolu", resolved_at=created_at + timedelta(hours=2))
    progress = compute_sla_progress(ticket)
    assert progress.state == "normal"
