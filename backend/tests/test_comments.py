"""Tests de la visibilité des commentaires (public vs note interne)."""
from app.models.category import Category
from app.models.priority import Priority
from tests.conftest import auth_cookies, create_user


def _create_ticket(client, db_session, requester_email):
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    payload = {
        "title": "Problème de messagerie",
        "description": "Je ne reçois plus mes e-mails depuis ce matin.",
        "category_id": category.id,
        "priority_id": priority.id,
    }
    return client.post("/api/tickets", json=payload, cookies=auth_cookies(client, requester_email)).json()


def test_internal_note_is_hidden_from_requester(client, db_session):
    create_user(db_session, "demandeur@test.example", "Utilisateur")
    create_user(db_session, "technicien@test.example", "Technicien")
    ticket = _create_ticket(client, db_session, "demandeur@test.example")

    client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"content": "Note interne : vérifier le quota de la boîte mail.", "is_internal": True},
        cookies=auth_cookies(client, "technicien@test.example"),
    )
    client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"content": "Bonjour, nous étudions votre demande.", "is_internal": False},
        cookies=auth_cookies(client, "technicien@test.example"),
    )

    response_user = client.get(f"/api/tickets/{ticket['id']}/comments", cookies=auth_cookies(client, "demandeur@test.example"))
    assert response_user.status_code == 200
    assert len(response_user.json()) == 1
    assert response_user.json()[0]["is_internal"] is False

    response_tech = client.get(f"/api/tickets/{ticket['id']}/comments", cookies=auth_cookies(client, "technicien@test.example"))
    assert len(response_tech.json()) == 2


def test_user_cannot_create_internal_note(client, db_session):
    create_user(db_session, "demandeur2@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "demandeur2@test.example")

    response = client.post(
        f"/api/tickets/{ticket['id']}/comments",
        json={"content": "Ma tentative de note interne", "is_internal": True},
        cookies=auth_cookies(client, "demandeur2@test.example"),
    )
    assert response.status_code == 201
    assert response.json()["is_internal"] is False  # rétrogradé en commentaire public
