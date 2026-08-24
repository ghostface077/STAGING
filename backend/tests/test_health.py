"""Tests des endpoints de santé : /api/health (liveness) et /api/health/db
(readiness base de données), volontairement séparés — voir leurs docstrings
dans app/main.py."""
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_health_liveness_does_not_touch_the_database(client):
    """/api/health répond même sans jamais interroger la base : c'est
    l'endpoint que Render doit utiliser pour ses décisions de redémarrage."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_db_reports_reachable_when_database_responds(client):
    response = client.get("/api/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


class _BrokenSession:
    """Simule une session dont la requête échoue (ex. Neon injoignable),
    sans passer par un vrai driver réseau."""

    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def test_health_db_reports_degraded_without_leaking_details_on_query_failure(client):
    """Le cas que health_check_db est censé gérer lui-même (son try/except) :
    la connexion s'obtient mais la requête échoue. Le client ne doit recevoir
    qu'un statut degraded/503 — jamais le message d'erreur brut ni DATABASE_URL."""
    def broken_get_db():
        yield _BrokenSession()

    app.dependency_overrides[get_db] = broken_get_db
    try:
        response = client.get("/api/health/db")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    body = response.json()
    assert body == {"status": "degraded", "database": "unreachable"}
    assert "connection refused" not in str(body)
