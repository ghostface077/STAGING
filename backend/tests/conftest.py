"""Configuration des tests : base de données SQLite en mémoire isolée par test."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.rate_limit import limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Réinitialise le compteur du rate limiter avant/après chaque test : son
    stockage (en mémoire) persiste sinon d'un test à l'autre dans le même
    processus pytest, ce qui pourrait faire échouer des tests de connexion
    sans rapport avec le test de rate limiting lui-même."""
    limiter.reset()
    yield
    limiter.reset()
from app.models.category import Category
from app.models.priority import Priority
from app.models.role import (
    ROLE_ADMINISTRATEUR,
    ROLE_RESPONSABLE_IT,
    ROLE_TECHNICIEN,
    ROLE_UTILISATEUR,
    Role,
)
from app.models.sla import SLA
from app.models.status import Status
from app.models.user import User
from app.security import hash_password

from fastapi.testclient import TestClient


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Données de référence minimales nécessaires aux tests
    for name in [ROLE_UTILISATEUR, ROLE_TECHNICIEN, ROLE_RESPONSABLE_IT, ROLE_ADMINISTRATEUR]:
        session.add(Role(name=name))
    for name, description in [("Nouveau", ""), ("Ouvert", ""), ("En cours", ""), ("Résolu", ""), ("Fermé", ""), ("Réouvert", "")]:
        session.add(Status(name=name, description=description))
    for name, level in [("Basse", 1), ("Normale", 2), ("Haute", 3), ("Critique", 4)]:
        session.add(Priority(name=name, level=level))
    session.add(Category(name="Matériel"))
    session.commit()

    priority_normale = session.query(Priority).filter_by(name="Normale").first()
    session.add(SLA(name="SLA Normale", priority_id=priority_normale.id, first_response_minutes=120, resolution_minutes=480))
    session.commit()

    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_user(db_session, email: str, role_name: str, password: str = "MotDePasse123!") -> User:
    role = db_session.query(Role).filter_by(name=role_name).first()
    user = User(
        role_id=role.id, first_name="Prénom", last_name="Nom", email=email,
        password_hash=hash_password(password), is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_cookies(client, email: str, password: str = "MotDePasse123!") -> dict:
    """Retourne les cookies d'authentification pour `email` (correctif #12 :
    l'API pose désormais des cookies httpOnly plutôt que de renvoyer le jeton
    dans le corps de la réponse), en réutilisant la session déjà obtenue sur ce
    `client` si un appel précédent l'a déjà connecté.

    Le cache est indispensable depuis l'introduction du rate limiting sur
    /api/auth/login (correctif #04) : plusieurs tests simulent des scénarios
    impliquant 4-5 utilisateurs différents et appelaient jusque-là `login` à
    chaque `auth_cookies(...)`, ce qui pouvait dépasser le quota (5/minute)
    en un seul test — alors qu'une session réelle ne s'authentifie qu'une
    seule fois. Ce cache reproduit ce comportement réaliste sans affaiblir
    la protection (les tests dédiés au rate limiting, eux, appellent
    directement `/api/auth/login`, sans passer par ce cache).

    Le jar de cookies persistant du `client` est systématiquement vidé après
    chaque connexion : sans cela, les cookies d'un utilisateur resteraient
    attachés implicitement à toute requête ultérieure sur le même `client`
    (y compris des appels volontairement non authentifiés, ou authentifiés
    comme un autre utilisateur dans le même test) — le seul moyen valide de
    s'authentifier dans les tests est de passer explicitement
    `cookies=auth_cookies(client, email)` à chaque appel, à l'identique du
    fonctionnement précédent avec `headers=auth_headers(...)`."""
    cache: dict[tuple[str, str], dict[str, str]] = getattr(client, "_auth_cookie_cache", None) or {}
    client._auth_cookie_cache = cache

    key = (email, password)
    if key not in cache:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        cache[key] = dict(response.cookies)
        client.cookies.clear()
    return cache[key]
