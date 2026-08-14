"""Tests de l'authentification : connexion, cookies, utilisateur courant."""
from tests.conftest import auth_cookies, create_user


def test_login_succeeds_with_valid_credentials(client, db_session):
    create_user(db_session, "utilisateur@test.example", "Utilisateur")
    response = client.post("/api/auth/login", json={"email": "utilisateur@test.example", "password": "MotDePasse123!"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "utilisateur@test.example"
    # Correctif #12 : le jeton n'est plus renvoyé dans le corps de la réponse,
    # uniquement posé en cookie httpOnly.
    assert "access_token" not in body
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_login_cookies_are_httponly_and_samesite_lax(client, db_session):
    """Vérifie les attributs des cookies posés à la connexion (correctif #12) :
    httpOnly (protection contre le vol de jeton par XSS) et SameSite=Lax
    (protection CSRF, sans jeton dédié — voir auth.py::_cookie_kwargs)."""
    create_user(db_session, "cookieattrs@test.example", "Utilisateur")
    response = client.post("/api/auth/login", json={"email": "cookieattrs@test.example", "password": "MotDePasse123!"})
    assert response.status_code == 200

    set_cookie_headers = response.headers.get_list("set-cookie")
    assert len(set_cookie_headers) == 2
    for header in set_cookie_headers:
        assert "httponly" in header.lower()
        assert "samesite=lax" in header.lower()

    refresh_cookie_header = next(h for h in set_cookie_headers if h.lower().startswith("refresh_token="))
    assert "path=/api/auth" in refresh_cookie_header.lower()


def test_login_fails_with_wrong_password(client, db_session):
    create_user(db_session, "utilisateur2@test.example", "Utilisateur")
    response = client.post("/api/auth/login", json={"email": "utilisateur2@test.example", "password": "MauvaisMotDePasse"})
    assert response.status_code == 401
    assert "access_token" not in response.cookies


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, db_session):
    create_user(db_session, "moi@test.example", "Technicien")
    cookies = auth_cookies(client, "moi@test.example")
    response = client.get("/api/auth/me", cookies=cookies)
    assert response.status_code == 200
    assert response.json()["email"] == "moi@test.example"


def test_authorization_header_alone_no_longer_authenticates(client, db_session):
    """Non-régression du changement de mécanisme (correctif #12) : l'ancien
    en-tête Authorization: Bearer n'a plus aucun effet, seul le cookie compte."""
    create_user(db_session, "legacyheader@test.example", "Utilisateur")
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer un-jeton-quelconque"})
    assert response.status_code == 401


def test_register_creates_user_role_account(client):
    response = client.post(
        "/api/auth/register",
        json={"first_name": "Nouvel", "last_name": "Utilisateur", "email": "nouveau@test.example", "password": "MotDePasse123!"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"]["name"] == "Utilisateur"
    assert "access_token" not in body
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
