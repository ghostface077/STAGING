"""Tests du renouvellement de session et de la révocation des refresh tokens
(correctif #12) : POST /api/auth/refresh, /logout, changement de mot de passe,
désactivation de compte."""
from app.models.refresh_token import RefreshToken
from tests.conftest import auth_cookies, create_user


def _login_cookies(client, email: str, password: str = "MotDePasse123!") -> dict:
    """Connexion directe (sans le cache de auth_cookies) : nécessaire ici car
    plusieurs tests ont besoin d'observer/consommer un refresh token précis
    (rotation, révocation), incompatible avec la réutilisation en cache."""
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    cookies = dict(response.cookies)
    client.cookies.clear()
    return cookies


# ============================= renouvellement =============================

def test_refresh_issues_new_valid_access_token(client, db_session):
    create_user(db_session, "refresh1@test.example", "Utilisateur")
    cookies = _login_cookies(client, "refresh1@test.example")

    response = client.post("/api/auth/refresh", cookies={"refresh_token": cookies["refresh_token"]})
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    new_access_token = response.cookies["access_token"]
    me = client.get("/api/auth/me", cookies={"access_token": new_access_token})
    assert me.status_code == 200
    assert me.json()["email"] == "refresh1@test.example"


def test_refresh_rotates_refresh_token_old_one_rejected(client, db_session):
    """La rotation révoque l'ancien refresh token dès son utilisation : le
    rejouer une seconde fois échoue (limite la fenêtre d'exploitation d'un vol)."""
    create_user(db_session, "refresh2@test.example", "Utilisateur")
    cookies = _login_cookies(client, "refresh2@test.example")

    first = client.post("/api/auth/refresh", cookies={"refresh_token": cookies["refresh_token"]})
    assert first.status_code == 200

    replay = client.post("/api/auth/refresh", cookies={"refresh_token": cookies["refresh_token"]})
    assert replay.status_code == 401


def test_refresh_without_cookie_returns_401(client, db_session):
    response = client.post("/api/auth/refresh")
    assert response.status_code == 401


def test_refresh_with_garbage_token_returns_401(client, db_session):
    response = client.post("/api/auth/refresh", cookies={"refresh_token": "un-jeton-invalide"})
    assert response.status_code == 401


def test_refresh_rejects_access_token_used_as_refresh_token(client, db_session):
    """Un access token, même valide, n'est pas accepté à la place d'un refresh
    token : le claim `type` est vérifié, pas seulement la signature."""
    create_user(db_session, "refresh3@test.example", "Utilisateur")
    cookies = _login_cookies(client, "refresh3@test.example")

    response = client.post("/api/auth/refresh", cookies={"refresh_token": cookies["access_token"]})
    assert response.status_code == 401


# ============================= déconnexion =============================

def test_logout_revokes_refresh_token(client, db_session):
    create_user(db_session, "logout1@test.example", "Utilisateur")
    cookies = _login_cookies(client, "logout1@test.example")

    logout_response = client.post("/api/auth/logout", cookies=cookies)
    assert logout_response.status_code == 200

    refresh_response = client.post("/api/auth/refresh", cookies={"refresh_token": cookies["refresh_token"]})
    assert refresh_response.status_code == 401


def test_logout_clears_cookies(client, db_session):
    create_user(db_session, "logout2@test.example", "Utilisateur")
    cookies = _login_cookies(client, "logout2@test.example")

    response = client.post("/api/auth/logout", cookies=cookies)
    set_cookie_headers = "\n".join(response.headers.get_list("set-cookie")).lower()
    assert "access_token=" in set_cookie_headers
    assert "refresh_token=" in set_cookie_headers


# ============================= révocation sur événement de sécurité =============================

def test_password_change_revokes_all_sessions(client, db_session):
    create_user(db_session, "pwdchange@test.example", "Utilisateur")
    cookies = _login_cookies(client, "pwdchange@test.example")

    change_response = client.put(
        "/api/users/moi/mot-de-passe",
        json={"current_password": "MotDePasse123!", "new_password": "NouveauMotDePasse456!"},
        cookies=cookies,
    )
    assert change_response.status_code == 200

    refresh_response = client.post("/api/auth/refresh", cookies={"refresh_token": cookies["refresh_token"]})
    assert refresh_response.status_code == 401


def test_admin_deactivation_revokes_all_sessions(client, db_session):
    create_user(db_session, "admin-revoke@test.example", "Administrateur")
    target = create_user(db_session, "target-revoke@test.example", "Utilisateur")
    target_cookies = _login_cookies(client, "target-revoke@test.example")

    admin_cookies = auth_cookies(client, "admin-revoke@test.example")
    deactivate_response = client.delete(f"/api/users/{target.id}", cookies=admin_cookies)
    assert deactivate_response.status_code == 200

    refresh_response = client.post("/api/auth/refresh", cookies={"refresh_token": target_cookies["refresh_token"]})
    assert refresh_response.status_code == 401


def test_deactivation_marks_refresh_tokens_revoked_in_database(client, db_session):
    """Vérifie directement en base que la révocation est effective (pas
    seulement observable via le comportement de l'endpoint)."""
    create_user(db_session, "admin-revoke2@test.example", "Administrateur")
    target = create_user(db_session, "target-revoke2@test.example", "Utilisateur")
    _login_cookies(client, "target-revoke2@test.example")

    admin_cookies = auth_cookies(client, "admin-revoke2@test.example")
    client.delete(f"/api/users/{target.id}", cookies=admin_cookies)

    sessions = db_session.query(RefreshToken).filter(RefreshToken.user_id == target.id).all()
    assert len(sessions) >= 1
    assert all(session.revoked_at is not None for session in sessions)
