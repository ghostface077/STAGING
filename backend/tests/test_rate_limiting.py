"""Tests du rate limiting sur la connexion (correctif #04 — protection anti
brute-force sur POST /api/auth/login)."""
from tests.conftest import create_user


def test_normal_login_still_works(client, db_session):
    """Une requête de connexion normale, isolée, doit continuer à fonctionner
    (le rate limiting ne doit pas gêner un usage légitime)."""
    create_user(db_session, "normal@test.example", "Utilisateur")

    response = client.post(
        "/api/auth/login", json={"email": "normal@test.example", "password": "MotDePasse123!"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_a_few_failed_attempts_are_not_blocked(client, db_session):
    """Quelques essais infructueux (typiquement une faute de frappe) restent
    possibles sans être bloqués : on ne pénalise pas un utilisateur légitime."""
    create_user(db_session, "typo@test.example", "Utilisateur")

    for _ in range(3):
        response = client.post(
            "/api/auth/login", json={"email": "typo@test.example", "password": "mauvais_mot_de_passe"}
        )
        assert response.status_code == 401  # refusé pour mauvais mot de passe, pas pour rate limit

    # Le 4ᵉ essai, avec le bon mot de passe cette fois, doit encore passer.
    response = client.post(
        "/api/auth/login", json={"email": "typo@test.example", "password": "MotDePasse123!"}
    )
    assert response.status_code == 200


def test_excessive_login_attempts_are_rate_limited(client, db_session):
    """Une rafale de requêtes dépassant le quota (5/minute) doit être bloquée
    avec un code 429, sans jamais révéler d'information sur le compte visé."""
    create_user(db_session, "cible@test.example", "Utilisateur")

    responses = [
        client.post("/api/auth/login", json={"email": "cible@test.example", "password": "mauvais"})
        for _ in range(5)
    ]
    assert all(r.status_code == 401 for r in responses)  # les 5 premiers essais sont dans le quota

    blocked = client.post("/api/auth/login", json={"email": "cible@test.example", "password": "mauvais"})
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["message"] == "Trop de tentatives. Merci de réessayer dans quelques instants."
    # La réponse de blocage ne doit contenir aucune donnée sur le compte (pas de token, pas d'email).
    assert "access_token" not in blocked.text
    assert "cible@test.example" not in blocked.text


def test_rate_limit_also_blocks_valid_credentials_once_quota_exceeded(client, db_session):
    """Le blocage s'applique à l'IP, pas au résultat de l'authentification :
    même une tentative avec le BON mot de passe est bloquée une fois le quota
    dépassé — la protection ne peut donc pas être contournée en devinant le
    bon mot de passe après plusieurs échecs."""
    create_user(db_session, "cible2@test.example", "Utilisateur")

    for _ in range(5):
        client.post("/api/auth/login", json={"email": "cible2@test.example", "password": "mauvais"})

    response = client.post(
        "/api/auth/login", json={"email": "cible2@test.example", "password": "MotDePasse123!"}
    )
    assert response.status_code == 429


def test_rate_limit_does_not_reveal_account_existence(client, db_session):
    """Le message d'erreur de connexion (hors rate limit) reste identique,
    qu'un compte existe ou non — comportement préexistant à préserver."""
    create_user(db_session, "existe@test.example", "Utilisateur")

    response_existing = client.post(
        "/api/auth/login", json={"email": "existe@test.example", "password": "mauvais"}
    )
    response_unknown = client.post(
        "/api/auth/login", json={"email": "inconnu@test.example", "password": "mauvais"}
    )
    assert response_existing.status_code == response_unknown.status_code == 401
    assert response_existing.json()["detail"] == response_unknown.json()["detail"] == "E-mail ou mot de passe incorrect."
