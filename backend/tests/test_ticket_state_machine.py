"""Tests de la machine à états du statut des tickets (correctif #13) :
POST /api/tickets/{id}/status ne doit accepter que des transitions actives
légitimes ; Résolu/Fermé restent réservés aux actions dédiées."""
from app.models.category import Category
from app.models.priority import Priority
from app.models.status import Status
from app.models.ticket import Ticket
from tests.conftest import auth_cookies, create_user


def _ticket_payload(db_session, title="Ticket machine à états"):
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    return {
        "title": title,
        "description": "Description du ticket.",
        "category_id": category.id,
        "priority_id": priority.id,
    }


def _create_ticket(client, db_session, requester_email, title="Ticket machine à états"):
    return client.post(
        "/api/tickets", json=_ticket_payload(db_session, title), cookies=auth_cookies(client, requester_email)
    ).json()


def _status_id(db_session, name: str) -> int:
    return db_session.query(Status).filter_by(name=name).first().id


def _change_status(client, ticket_id, status_name, db_session, actor_email):
    return client.post(
        f"/api/tickets/{ticket_id}/status",
        json={"status_id": _status_id(db_session, status_name)},
        cookies=auth_cookies(client, actor_email),
    )


# ============================= transitions actives légitimes =============================

def test_allowed_active_transitions_succeed(client, db_session):
    create_user(db_session, "manager-sm1@test.example", "Responsable IT")
    create_user(db_session, "req-sm1@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sm1@test.example")

    for target in ("Ouvert", "En cours", "En attente", "Ouvert"):
        response = _change_status(client, ticket["id"], target, db_session, "manager-sm1@test.example")
        assert response.status_code == 200, response.text
        assert response.json()["status"]["name"] == target


def test_technician_can_change_status(client, db_session):
    """Non-régression : le personnel support (pas seulement Responsable IT) reste autorisé."""
    create_user(db_session, "tech-sm2@test.example", "Technicien")
    create_user(db_session, "req-sm2@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sm2@test.example")

    response = _change_status(client, ticket["id"], "En cours", db_session, "tech-sm2@test.example")
    assert response.status_code == 200


def test_regular_user_cannot_change_status(client, db_session):
    """Non-régression : réservé au personnel support."""
    create_user(db_session, "req-sm3@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sm3@test.example")

    response = _change_status(client, ticket["id"], "En cours", db_session, "req-sm3@test.example")
    assert response.status_code == 403


# ============================= transitions refusées =============================

def test_same_status_transition_rejected(client, db_session):
    create_user(db_session, "manager-sm4@test.example", "Responsable IT")
    create_user(db_session, "req-sm4@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sm4@test.example")

    response = _change_status(client, ticket["id"], "Nouveau", db_session, "manager-sm4@test.example")
    assert response.status_code == 409
    assert "déjà" in response.json()["detail"]


def test_cannot_reach_resolu_via_change_status(client, db_session):
    create_user(db_session, "manager-sm5@test.example", "Responsable IT")
    create_user(db_session, "req-sm5@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sm5@test.example")

    response = _change_status(client, ticket["id"], "Résolu", db_session, "manager-sm5@test.example")
    assert response.status_code == 409
    assert "Résoudre" in response.json()["detail"]


def test_cannot_reach_ferme_via_change_status(client, db_session):
    create_user(db_session, "manager-sm6@test.example", "Responsable IT")
    create_user(db_session, "req-sm6@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sm6@test.example")

    response = _change_status(client, ticket["id"], "Fermé", db_session, "manager-sm6@test.example")
    assert response.status_code == 409
    assert "Fermer" in response.json()["detail"]


def test_cannot_leave_resolu_via_change_status(client, db_session):
    """Un ticket Résolu ne peut redevenir actif que via /reopen, jamais via
    change_status — c'est précisément la faille corrigée par ce correctif."""
    create_user(db_session, "manager-sm7@test.example", "Responsable IT")
    create_user(db_session, "req-sm7@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sm7@test.example")

    resolve = client.post(
        f"/api/tickets/{ticket['id']}/resolve", json={"solution": "Résolu."},
        cookies=auth_cookies(client, "manager-sm7@test.example"),
    )
    assert resolve.status_code == 200
    assert resolve.json()["resolved_at"] is not None

    response = _change_status(client, ticket["id"], "En cours", db_session, "manager-sm7@test.example")
    assert response.status_code == 409
    assert "Réouvrir" in response.json()["detail"]

    # resolved_at doit rester intact : aucune corruption possible via ce chemin.
    db_ticket = db_session.get(Ticket, ticket["id"])
    assert db_ticket.resolved_at is not None
    assert db_ticket.status.name == "Résolu"


def test_annule_is_terminal(client, db_session):
    create_user(db_session, "manager-sm8@test.example", "Responsable IT")
    create_user(db_session, "req-sm8@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sm8@test.example")

    cancel = _change_status(client, ticket["id"], "Annulé", db_session, "manager-sm8@test.example")
    assert cancel.status_code == 200
    assert cancel.json()["status"]["name"] == "Annulé"

    response = _change_status(client, ticket["id"], "Ouvert", db_session, "manager-sm8@test.example")
    assert response.status_code == 409


# ============================= non-régression du cycle resolve/close/reopen =============================

def test_reopen_hands_control_back_to_change_status(client, db_session):
    create_user(db_session, "manager-sm9@test.example", "Responsable IT")
    create_user(db_session, "req-sm9@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-sm9@test.example")

    client.post(
        f"/api/tickets/{ticket['id']}/resolve", json={"solution": "Résolu."},
        cookies=auth_cookies(client, "manager-sm9@test.example"),
    )
    reopen = client.post(
        f"/api/tickets/{ticket['id']}/reopen", cookies=auth_cookies(client, "manager-sm9@test.example")
    )
    assert reopen.status_code == 200
    assert reopen.json()["status"]["name"] == "Réouvert"
    assert reopen.json()["resolved_at"] is None

    response = _change_status(client, ticket["id"], "En cours", db_session, "manager-sm9@test.example")
    assert response.status_code == 200
    assert response.json()["status"]["name"] == "En cours"
