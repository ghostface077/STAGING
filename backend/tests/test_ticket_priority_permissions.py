"""Tests de la nouvelle règle métier : un Utilisateur ne choisit plus la
priorité de son ticket (fixée par défaut à "Normale", toute valeur envoyée
est ignorée), seuls Responsable IT et Administrateur peuvent la définir/
modifier ensuite — un Technicien ne le peut plus."""
from app.models.category import Category
from app.models.priority import Priority
from tests.conftest import auth_cookies, create_user


def _ticket_payload(db_session, **overrides):
    category = db_session.query(Category).first()
    payload = {
        "title": "Mon imprimante ne fonctionne plus",
        "description": "Le voyant rouge clignote depuis ce matin.",
        "category_id": category.id,
    }
    payload.update(overrides)
    return payload


def test_user_created_ticket_defaults_to_normale_priority(client, db_session):
    create_user(db_session, "user-prio1@test.example", "Utilisateur")

    response = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "user-prio1@test.example"))

    assert response.status_code == 201
    assert response.json()["priority"]["name"] == "Normale"


def test_user_cannot_impose_a_priority_via_the_api(client, db_session):
    """Même en envoyant priority_id directement (en contournant l'interface),
    le ticket créé par un Utilisateur reste à la priorité par défaut."""
    create_user(db_session, "user-prio2@test.example", "Utilisateur")
    critique = db_session.query(Priority).filter_by(name="Critique").first()

    response = client.post(
        "/api/tickets",
        json=_ticket_payload(db_session, priority_id=critique.id),
        cookies=auth_cookies(client, "user-prio2@test.example"),
    )

    assert response.status_code == 201
    assert response.json()["priority"]["name"] == "Normale"
    assert response.json()["priority"]["name"] != "Critique"


def test_manager_can_set_priority(client, db_session):
    create_user(db_session, "user-prio3@test.example", "Utilisateur")
    create_user(db_session, "manager-prio3@test.example", "Responsable IT")
    haute = db_session.query(Priority).filter_by(name="Haute").first()
    ticket = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "user-prio3@test.example")).json()

    response = client.post(
        f"/api/tickets/{ticket['id']}/priority",
        json={"priority_id": haute.id},
        cookies=auth_cookies(client, "manager-prio3@test.example"),
    )

    assert response.status_code == 200
    assert response.json()["priority"]["name"] == "Haute"


def test_admin_can_set_priority(client, db_session):
    create_user(db_session, "user-prio4@test.example", "Utilisateur")
    create_user(db_session, "admin-prio4@test.example", "Administrateur")
    critique = db_session.query(Priority).filter_by(name="Critique").first()
    ticket = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "user-prio4@test.example")).json()

    response = client.post(
        f"/api/tickets/{ticket['id']}/priority",
        json={"priority_id": critique.id},
        cookies=auth_cookies(client, "admin-prio4@test.example"),
    )

    assert response.status_code == 200
    assert response.json()["priority"]["name"] == "Critique"


def test_technician_cannot_change_priority(client, db_session):
    create_user(db_session, "user-prio5@test.example", "Utilisateur")
    create_user(db_session, "tech-prio5@test.example", "Technicien")
    haute = db_session.query(Priority).filter_by(name="Haute").first()
    ticket = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "user-prio5@test.example")).json()

    response = client.post(
        f"/api/tickets/{ticket['id']}/priority",
        json={"priority_id": haute.id},
        cookies=auth_cookies(client, "tech-prio5@test.example"),
    )

    assert response.status_code == 403


def test_ticket_creation_does_not_require_equipment(client, db_session):
    """Le champ équipement n'est pas requis à la création (déjà optionnel,
    confirmé explicitement ici) et reste absent (None) si non fourni."""
    create_user(db_session, "user-prio6@test.example", "Utilisateur")

    response = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "user-prio6@test.example"))

    assert response.status_code == 201
    assert response.json()["equipment_id"] is None
