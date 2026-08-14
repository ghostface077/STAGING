"""Tests du journal opérationnel/sécurité (correctif #10) : échecs de connexion,
requêtes, erreurs de validation, quota dépassé, exceptions non gérées."""
import asyncio
import logging

import pytest
from starlette.requests import Request

from app.main import unhandled_exception_handler
from app.rate_limit import limiter
from tests.conftest import auth_cookies, create_user


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


def test_failed_login_is_logged_with_email_but_never_password(client, db_session, caplog):
    create_user(db_session, "logtest1@test.example", "Utilisateur")
    with caplog.at_level(logging.WARNING, logger="app.auth"):
        response = client.post(
            "/api/auth/login", json={"email": "logtest1@test.example", "password": "MauvaisMotDePasse!"}
        )
    assert response.status_code == 401
    messages = "\n".join(r.message for r in caplog.records)
    assert "logtest1@test.example" in messages
    assert "MauvaisMotDePasse!" not in messages


def test_disabled_account_login_attempt_is_logged(client, db_session, caplog):
    user = create_user(db_session, "logtest2@test.example", "Utilisateur")
    user.is_active = False
    db_session.commit()

    with caplog.at_level(logging.WARNING, logger="app.auth"):
        response = client.post(
            "/api/auth/login", json={"email": "logtest2@test.example", "password": "MotDePasse123!"}
        )
    assert response.status_code == 403
    messages = "\n".join(r.message for r in caplog.records)
    assert "désactivé" in messages
    assert "logtest2@test.example" in messages


def test_successful_login_does_not_log_a_failure_warning(client, db_session, caplog):
    create_user(db_session, "logtest3@test.example", "Utilisateur")
    with caplog.at_level(logging.WARNING, logger="app.auth"):
        response = client.post(
            "/api/auth/login", json={"email": "logtest3@test.example", "password": "MotDePasse123!"}
        )
    assert response.status_code == 200
    assert len(caplog.records) == 0


def test_request_is_logged_with_method_path_status(client, db_session, caplog):
    with caplog.at_level(logging.INFO, logger="app.requests"):
        response = client.get("/api/health")
    assert response.status_code == 200
    assert any(
        r.name == "app.requests" and "GET" in r.message and "/api/health" in r.message and "200" in r.message
        for r in caplog.records
    )


def test_authenticated_request_is_logged_with_user_id(client, db_session, caplog):
    user = create_user(db_session, "logtest4@test.example", "Utilisateur")
    with caplog.at_level(logging.INFO, logger="app.requests"):
        response = client.get("/api/auth/me", cookies=auth_cookies(client, "logtest4@test.example"))
    assert response.status_code == 200
    assert any(f"user={user.id}" in r.message for r in caplog.records if r.name == "app.requests")


def test_validation_error_is_logged(client, db_session, caplog):
    create_user(db_session, "logtest5@test.example", "Utilisateur")
    with caplog.at_level(logging.WARNING):
        response = client.post(
            "/api/tickets", json={"title": "x"}, cookies=auth_cookies(client, "logtest5@test.example")
        )
    assert response.status_code == 422
    assert any("Validation invalide" in r.message for r in caplog.records)


def test_rate_limit_exceeded_is_logged(client, db_session, caplog):
    create_user(db_session, "logtest6@test.example", "Utilisateur")
    with caplog.at_level(logging.WARNING):
        for _ in range(6):
            response = client.post(
                "/api/auth/login", json={"email": "logtest6@test.example", "password": "MauvaisMotDePasse!"}
            )
    assert response.status_code == 429
    assert any("Quota de requêtes dépassé" in r.message for r in caplog.records)


def test_unhandled_exception_is_logged_and_never_leaked_to_client(caplog):
    """Le gestionnaire générique journalise la trace complète côté serveur,
    mais ne renvoie jamais le détail de l'exception dans la réponse HTTP."""
    scope = {"type": "http", "method": "GET", "path": "/api/route-inexistante-pour-le-test", "headers": []}
    request = Request(scope)

    with caplog.at_level(logging.ERROR):
        response = asyncio.run(unhandled_exception_handler(request, ValueError("détail interne sensible")))

    assert response.status_code == 500
    assert b"detail interne sensible" not in response.body.lower()
    assert b"d\xc3\xa9tail interne sensible" not in response.body  # jamais dans le corps renvoyé au client
    assert any("Erreur non gérée" in r.message for r in caplog.records)
