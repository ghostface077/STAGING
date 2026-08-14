"""Tests de la pagination serveur (correctif #07) sur /api/tickets, /api/users,
/api/equipment et /api/knowledge-base."""
from app.models.category import Category
from app.models.equipment import Equipment
from app.models.knowledge_base import KB_STATUS_PUBLIE, KnowledgeBaseArticle
from app.models.priority import Priority
from tests.conftest import auth_cookies, create_user


def _ticket_payload(db_session, title="Ticket de test"):
    category = db_session.query(Category).first()
    priority = db_session.query(Priority).filter_by(name="Normale").first()
    return {
        "title": title,
        "description": "Description du ticket.",
        "category_id": category.id,
        "priority_id": priority.id,
    }


def _create_tickets(client, db_session, requester_email, count, title_prefix="Ticket numero"):
    return [
        client.post(
            "/api/tickets", json=_ticket_payload(db_session, f"{title_prefix} {i}"),
            cookies=auth_cookies(client, requester_email),
        ).json()
        for i in range(count)
    ]


# ============================= /api/tickets =============================

def test_tickets_page_1_and_page_2_are_distinct(client, db_session):
    create_user(db_session, "pag1@test.example", "Responsable IT")
    create_user(db_session, "req-pag1@test.example", "Utilisateur")
    _create_tickets(client, db_session, "req-pag1@test.example", 5)

    page1 = client.get(
        "/api/tickets", params={"page": 1, "page_size": 2}, cookies=auth_cookies(client, "pag1@test.example")
    ).json()
    page2 = client.get(
        "/api/tickets", params={"page": 2, "page_size": 2}, cookies=auth_cookies(client, "pag1@test.example")
    ).json()

    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    assert {t["id"] for t in page1["items"]}.isdisjoint({t["id"] for t in page2["items"]})
    assert page1["total"] == page2["total"] == 5
    assert page1["pages"] == page2["pages"] == 3  # ceil(5 / 2)
    assert page1["page"] == 1 and page2["page"] == 2


def test_tickets_custom_page_size(client, db_session):
    create_user(db_session, "pag2@test.example", "Responsable IT")
    create_user(db_session, "req-pag2@test.example", "Utilisateur")
    _create_tickets(client, db_session, "req-pag2@test.example", 7)

    body = client.get(
        "/api/tickets", params={"page": 1, "page_size": 5}, cookies=auth_cookies(client, "pag2@test.example")
    ).json()
    assert len(body["items"]) == 5
    assert body["page_size"] == 5
    assert body["total"] == 7
    assert body["pages"] == 2


def test_tickets_default_page_and_page_size(client, db_session):
    create_user(db_session, "pag3@test.example", "Responsable IT")
    body = client.get("/api/tickets", cookies=auth_cookies(client, "pag3@test.example")).json()
    assert body["page"] == 1
    assert body["page_size"] == 20


def test_tickets_page_size_over_max_is_rejected(client, db_session):
    create_user(db_session, "pag4@test.example", "Responsable IT")
    response = client.get(
        "/api/tickets", params={"page_size": 101}, cookies=auth_cookies(client, "pag4@test.example")
    )
    assert response.status_code == 422


def test_tickets_page_below_one_is_rejected(client, db_session):
    create_user(db_session, "pag4b@test.example", "Responsable IT")
    response = client.get("/api/tickets", params={"page": 0}, cookies=auth_cookies(client, "pag4b@test.example"))
    assert response.status_code == 422


def test_tickets_filters_combined_with_pagination(client, db_session):
    """Les filtres existants (recherche texte) restent appliqués avant la pagination."""
    create_user(db_session, "pag5@test.example", "Responsable IT")
    create_user(db_session, "req-pag5@test.example", "Utilisateur")
    _create_tickets(client, db_session, "req-pag5@test.example", 3, title_prefix="Recherchable")
    client.post(
        "/api/tickets", json=_ticket_payload(db_session, "Sujet totalement différent"),
        cookies=auth_cookies(client, "req-pag5@test.example"),
    )

    body = client.get(
        "/api/tickets", params={"search": "Recherchable", "page": 1, "page_size": 20},
        cookies=auth_cookies(client, "pag5@test.example"),
    ).json()
    assert body["total"] == 3
    assert all("recherchable" in t["title"].lower() for t in body["items"])


def test_tickets_pagination_does_not_bypass_role_scoping(client, db_session):
    """Non-régression permissions : la pagination ne permet pas à un Utilisateur
    de voir les tickets d'un autre, quelle que soit la page demandée."""
    create_user(db_session, "proprio-pag@test.example", "Utilisateur")
    create_user(db_session, "intrus-pag@test.example", "Utilisateur")
    _create_tickets(client, db_session, "proprio-pag@test.example", 3)

    body = client.get(
        "/api/tickets", params={"page": 1, "page_size": 20}, cookies=auth_cookies(client, "intrus-pag@test.example")
    ).json()
    assert body["total"] == 0
    assert body["items"] == []


# ============================= /api/users =============================

def test_users_pagination_basic(client, db_session):
    create_user(db_session, "manager-pag@test.example", "Responsable IT")
    for i in range(3):
        create_user(db_session, f"userpag{i}@test.example", "Utilisateur")

    response = client.get(
        "/api/users", params={"page": 1, "page_size": 2}, cookies=auth_cookies(client, "manager-pag@test.example")
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] >= 4  # au moins le manager + les 3 comptes créés
    assert body["page_size"] == 2
    assert body["pages"] >= 2


def test_users_pagination_permissions_unchanged(client, db_session):
    """Non-régression : require_manager toujours appliqué avec la pagination."""
    create_user(db_session, "simple-pag@test.example", "Utilisateur")
    response = client.get("/api/users", params={"page": 1}, cookies=auth_cookies(client, "simple-pag@test.example"))
    assert response.status_code == 403


def test_users_page_size_over_max_is_rejected(client, db_session):
    create_user(db_session, "manager-pag2@test.example", "Responsable IT")
    response = client.get(
        "/api/users", params={"page_size": 250}, cookies=auth_cookies(client, "manager-pag2@test.example")
    )
    assert response.status_code == 422


# ============================= /api/equipment =============================

def test_equipment_pagination_basic(client, db_session):
    create_user(db_session, "eq-manager@test.example", "Responsable IT")
    for i in range(3):
        db_session.add(Equipment(asset_number=f"AST-PAG-{i}", type="Ordinateur", brand="Dell", model="X"))
    db_session.commit()

    response = client.get(
        "/api/equipment", params={"page": 1, "page_size": 2}, cookies=auth_cookies(client, "eq-manager@test.example")
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["pages"] == 2


def test_equipment_pagination_permissions_unchanged(client, db_session):
    """Non-régression : un simple utilisateur ne voit toujours que son propre matériel, paginé."""
    user = create_user(db_session, "eq-user@test.example", "Utilisateur")
    db_session.add(Equipment(asset_number="AST-MINE-1", type="Ordinateur", brand="HP", model="Y", user_id=user.id))
    db_session.add(Equipment(asset_number="AST-OTHER-1", type="Ordinateur", brand="HP", model="Z"))
    db_session.commit()

    response = client.get("/api/equipment", cookies=auth_cookies(client, "eq-user@test.example"))
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["asset_number"] == "AST-MINE-1"


# ============================= /api/knowledge-base =============================

def test_knowledge_base_pagination_basic(client, db_session):
    create_user(db_session, "kb-user@test.example", "Utilisateur")
    for i in range(3):
        db_session.add(KnowledgeBaseArticle(title=f"Article {i}", content="Contenu de l'article.", status=KB_STATUS_PUBLIE))
    db_session.commit()

    response = client.get(
        "/api/knowledge-base", params={"page": 1, "page_size": 2}, cookies=auth_cookies(client, "kb-user@test.example")
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["pages"] == 2


def test_knowledge_base_pagination_permissions_unchanged(client, db_session):
    """Non-régression : un utilisateur non-staff ne voit toujours pas les brouillons, paginé."""
    create_user(db_session, "kb-user2@test.example", "Utilisateur")
    db_session.add(KnowledgeBaseArticle(title="Article publié", content="Visible.", status=KB_STATUS_PUBLIE))
    db_session.add(KnowledgeBaseArticle(title="Article brouillon", content="Invisible.", status="Brouillon"))
    db_session.commit()

    response = client.get("/api/knowledge-base", cookies=auth_cookies(client, "kb-user2@test.example"))
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Article publié"
