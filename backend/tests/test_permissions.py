"""Tests de contrôle d'accès (RBAC) sur les endpoints d'administration."""
from tests.conftest import auth_headers, create_user


def test_regular_user_cannot_list_users(client, db_session):
    create_user(db_session, "simple@test.example", "Utilisateur")
    response = client.get("/api/users", headers=auth_headers(client, "simple@test.example"))
    assert response.status_code == 403


def test_manager_can_list_users(client, db_session):
    create_user(db_session, "manager@test.example", "Responsable IT")
    response = client.get("/api/users", headers=auth_headers(client, "manager@test.example"))
    assert response.status_code == 200


def test_only_admin_can_create_role(client, db_session):
    create_user(db_session, "manager2@test.example", "Responsable IT")
    admin = create_user(db_session, "admin@test.example", "Administrateur")

    response_manager = client.post("/api/roles", json={"name": "Rôle Test"}, headers=auth_headers(client, "manager2@test.example"))
    assert response_manager.status_code == 403

    response_admin = client.post("/api/roles", json={"name": "Rôle Test"}, headers=auth_headers(client, "admin@test.example"))
    assert response_admin.status_code == 201


def test_deactivated_user_cannot_authenticate(client, db_session):
    user = create_user(db_session, "inactif@test.example", "Utilisateur")
    user.is_active = False
    db_session.commit()

    response = client.post("/api/auth/login", json={"email": "inactif@test.example", "password": "MotDePasse123!"})
    assert response.status_code == 403
