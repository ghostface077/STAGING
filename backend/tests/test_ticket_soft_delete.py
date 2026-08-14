"""Tests de la suppression logique des tickets (correctif #09) : le ticket et
toutes ses données liées sont conservés, exclus des vues normales, journalisés,
et restaurables uniquement par un administrateur."""
from app.models.attachment import Attachment
from app.models.audit_log import AuditLog
from app.models.comment import Comment
from app.models.satisfaction_rating import SatisfactionRating
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory
from app.models.category import Category
from app.models.priority import Priority
from tests.conftest import auth_cookies, create_user


def _ticket_payload(db_session, title="Ticket à supprimer"):
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    return {
        "title": title,
        "description": "Description du ticket.",
        "category_id": category.id,
        "priority_id": priority.id,
    }


def _create_ticket(client, db_session, requester_email, title="Ticket à supprimer"):
    return client.post(
        "/api/tickets", json=_ticket_payload(db_session, title), cookies=auth_cookies(client, requester_email)
    ).json()


# ============================= suppression =============================

def test_soft_delete_hides_ticket_from_list_and_detail(client, db_session):
    create_user(db_session, "manager-sd1@test.example", "Responsable IT")
    create_user(db_session, "req-sd1@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd1@test.example")

    del_resp = client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "manager-sd1@test.example"))
    assert del_resp.status_code == 200

    get_resp = client.get(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "manager-sd1@test.example"))
    assert get_resp.status_code == 404

    list_resp = client.get("/api/tickets", cookies=auth_cookies(client, "manager-sd1@test.example"))
    ids = [t["id"] for t in list_resp.json()["items"]]
    assert ticket["id"] not in ids


def test_soft_delete_preserves_related_data_in_database(client, db_session):
    """Rien n'est physiquement effacé : commentaires, pièces jointes,
    historique et évaluation de satisfaction restent en base."""
    create_user(db_session, "manager-sd2@test.example", "Responsable IT")
    technicien = create_user(db_session, "tech-sd2@test.example", "Technicien")
    create_user(db_session, "req-sd2@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd2@test.example")

    client.post(
        f"/api/tickets/{ticket['id']}/comments", json={"content": "Un commentaire.", "is_internal": False},
        cookies=auth_cookies(client, "req-sd2@test.example"),
    )
    db_session.add(
        Attachment(
            ticket_id=ticket["id"], file_name="notes.txt", file_path="/tmp/notes.txt",
            file_type="text/plain", file_size=12,
        )
    )
    db_session.commit()

    client.post(
        f"/api/tickets/{ticket['id']}/assign", json={"technician_id": technicien.id},
        cookies=auth_cookies(client, "tech-sd2@test.example"),
    )

    client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "manager-sd2@test.example"))

    assert db_session.query(Comment).filter(Comment.ticket_id == ticket["id"]).count() == 1
    assert db_session.query(Attachment).filter(Attachment.ticket_id == ticket["id"]).count() == 1
    assert db_session.query(TicketHistory).filter(TicketHistory.ticket_id == ticket["id"]).count() >= 2  # création + attribution (+ suppression)

    db_ticket = db_session.get(Ticket, ticket["id"])
    assert db_ticket is not None  # toujours en base
    assert db_ticket.deleted_at is not None


def test_soft_delete_logs_audit_and_history(client, db_session):
    manager = create_user(db_session, "manager-sd3@test.example", "Responsable IT")
    create_user(db_session, "req-sd3@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd3@test.example")

    client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "manager-sd3@test.example"))

    audit_entry = (
        db_session.query(AuditLog)
        .filter(AuditLog.entity_type == "ticket", AuditLog.entity_id == ticket["id"], AuditLog.action == "suppression_ticket")
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.user_id == manager.id

    history_entry = (
        db_session.query(TicketHistory)
        .filter(TicketHistory.ticket_id == ticket["id"], TicketHistory.action == "suppression")
        .first()
    )
    assert history_entry is not None

    db_ticket = db_session.get(Ticket, ticket["id"])
    assert db_ticket.deleted_by_id == manager.id


def test_cannot_delete_already_deleted_ticket(client, db_session):
    create_user(db_session, "manager-sd4@test.example", "Responsable IT")
    create_user(db_session, "req-sd4@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd4@test.example")

    first = client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "manager-sd4@test.example"))
    assert first.status_code == 200

    second = client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "manager-sd4@test.example"))
    assert second.status_code == 409


def test_technician_still_forbidden_from_deleting(client, db_session):
    """Non-régression : la règle de rôle existante reste appliquée."""
    create_user(db_session, "tech-sd5@test.example", "Technicien")
    create_user(db_session, "req-sd5@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd5@test.example")

    response = client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "tech-sd5@test.example"))
    assert response.status_code == 403


# ============================= fuites indirectes =============================

def test_deleted_ticket_inaccessible_via_comments_attachments_satisfaction(client, db_session):
    create_user(db_session, "manager-sd6@test.example", "Responsable IT")
    create_user(db_session, "req-sd6@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd6@test.example")
    client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "manager-sd6@test.example"))

    cookies = auth_cookies(client, "req-sd6@test.example")
    assert client.get(f"/api/tickets/{ticket['id']}/comments", cookies=cookies).status_code == 404
    assert client.get(f"/api/tickets/{ticket['id']}/satisfaction", cookies=cookies).status_code == 404
    upload = client.post(
        f"/api/tickets/{ticket['id']}/attachments", files={"file": ("x.txt", b"contenu", "text/plain")}, cookies=cookies
    )
    assert upload.status_code == 404


def test_deleted_ticket_excluded_from_dashboard_and_reports(client, db_session):
    manager_email = "manager-sd7@test.example"
    create_user(db_session, manager_email, "Responsable IT")
    create_user(db_session, "req-sd7@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd7@test.example", title="Ticket unique sd7")
    cookies = auth_cookies(client, manager_email)

    before = client.get("/api/dashboard/statistics", cookies=cookies).json()["total_tickets"]
    client.delete(f"/api/tickets/{ticket['id']}", cookies=cookies)
    after = client.get("/api/dashboard/statistics", cookies=cookies).json()["total_tickets"]
    assert after == before - 1

    summary = client.get("/api/reports/summary", cookies=cookies).json()
    export = client.get("/api/reports/export.csv", cookies=cookies)
    assert "Ticket unique sd7" not in export.text
    assert summary["total_tickets"] == after


# ============================= restauration =============================

def test_restore_by_admin_makes_ticket_visible_again(client, db_session):
    admin = create_user(db_session, "admin-sd8@test.example", "Administrateur")
    create_user(db_session, "req-sd8@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd8@test.example")
    client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "admin-sd8@test.example"))

    restore = client.post(f"/api/tickets/{ticket['id']}/restore", cookies=auth_cookies(client, "admin-sd8@test.example"))
    assert restore.status_code == 200
    assert restore.json()["deleted_at"] is None

    get_resp = client.get(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "admin-sd8@test.example"))
    assert get_resp.status_code == 200

    history_entry = (
        db_session.query(TicketHistory)
        .filter(TicketHistory.ticket_id == ticket["id"], TicketHistory.action == "restauration")
        .first()
    )
    assert history_entry is not None
    audit_entry = (
        db_session.query(AuditLog)
        .filter(AuditLog.entity_type == "ticket", AuditLog.action == "restauration_ticket", AuditLog.entity_id == ticket["id"])
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.user_id == admin.id


def test_restore_forbidden_for_manager(client, db_session):
    """Décision validée : seul l'Administrateur peut restaurer, pas le Responsable IT."""
    create_user(db_session, "manager-sd9@test.example", "Responsable IT")
    create_user(db_session, "req-sd9@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd9@test.example")
    client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "manager-sd9@test.example"))

    response = client.post(f"/api/tickets/{ticket['id']}/restore", cookies=auth_cookies(client, "manager-sd9@test.example"))
    assert response.status_code == 403


def test_restore_non_deleted_ticket_conflict(client, db_session):
    create_user(db_session, "admin-sd10@test.example", "Administrateur")
    create_user(db_session, "req-sd10@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd10@test.example")

    response = client.post(f"/api/tickets/{ticket['id']}/restore", cookies=auth_cookies(client, "admin-sd10@test.example"))
    assert response.status_code == 409


# ============================= corbeille (include_deleted) =============================

def test_include_deleted_requires_admin(client, db_session):
    create_user(db_session, "manager-sd11@test.example", "Responsable IT")
    create_user(db_session, "tech-sd11@test.example", "Technicien")
    create_user(db_session, "user-sd11@test.example", "Utilisateur")

    for email in ("manager-sd11@test.example", "tech-sd11@test.example", "user-sd11@test.example"):
        response = client.get("/api/tickets", params={"include_deleted": "true"}, cookies=auth_cookies(client, email))
        assert response.status_code == 403


def test_include_deleted_returns_only_deleted_tickets(client, db_session):
    admin_email = "admin-sd12@test.example"
    create_user(db_session, admin_email, "Administrateur")
    create_user(db_session, "req-sd12@test.example", "Utilisateur")
    active_ticket = _create_ticket(client, db_session, "req-sd12@test.example", title="Actif sd12")
    deleted_ticket = _create_ticket(client, db_session, "req-sd12@test.example", title="Supprimé sd12")
    client.delete(f"/api/tickets/{deleted_ticket['id']}", cookies=auth_cookies(client, admin_email))

    corbeille = client.get(
        "/api/tickets", params={"include_deleted": "true"}, cookies=auth_cookies(client, admin_email)
    ).json()
    ids = [t["id"] for t in corbeille["items"]]
    assert deleted_ticket["id"] in ids
    assert active_ticket["id"] not in ids  # jamais de mélange actifs/supprimés

    normal_list = client.get("/api/tickets", cookies=auth_cookies(client, admin_email)).json()
    normal_ids = [t["id"] for t in normal_list["items"]]
    assert active_ticket["id"] in normal_ids
    assert deleted_ticket["id"] not in normal_ids


# ============================= non-régression =============================

def test_reference_generation_still_counts_deleted_tickets(client, db_session):
    """La référence d'un ticket ne doit jamais être réutilisée, supprimé ou non."""
    create_user(db_session, "admin-sd13@test.example", "Administrateur")
    create_user(db_session, "req-sd13@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sd13@test.example")
    client.delete(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "admin-sd13@test.example"))

    new_ticket = _create_ticket(client, db_session, "req-sd13@test.example", title="Ticket suivant")
    assert new_ticket["reference"] != ticket["reference"]
