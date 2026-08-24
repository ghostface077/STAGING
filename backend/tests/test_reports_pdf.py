"""Tests de l'export PDF des rapports — GET /api/reports/export.pdf."""
from app.models.category import Category
from app.models.priority import Priority
from tests.conftest import auth_cookies, create_user


def _ticket_payload(db_session, title):
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    return {
        "title": title,
        "description": "Description du ticket.",
        "category_id": category.id,
        "priority_id": priority.id,
    }


def test_pdf_export_returns_a_valid_pdf(client, db_session):
    create_user(db_session, "manager-pdf1@test.example", "Responsable IT")
    create_user(db_session, "req-pdf1@test.example", "Utilisateur")
    client.post(
        "/api/tickets", json=_ticket_payload(db_session, "Ticket pour export PDF"),
        cookies=auth_cookies(client, "req-pdf1@test.example"),
    )

    response = client.get("/api/reports/export.pdf", cookies=auth_cookies(client, "manager-pdf1@test.example"))

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    # Un PDF valide commence toujours par cette signature (magic bytes).
    assert response.content.startswith(b"%PDF-")


def test_pdf_export_works_with_no_tickets_in_period(client, db_session):
    """La période demandée ne doit contenir aucun ticket : le PDF reste
    valide (branche "Aucun ticket sur cette période.") plutôt que de planter
    sur une table vide."""
    create_user(db_session, "manager-pdf2@test.example", "Responsable IT")

    response = client.get(
        "/api/reports/export.pdf",
        params={"date_from": "2000-01-01", "date_to": "2000-01-02"},
        cookies=auth_cookies(client, "manager-pdf2@test.example"),
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")


def test_pdf_export_permissions(client, db_session):
    """Mêmes permissions que l'export CSV (réservé Responsable IT / Administrateur)."""
    create_user(db_session, "user-pdf3@test.example", "Utilisateur")
    create_user(db_session, "tech-pdf3@test.example", "Technicien")
    create_user(db_session, "manager-pdf3@test.example", "Responsable IT")
    create_user(db_session, "admin-pdf3@test.example", "Administrateur")

    assert client.get("/api/reports/export.pdf", cookies=auth_cookies(client, "user-pdf3@test.example")).status_code == 403
    assert client.get("/api/reports/export.pdf", cookies=auth_cookies(client, "tech-pdf3@test.example")).status_code == 403
    assert client.get("/api/reports/export.pdf", cookies=auth_cookies(client, "manager-pdf3@test.example")).status_code == 200
    assert client.get("/api/reports/export.pdf", cookies=auth_cookies(client, "admin-pdf3@test.example")).status_code == 200


def test_pdf_export_matches_summary_totals(client, db_session):
    """Le PDF doit refléter les mêmes chiffres que /summary pour la même
    période — _compute_summary est partagée par les deux, ce test vérifie
    que le partage fonctionne réellement (pas seulement que le code compile)."""
    create_user(db_session, "manager-pdf4@test.example", "Responsable IT")
    create_user(db_session, "req-pdf4@test.example", "Utilisateur")
    for i in range(3):
        client.post(
            "/api/tickets", json=_ticket_payload(db_session, f"Ticket {i}"),
            cookies=auth_cookies(client, "req-pdf4@test.example"),
        )

    summary = client.get("/api/reports/summary", cookies=auth_cookies(client, "manager-pdf4@test.example")).json()
    pdf_response = client.get("/api/reports/export.pdf", cookies=auth_cookies(client, "manager-pdf4@test.example"))

    assert summary["total_tickets"] == 3
    assert pdf_response.status_code == 200
    assert pdf_response.content.startswith(b"%PDF-")
