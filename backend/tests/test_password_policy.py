"""Tests de la politique de mot de passe (correctif #14) : complexité
(majuscule, minuscule, chiffre, caractère spécial), longueur, et interdiction
de réutiliser le mot de passe actuel lors d'un changement."""
from app.models.role import Role
from tests.conftest import auth_cookies, create_user

WEAK_PASSWORDS = {
    "sans_majuscule": "motdepasse1!",
    "sans_minuscule": "MOTDEPASSE1!",
    "sans_chiffre": "MotDePasse!!",
    "sans_special": "MotDePasse12",
    "trop_court": "Ab1!",
}

COMPLIANT_PASSWORD = "MotDePasseValide1!"


def _register_payload(email: str, password: str) -> dict:
    return {"first_name": "Test", "last_name": "Utilisateur", "email": email, "password": password}


# ============================= inscription =============================

def test_registration_rejects_weak_passwords(client, db_session):
    for label, weak_password in WEAK_PASSWORDS.items():
        response = client.post(
            "/api/auth/register", json=_register_payload(f"weak-{label}@test.example", weak_password)
        )
        assert response.status_code == 422, f"{label} aurait dû être rejeté"


def test_registration_accepts_compliant_password(client, db_session):
    response = client.post("/api/auth/register", json=_register_payload("compliant@test.example", COMPLIANT_PASSWORD))
    assert response.status_code == 201


def test_registration_rejects_password_over_72_chars(client, db_session):
    """bcrypt tronque silencieusement au-delà de 72 octets (vérifié
    empiriquement) : max_length=72 empêche la fausse impression de sécurité
    d'un mot de passe plus long dont la fin serait ignorée sans le savoir."""
    too_long = "Aa1!" * 19  # 76 caractères, composition valide, uniquement trop long
    response = client.post("/api/auth/register", json=_register_payload("toolong@test.example", too_long))
    assert response.status_code == 422

    exactly_72 = "Aa1!" * 18  # 72 caractères exactement, composition valide -> accepté
    assert len(exactly_72) == 72
    response = client.post("/api/auth/register", json=_register_payload("exactly72@test.example", exactly_72))
    assert response.status_code == 201


def test_login_password_field_not_subject_to_complexity(client, db_session):
    """La politique de complexité ne s'applique qu'à la création/au changement
    de mot de passe, jamais à la connexion elle-même (un compte existant peut
    avoir un mot de passe créé avant l'introduction de cette politique)."""
    create_user(db_session, "existing@test.example", "Utilisateur")
    response = client.post("/api/auth/login", json={"email": "existing@test.example", "password": "mauvais"})
    assert response.status_code == 401  # rejeté pour mot de passe incorrect, pas 422 de validation


# ============================= création par un manager =============================

def test_manager_user_creation_enforces_policy(client, db_session):
    create_user(db_session, "manager-pp1@test.example", "Responsable IT")
    role = db_session.query(Role).filter_by(name="Utilisateur").first()

    weak_response = client.post(
        "/api/users",
        json={
            "first_name": "Nouveau", "last_name": "Compte", "email": "weakcreated@test.example",
            "role_id": role.id, "password": "faible",
        },
        cookies=auth_cookies(client, "manager-pp1@test.example"),
    )
    assert weak_response.status_code == 422

    strong_response = client.post(
        "/api/users",
        json={
            "first_name": "Nouveau", "last_name": "Compte", "email": "strongcreated@test.example",
            "role_id": role.id, "password": COMPLIANT_PASSWORD,
        },
        cookies=auth_cookies(client, "manager-pp1@test.example"),
    )
    assert strong_response.status_code == 201


# ============================= changement de mot de passe =============================

def test_change_password_enforces_policy(client, db_session):
    create_user(db_session, "pwchange1@test.example", "Utilisateur")
    response = client.put(
        "/api/users/moi/mot-de-passe",
        json={"current_password": "MotDePasse123!", "new_password": "faible"},
        cookies=auth_cookies(client, "pwchange1@test.example"),
    )
    assert response.status_code == 422


def test_change_password_rejects_same_as_current(client, db_session):
    create_user(db_session, "pwchange2@test.example", "Utilisateur")
    response = client.put(
        "/api/users/moi/mot-de-passe",
        json={"current_password": "MotDePasse123!", "new_password": "MotDePasse123!"},
        cookies=auth_cookies(client, "pwchange2@test.example"),
    )
    assert response.status_code == 422
    assert "différent" in response.text


def test_change_password_accepts_compliant_different_password(client, db_session):
    create_user(db_session, "pwchange3@test.example", "Utilisateur")
    response = client.put(
        "/api/users/moi/mot-de-passe",
        json={"current_password": "MotDePasse123!", "new_password": COMPLIANT_PASSWORD},
        cookies=auth_cookies(client, "pwchange3@test.example"),
    )
    assert response.status_code == 200
