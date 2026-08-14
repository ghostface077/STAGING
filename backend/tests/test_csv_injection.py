"""Tests de la protection contre l'injection CSV / Formula Injection
(CWE-1236) sur GET /api/reports/export.csv — correctif #11."""
import csv
import io

from app.models.category import Category
from app.models.priority import Priority
from tests.conftest import auth_headers, create_user


def _ticket_payload(db_session, title):
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    return {
        "title": title,
        "description": "Description du ticket.",
        "category_id": category.id,
        "priority_id": priority.id,
    }


def _create_ticket(client, db_session, requester_email, title):
    return client.post(
        "/api/tickets", json=_ticket_payload(db_session, title), headers=auth_headers(client, requester_email)
    ).json()


def _export_rows(client, manager_email):
    response = client.get("/api/reports/export.csv", headers=auth_headers(client, manager_email))
    assert response.status_code == 200
    reader = csv.reader(io.StringIO(response.text), delimiter=";")
    rows = list(reader)
    return rows[0], rows[1:]  # (en-tête, lignes de données)


# ============================= titre du ticket =============================

def test_csv_export_sanitizes_formula_title(client, db_session):
    create_user(db_session, "manager-csv1@test.example", "Responsable IT")
    create_user(db_session, "req-csv1@test.example", "Utilisateur")
    _create_ticket(client, db_session, "req-csv1@test.example", "=SUM(A1:A2)")

    _, rows = _export_rows(client, "manager-csv1@test.example")
    titles = [row[1] for row in rows]
    assert "'=SUM(A1:A2)" in titles
    assert "=SUM(A1:A2)" not in titles


# ============================= nom du demandeur =============================

def test_csv_export_sanitizes_formula_requester_name(client, db_session):
    create_user(db_session, "manager-csv2@test.example", "Responsable IT")
    requester = create_user(db_session, "req-csv2@test.example", "Utilisateur")
    requester.first_name = "=cmd|' /C calc'!A0"
    db_session.commit()
    _create_ticket(client, db_session, "req-csv2@test.example", "Ticket normal csv2")

    _, rows = _export_rows(client, "manager-csv2@test.example")
    demandeurs = [row[5] for row in rows]
    assert any(name.startswith("'=cmd|") for name in demandeurs)
    assert not any(name.startswith("=cmd|") for name in demandeurs)


# ============================= nom du technicien =============================

def test_csv_export_sanitizes_formula_technician_name(client, db_session):
    create_user(db_session, "manager-csv3@test.example", "Responsable IT")
    technicien = create_user(db_session, "tech-csv3@test.example", "Technicien")
    technicien.first_name = "=HYPERLINK(\"http://evil.example\")"
    db_session.commit()
    create_user(db_session, "req-csv3@test.example", "Utilisateur")
    ticket = _create_ticket(client, db_session, "req-csv3@test.example", "Ticket normal csv3")
    client.post(
        f"/api/tickets/{ticket['id']}/assign", json={"technician_id": technicien.id},
        headers=auth_headers(client, "tech-csv3@test.example"),
    )

    _, rows = _export_rows(client, "manager-csv3@test.example")
    techniciens = [row[6] for row in rows]
    assert any(name.startswith("'=HYPERLINK") for name in techniciens)
    assert not any(name.startswith("=HYPERLINK") for name in techniciens)


# ============================= autres préfixes dangereux =============================

def test_csv_export_sanitizes_plus_prefix(client, db_session):
    create_user(db_session, "manager-csv4@test.example", "Responsable IT")
    create_user(db_session, "req-csv4@test.example", "Utilisateur")
    _create_ticket(client, db_session, "req-csv4@test.example", "+123 formule")

    _, rows = _export_rows(client, "manager-csv4@test.example")
    assert "'+123 formule" in [row[1] for row in rows]


def test_csv_export_sanitizes_minus_prefix(client, db_session):
    create_user(db_session, "manager-csv5@test.example", "Responsable IT")
    create_user(db_session, "req-csv5@test.example", "Utilisateur")
    _create_ticket(client, db_session, "req-csv5@test.example", "-123 formule")

    _, rows = _export_rows(client, "manager-csv5@test.example")
    assert "'-123 formule" in [row[1] for row in rows]


def test_csv_export_sanitizes_at_prefix(client, db_session):
    create_user(db_session, "manager-csv6@test.example", "Responsable IT")
    create_user(db_session, "req-csv6@test.example", "Utilisateur")
    _create_ticket(client, db_session, "req-csv6@test.example", "@test formule")

    _, rows = _export_rows(client, "manager-csv6@test.example")
    assert "'@test formule" in [row[1] for row in rows]


def test_csv_export_sanitizes_tab_prefix(client, db_session):
    create_user(db_session, "manager-csv7@test.example", "Responsable IT")
    create_user(db_session, "req-csv7@test.example", "Utilisateur")
    _create_ticket(client, db_session, "req-csv7@test.example", "\tmalicious tab")

    _, rows = _export_rows(client, "manager-csv7@test.example")
    assert "'\tmalicious tab" in [row[1] for row in rows]


def test_csv_export_sanitizes_carriage_return_prefix(client, db_session):
    create_user(db_session, "manager-csv8@test.example", "Responsable IT")
    create_user(db_session, "req-csv8@test.example", "Utilisateur")
    _create_ticket(client, db_session, "req-csv8@test.example", "\rmalicious cr")

    _, rows = _export_rows(client, "manager-csv8@test.example")
    assert "'\rmalicious cr" in [row[1] for row in rows]


# ============================= contenu légitime inchangé =============================

def test_csv_export_keeps_normal_text_unchanged(client, db_session):
    create_user(db_session, "manager-csv9@test.example", "Responsable IT")
    create_user(db_session, "req-csv9@test.example", "Utilisateur")
    title = "Écran qui reste noir : câble déconnecté, 2 tentatives, \"urgent\" !"
    _create_ticket(client, db_session, "req-csv9@test.example", title)

    _, rows = _export_rows(client, "manager-csv9@test.example")
    titles = [row[1] for row in rows]
    assert title in titles  # strictement inchangé, aucune apostrophe ajoutée


# ============================= permissions inchangées =============================

def test_csv_export_permissions_unchanged(client, db_session):
    create_user(db_session, "user-csv10@test.example", "Utilisateur")
    create_user(db_session, "manager-csv10@test.example", "Responsable IT")
    create_user(db_session, "admin-csv10@test.example", "Administrateur")

    assert client.get("/api/reports/export.csv", headers=auth_headers(client, "user-csv10@test.example")).status_code == 403
    assert client.get("/api/reports/export.csv", headers=auth_headers(client, "manager-csv10@test.example")).status_code == 200
    assert client.get("/api/reports/export.csv", headers=auth_headers(client, "admin-csv10@test.example")).status_code == 200
