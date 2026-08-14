"""Tests d'autorisation du tableau de bord : statistiques nominatives par
technicien (correctif #06 — GET /api/dashboard/tickets-by-technician)."""
from app.models.category import Category
from app.models.priority import Priority
from tests.conftest import auth_cookies, create_user


def _ticket_payload(db_session):
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    return {
        "title": "Écran qui reste noir au démarrage",
        "description": "Le poste ne s'allume plus depuis ce matin.",
        "category_id": category.id,
        "priority_id": priority.id,
    }


# --- Test 1 : Utilisateur authentifié -> refusé ---

def test_regular_user_cannot_access_technician_stats(client, db_session):
    create_user(db_session, "user1@test.example", "Utilisateur")
    response = client.get("/api/dashboard/tickets-by-technician", cookies=auth_cookies(client, "user1@test.example"))
    assert response.status_code == 403


# --- Test 2 : Technicien -> règle métier attendue = refusé (ses propres chiffres
# sont déjà disponibles, scopés, via les autres endpoints du dashboard) ---

def test_technician_cannot_access_technician_stats(client, db_session):
    create_user(db_session, "tech1@test.example", "Technicien")
    response = client.get("/api/dashboard/tickets-by-technician", cookies=auth_cookies(client, "tech1@test.example"))
    assert response.status_code == 403


def test_technician_still_gets_own_scoped_statistics(client, db_session):
    """Non-régression : un technicien continue d'obtenir ses propres chiffres
    (scopés) via les endpoints inchangés du dashboard — il n'a donc besoin
    d'aucun accès à la liste nominative pour connaître sa propre performance."""
    technicien = create_user(db_session, "tech1b@test.example", "Technicien")
    create_user(db_session, "req1b@test.example", "Utilisateur")
    ticket = client.post(
        "/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "req1b@test.example")
    ).json()
    client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"technician_id": technicien.id},
        cookies=auth_cookies(client, "tech1b@test.example"),
    )

    response = client.get("/api/dashboard/statistics", cookies=auth_cookies(client, "tech1b@test.example"))
    assert response.status_code == 200
    assert response.json()["total_tickets"] == 1  # scopé à son propre ticket assigné


# --- Test 3 : Responsable IT -> autorisé (prévu par la matrice) ---

def test_manager_can_access_technician_stats(client, db_session):
    create_user(db_session, "manager1@test.example", "Responsable IT")
    response = client.get("/api/dashboard/tickets-by-technician", cookies=auth_cookies(client, "manager1@test.example"))
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# --- Test 4 : Administrateur -> autorisé (prévu par la matrice) ---

def test_admin_can_access_technician_stats(client, db_session):
    create_user(db_session, "admin1@test.example", "Administrateur")
    response = client.get("/api/dashboard/tickets-by-technician", cookies=auth_cookies(client, "admin1@test.example"))
    assert response.status_code == 200


def test_manager_sees_correct_nominative_data(client, db_session):
    """Vérifie que la donnée nominative reste correcte et complète pour un rôle autorisé."""
    technicien = create_user(db_session, "tech2@test.example", "Technicien")
    create_user(db_session, "manager2@test.example", "Responsable IT")
    create_user(db_session, "req2@test.example", "Utilisateur")
    ticket = client.post(
        "/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "req2@test.example")
    ).json()
    client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"technician_id": technicien.id},
        cookies=auth_cookies(client, "tech2@test.example"),
    )

    response = client.get("/api/dashboard/tickets-by-technician", cookies=auth_cookies(client, "manager2@test.example"))
    assert response.status_code == 200
    entry = next(item for item in response.json() if item["technician_id"] == technicien.id)
    assert entry["technician_name"] == technicien.full_name
    assert entry["tickets_assignes"] == 1


# --- Test 5 : utilisateur non authentifié -> 401 ---

def test_unauthenticated_cannot_access_technician_stats(client, db_session):
    response = client.get("/api/dashboard/tickets-by-technician")
    assert response.status_code == 401


# --- Test 6 : manipulation d'un technician_id -> aucune fuite ---

def test_manipulating_technician_id_on_ticket_list_leaks_nothing(client, db_session):
    """Un utilisateur non autorisé ne peut pas obtenir de statistiques agrégées
    sur un technicien en manipulant le paramètre technician_id d'une autre
    route (/api/tickets) : la portée par rôle s'applique toujours."""
    technicien = create_user(db_session, "tech3@test.example", "Technicien")
    create_user(db_session, "req3@test.example", "Utilisateur")
    create_user(db_session, "intrus3@test.example", "Utilisateur")
    ticket = client.post(
        "/api/tickets", json=_ticket_payload(db_session), cookies=auth_cookies(client, "req3@test.example")
    ).json()
    client.post(
        f"/api/tickets/{ticket['id']}/assign",
        json={"technician_id": technicien.id},
        cookies=auth_cookies(client, "tech3@test.example"),
    )

    response = client.get(
        "/api/tickets", params={"technician_id": technicien.id}, cookies=auth_cookies(client, "intrus3@test.example")
    )
    assert response.status_code == 200  # la route existe et répond normalement...
    body = response.json()
    assert body["items"] == []  # ...mais ne renvoie aucun ticket d'un autre utilisateur
    assert body["total"] == 0
    assert technicien.full_name not in response.text


# --- Test 7 : statistiques globales toujours fonctionnelles pour les rôles autorisés ---

def test_global_statistics_still_work_for_authorized_roles(client, db_session):
    create_user(db_session, "manager3@test.example", "Responsable IT")
    create_user(db_session, "admin3@test.example", "Administrateur")

    for email in ("manager3@test.example", "admin3@test.example"):
        response = client.get("/api/dashboard/statistics", cookies=auth_cookies(client, email))
        assert response.status_code == 200
        for endpoint in ("tickets-by-status", "tickets-by-priority", "tickets-by-category", "sla"):
            r = client.get(f"/api/dashboard/{endpoint}", cookies=auth_cookies(client, email))
            assert r.status_code == 200, f"{endpoint} a régressé pour {email}"


# --- Test 8 : aucune route alternative ne fuite les mêmes données ---

def test_no_alternative_route_leaks_technician_stats(client, db_session):
    """Les autres routes exposant potentiellement des données nominatives par
    technicien (rapports) restent, elles aussi, hors d'accès à un rôle non autorisé."""
    create_user(db_session, "user4@test.example", "Utilisateur")
    create_user(db_session, "tech4@test.example", "Technicien")

    for email in ("user4@test.example", "tech4@test.example"):
        assert client.get("/api/reports/summary", cookies=auth_cookies(client, email)).status_code == 403
        assert client.get("/api/reports/export.csv", cookies=auth_cookies(client, email)).status_code == 403
        assert client.get("/api/users", cookies=auth_cookies(client, email)).status_code == 403


# --- Test 9 : la réponse de refus ne contient aucune donnée nominative ---

def test_forbidden_response_contains_no_nominative_data(client, db_session):
    technicien = create_user(db_session, "tech5@test.example", "Technicien")
    create_user(db_session, "user5@test.example", "Utilisateur")

    response = client.get("/api/dashboard/tickets-by-technician", cookies=auth_cookies(client, "user5@test.example"))
    assert response.status_code == 403
    assert technicien.full_name not in response.text
    assert technicien.email not in response.text
    assert "tickets_assignes" not in response.text
