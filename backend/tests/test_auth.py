"""Tests de l'authentification : connexion, token, utilisateur courant."""
from tests.conftest import auth_headers, create_user


def test_login_succeeds_with_valid_credentials(client, db_session):
    create_user(db_session, "utilisateur@test.example", "Utilisateur")
    response = client.post("/api/auth/login", json={"email": "utilisateur@test.example", "password": "MotDePasse123!"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["user"]["email"] == "utilisateur@test.example"


def test_login_fails_with_wrong_password(client, db_session):
    create_user(db_session, "utilisateur2@test.example", "Utilisateur")
    response = client.post("/api/auth/login", json={"email": "utilisateur2@test.example", "password": "MauvaisMotDePasse"})
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, db_session):
    create_user(db_session, "moi@test.example", "Technicien")
    headers = auth_headers(client, "moi@test.example")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "moi@test.example"


def test_register_creates_user_role_account(client):
    response = client.post(
        "/api/auth/register",
        json={"first_name": "Nouvel", "last_name": "Utilisateur", "email": "nouveau@test.example", "password": "MotDePasse123!"},
    )
    assert response.status_code == 201
    assert response.json()["user"]["role"]["name"] == "Utilisateur"
