"""Tests du cycle de vie des tickets : création, attribution, statut, résolution."""
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


def test_create_ticket_generates_reference(client, db_session):
    create_user(db_session, "demandeur@test.example", "Utilisateur")
    cookies = auth_cookies(client, "demandeur@test.example")

    response = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=cookies)
    assert response.status_code == 201
    body = response.json()
    assert body["reference"].startswith("TCK-")
    assert body["status"]["name"] == "Nouveau"


def test_technician_can_take_unassigned_ticket(client, db_session):
    create_user(db_session, "demandeur2@test.example", "Utilisateur")
    technicien = create_user(db_session, "technicien@test.example", "Technicien")

    ticket = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "demandeur2@test.example")).json()

    response = client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"technician_id": technicien.id},
        cookies=auth_cookies(client, "technicien@test.example"),
    )
    assert response.status_code == 200
    assert response.json()["technician"]["id"] == technicien.id
    assert response.json()["status"]["name"] == "Ouvert"


def test_technician_cannot_assign_ticket_to_someone_else(client, db_session):
    create_user(db_session, "demandeur3@test.example", "Utilisateur")
    create_user(db_session, "technicien2@test.example", "Technicien")
    autre_technicien = create_user(db_session, "technicien3@test.example", "Technicien")

    ticket = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "demandeur3@test.example")).json()

    response = client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"technician_id": autre_technicien.id},
        cookies=auth_cookies(client, "technicien2@test.example"),
    )
    assert response.status_code == 403


def test_resolve_ticket_sets_solution_and_status(client, db_session):
    create_user(db_session, "demandeur4@test.example", "Utilisateur")
    create_user(db_session, "technicien4@test.example", "Technicien")

    ticket = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "demandeur4@test.example")).json()

    response = client.post(
        f"/api/tickets/{ticket['id']}/resolve",
        json={"solution": "Remplacement du câble d'alimentation."},
        cookies=auth_cookies(client, "technicien4@test.example"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"]["name"] == "Résolu"
    assert body["solution"] == "Remplacement du câble d'alimentation."


def test_regular_user_cannot_view_others_tickets(client, db_session):
    create_user(db_session, "proprietaire@test.example", "Utilisateur")
    create_user(db_session, "intrus@test.example", "Utilisateur")

    ticket = client.post("/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "proprietaire@test.example")).json()

    response = client.get(f"/api/tickets/{ticket['id']}", cookies=auth_cookies(client, "intrus@test.example"))
    assert response.status_code == 403


def test_only_user_role_can_create_ticket(client, db_session):
    """Règle métier : seul le rôle Utilisateur crée des tickets ; les autres rôles sont refusés (403)."""
    create_user(db_session, "demandeur5@test.example", "Utilisateur")
    create_user(db_session, "technicien5@test.example", "Technicien")
    create_user(db_session, "manager5@test.example", "Responsable IT")
    create_user(db_session, "admin5@test.example", "Administrateur")

    payload = _ticket_payload(db_session)

    response_user = client.post("/api/tickets", json=payload, cookies=auth_cookies(client, "demandeur5@test.example"))
    assert response_user.status_code == 201

    for email in ("technicien5@test.example", "manager5@test.example", "admin5@test.example"):
        response = client.post("/api/tickets", json=payload, cookies=auth_cookies(client, email))
        assert response.status_code == 403, f"{email} n'aurait pas dû pouvoir créer un ticket"


def test_technician_default_list_excludes_unassigned_tickets(client, db_session):
    """La vue par défaut d'un technicien (sans filtre) ne doit contenir que ses
    propres tickets assignés — les tickets non assignés restent réservés à la
    vue dédiée `unassigned=true` (page « Non assignés »), pas mélangés ici."""
    create_user(db_session, "demandeur6@test.example", "Utilisateur")
    technicien = create_user(db_session, "technicien6@test.example", "Technicien")
    autre_technicien = create_user(db_session, "technicien7@test.example", "Technicien")

    payload = _ticket_payload(db_session)
    demandeur_cookies = auth_cookies(client, "demandeur6@test.example")

    ticket_non_assigne = client.post("/api/tickets", json=payload, cookies=demandeur_cookies).json()
    ticket_assigne = client.post("/api/tickets", json=payload, cookies=demandeur_cookies).json()
    ticket_autre_technicien = client.post("/api/tickets", json=payload, cookies=demandeur_cookies).json()

    tech_cookies = auth_cookies(client, "technicien6@test.example")
    client.post(f"/api/tickets/{ticket_assigne['id']}/assign", json={"technician_id": technicien.id}, cookies=tech_cookies)
    client.post(
        f"/api/tickets/{ticket_autre_technicien['id']}/assign",
        json={"technician_id": autre_technicien.id},
        cookies=auth_cookies(client, "technicien7@test.example"),
    )

    default_list = client.get("/api/tickets", cookies=tech_cookies).json()
    default_ids = {item["id"] for item in default_list["items"]}
    assert default_ids == {ticket_assigne["id"]}
    assert ticket_non_assigne["id"] not in default_ids
    assert ticket_autre_technicien["id"] not in default_ids

    unassigned_list = client.get("/api/tickets", params={"unassigned": True}, cookies=tech_cookies).json()
    unassigned_ids = {item["id"] for item in unassigned_list["items"]}
    assert unassigned_ids == {ticket_non_assigne["id"]}
