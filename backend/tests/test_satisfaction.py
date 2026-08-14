"""Tests de l'API des évaluations de satisfaction : autorisation (correctif #03 —
IDOR sur GET /api/tickets/{ticket_id}/satisfaction) et non-régression du cycle
de vie existant."""
from app.models.category import Category
from app.models.priority import Priority
from tests.conftest import auth_cookies, create_user


def _ticket_payload(db_session):
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    return {
        "title": "Mon imprimante ne fonctionne plus",
        "description": "Le voyant rouge clignote depuis ce matin.",
        "category_id": category.id,
        "priority_id": priority.id,
    }


def _create_resolved_ticket(client, db_session, requester_email, technician):
    """Crée un ticket, l'assigne au technicien donné puis le résout — état
    requis avant de pouvoir déposer une évaluation de satisfaction."""
    ticket = client.post(
        "/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, requester_email)
    ).json()
    client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"technician_id": technician.id},
        cookies=auth_cookies(client, technician.email),
    )
    resolved = client.post(
        f"/api/tickets/{ticket['id']}/resolve",
        json={"solution": "Problème résolu."},
        cookies=auth_cookies(client, technician.email),
    ).json()
    return resolved


# --- Test 1 : le propriétaire consulte sa propre évaluation ---

def test_owner_can_view_own_satisfaction(client, db_session):
    create_user(db_session, "proprio1@test.example", "Utilisateur")
    technicien = create_user(db_session, "tech1@test.example", "Technicien")
    ticket = _create_resolved_ticket(client, db_session, "proprio1@test.example", technicien)

    create_resp = client.post(
        f"/api/tickets/{ticket['id']}/satisfaction",
        json={"rating": 5, "comment": "Très réactif, merci."},
        cookies=auth_cookies(client, "proprio1@test.example"),
    )
    assert create_resp.status_code == 201

    get_resp = client.get(
        f"/api/tickets/{ticket['id']}/satisfaction", cookies=auth_cookies(client, "proprio1@test.example")
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["rating"] == 5
    assert get_resp.json()["comment"] == "Très réactif, merci."


# --- Test 2 : un utilisateur tiers ne peut pas consulter l'évaluation d'un autre (IDOR) ---

def test_other_user_cannot_view_others_satisfaction(client, db_session):
    create_user(db_session, "proprio2@test.example", "Utilisateur")
    create_user(db_session, "intrus2@test.example", "Utilisateur")
    technicien = create_user(db_session, "tech2@test.example", "Technicien")
    ticket = _create_resolved_ticket(client, db_session, "proprio2@test.example", technicien)

    client.post(
        f"/api/tickets/{ticket['id']}/satisfaction",
        json={"rating": 4, "comment": "Correct."},
        cookies=auth_cookies(client, "proprio2@test.example"),
    )

    response = client.get(
        f"/api/tickets/{ticket['id']}/satisfaction", cookies=auth_cookies(client, "intrus2@test.example")
    )
    assert response.status_code == 403
    assert "rating" not in response.text  # la donnée protégée ne doit jamais fuiter dans la réponse


# --- Test 3 : un utilisateur tiers ne peut pas créer/« modifier » l'évaluation d'un ticket qui n'est pas le sien ---

def test_other_user_cannot_create_satisfaction_for_others_ticket(client, db_session):
    create_user(db_session, "proprio3@test.example", "Utilisateur")
    create_user(db_session, "intrus3@test.example", "Utilisateur")
    technicien = create_user(db_session, "tech3@test.example", "Technicien")
    ticket = _create_resolved_ticket(client, db_session, "proprio3@test.example", technicien)

    response = client.post(
        f"/api/tickets/{ticket['id']}/satisfaction",
        json={"rating": 1, "comment": "Tentative non autorisée."},
        cookies=auth_cookies(client, "intrus3@test.example"),
    )
    assert response.status_code == 403


# --- Test 4 : aucun endpoint de suppression n'existe (rien à contourner) ---

def test_no_delete_endpoint_exists(client, db_session):
    create_user(db_session, "proprio4@test.example", "Utilisateur")
    technicien = create_user(db_session, "tech4@test.example", "Technicien")
    ticket = _create_resolved_ticket(client, db_session, "proprio4@test.example", technicien)
    client.post(
        f"/api/tickets/{ticket['id']}/satisfaction",
        json={"rating": 3},
        cookies=auth_cookies(client, "proprio4@test.example"),
    )

    response = client.delete(
        f"/api/tickets/{ticket['id']}/satisfaction", cookies=auth_cookies(client, "proprio4@test.example")
    )
    assert response.status_code == 405  # méthode non autorisée : DELETE n'est pas défini sur cette route


# --- Test 5 : aucune authentification -> 401 ---

def test_unauthenticated_cannot_view_satisfaction(client, db_session):
    create_user(db_session, "proprio5@test.example", "Utilisateur")
    technicien = create_user(db_session, "tech5@test.example", "Technicien")
    ticket = _create_resolved_ticket(client, db_session, "proprio5@test.example", technicien)

    response = client.get(f"/api/tickets/{ticket['id']}/satisfaction")
    assert response.status_code == 401


# --- Test 6 : les permissions Responsable IT / Administrateur sont conservées ---

def test_manager_and_admin_can_view_any_satisfaction(client, db_session):
    create_user(db_session, "proprio6@test.example", "Utilisateur")
    technicien = create_user(db_session, "tech6@test.example", "Technicien")
    create_user(db_session, "manager6@test.example", "Responsable IT")
    create_user(db_session, "admin6@test.example", "Administrateur")
    ticket = _create_resolved_ticket(client, db_session, "proprio6@test.example", technicien)
    client.post(
        f"/api/tickets/{ticket['id']}/satisfaction",
        json={"rating": 2, "comment": "Peut mieux faire."},
        cookies=auth_cookies(client, "proprio6@test.example"),
    )

    for email in ("manager6@test.example", "admin6@test.example"):
        response = client.get(f"/api/tickets/{ticket['id']}/satisfaction", cookies=auth_cookies(client, email))
        assert response.status_code == 200, f"{email} devrait pouvoir consulter n'importe quelle évaluation"
        assert response.json()["rating"] == 2


# --- Règle métier Technicien : assigné -> autorisé, non assigné/autre -> refusé ---

def test_assigned_technician_can_view_satisfaction(client, db_session):
    create_user(db_session, "proprio7@test.example", "Utilisateur")
    technicien = create_user(db_session, "tech7@test.example", "Technicien")
    ticket = _create_resolved_ticket(client, db_session, "proprio7@test.example", technicien)
    client.post(
        f"/api/tickets/{ticket['id']}/satisfaction",
        json={"rating": 5},
        cookies=auth_cookies(client, "proprio7@test.example"),
    )

    response = client.get(f"/api/tickets/{ticket['id']}/satisfaction", cookies=auth_cookies(client, "tech7@test.example"))
    assert response.status_code == 200


def test_unrelated_technician_cannot_view_satisfaction(client, db_session):
    create_user(db_session, "proprio8@test.example", "Utilisateur")
    technicien = create_user(db_session, "tech8a@test.example", "Technicien")
    create_user(db_session, "tech8b@test.example", "Technicien")  # non assigné à CE ticket
    ticket = _create_resolved_ticket(client, db_session, "proprio8@test.example", technicien)
    client.post(
        f"/api/tickets/{ticket['id']}/satisfaction",
        json={"rating": 5},
        cookies=auth_cookies(client, "proprio8@test.example"),
    )

    # Le ticket est déjà assigné à tech8a : un autre technicien ne doit pas y avoir accès
    # (règle _can_view_ticket : technician_id == moi OU technician_id est vide).
    response = client.get(f"/api/tickets/{ticket['id']}/satisfaction", cookies=auth_cookies(client, "tech8b@test.example"))
    assert response.status_code == 403
