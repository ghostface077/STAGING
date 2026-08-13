"""
Données de démonstration (idempotent : peut être exécuté plusieurs fois sans dupliquer les données).
Toutes les données sont fictives, en français, et ne représentent aucune personne réelle.

Utilisation :
    python -m app.seed
"""
import secrets
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import (
    SLA,
    AuditLog,
    Category,
    Comment,
    Department,
    Equipment,
    KnowledgeBaseArticle,
    Notification,
    Priority,
    Role,
    SatisfactionRating,
    Status,
    Team,
    Ticket,
    TicketHistory,
    User,
)
from app.security import hash_password
from app.services.reference_service import generate_ticket_reference


def get_or_create(db: Session, model, defaults: dict | None = None, **filters):
    instance = db.query(model).filter_by(**filters).first()
    if instance:
        return instance, False
    params = {**filters, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True


def seed_roles(db: Session) -> dict[str, Role]:
    noms = {
        "Utilisateur": "Peut créer et suivre ses propres tickets.",
        "Technicien": "Traite les tickets qui lui sont assignés ou disponibles.",
        "Responsable IT": "Supervise les équipes, les SLA et les statistiques du support.",
        "Administrateur": "Gère l'ensemble des paramètres et des données de l'application.",
    }
    roles = {}
    for name, description in noms.items():
        role, _ = get_or_create(db, Role, name=name, defaults={"description": description})
        roles[name] = role
    return roles


def seed_departments(db: Session) -> dict[str, Department]:
    noms = {
        "Direction Générale": "Direction et pilotage stratégique de l'organisation.",
        "Ressources Humaines": "Gestion du personnel et des recrutements.",
        "Comptabilité": "Gestion financière et comptable.",
        "Service Informatique": "Support et infrastructure informatique.",
        "Commercial": "Ventes et relation client.",
        "Logistique": "Gestion des stocks et des livraisons.",
    }
    departments = {}
    for name, description in noms.items():
        dept, _ = get_or_create(db, Department, name=name, defaults={"description": description})
        departments[name] = dept
    return departments


def seed_categories(db: Session) -> dict[str, Category]:
    structure = {
        "Matériel": ["Ordinateur", "Imprimante", "Périphériques", "Téléphonie"],
        "Logiciel": ["Système d'exploitation", "Suite bureautique", "Logiciel métier", "Messagerie"],
        "Réseau": ["Connexion Wi-Fi", "VPN", "Accès Internet", "Partage de fichiers"],
        "Compte": ["Mot de passe", "Création de compte", "Droits d'accès"],
    }
    categories: dict[str, Category] = {}
    for parent_name, children in structure.items():
        parent, _ = get_or_create(db, Category, name=parent_name, parent_id=None)
        categories[parent_name] = parent
        for child_name in children:
            child, _ = get_or_create(db, Category, name=child_name, parent_id=parent.id)
            categories[child_name] = child
    return categories


def seed_priorities(db: Session) -> dict[str, Priority]:
    data = [
        ("Basse", 1, "Impact limité, aucune urgence."),
        ("Normale", 2, "Impact modéré sur l'activité."),
        ("Haute", 3, "Impact important, traitement rapide requis."),
        ("Critique", 4, "Blocage majeur nécessitant une intervention immédiate."),
    ]
    priorities = {}
    for name, level, description in data:
        priority, _ = get_or_create(db, Priority, name=name, defaults={"level": level, "description": description})
        priorities[name] = priority
    return priorities


def seed_statuses(db: Session) -> dict[str, Status]:
    data = {
        "Nouveau": "Ticket créé, en attente de traitement.",
        "Ouvert": "Ticket pris en charge par un technicien.",
        "En cours": "Le technicien travaille activement sur le ticket.",
        "En attente": "En attente d'une information complémentaire.",
        "Résolu": "Une solution a été apportée.",
        "Fermé": "Le ticket est clos et confirmé.",
        "Réouvert": "Le ticket a été réouvert après une résolution jugée insuffisante.",
        "Annulé": "Le ticket a été annulé.",
    }
    statuses = {}
    for name, description in data.items():
        status_obj, _ = get_or_create(db, Status, name=name, defaults={"description": description})
        statuses[name] = status_obj
    return statuses


def seed_slas(db: Session, priorities: dict[str, Priority]) -> dict[str, SLA]:
    data = [
        ("SLA Critique", "Critique", 15, 120),
        ("SLA Haute", "Haute", 30, 240),
        ("SLA Normale", "Normale", 120, 480),
        ("SLA Basse", "Basse", 240, 1440),
    ]
    slas = {}
    for name, priority_name, first_response, resolution in data:
        sla, _ = get_or_create(
            db, SLA, name=name, priority_id=priorities[priority_name].id,
            defaults={"first_response_minutes": first_response, "resolution_minutes": resolution, "is_active": True},
        )
        slas[priority_name] = sla
    return slas


def _resolve_seed_password(value: str | None) -> tuple[str, bool]:
    """Retourne (mot_de_passe, généré_aléatoirement) pour un mot de passe de seed.

    Si `value` (lu depuis une variable d'environnement SEED_*_PASSWORD) est
    fourni, il est utilisé tel quel. Sinon, un mot de passe aléatoire fort est
    généré à la volée : aucun mot de passe n'est jamais codé en dur dans le
    code source, pour aucun des quatre rôles. Ce mot de passe généré n'est
    jamais journalisé (voir seed_users) — définissez la variable correspondante
    si vous avez besoin de connaître ce mot de passe pour vous connecter.
    """
    if value:
        return value, False
    return secrets.token_urlsafe(16), True


def seed_users(db: Session, roles: dict[str, Role], departments: dict[str, Department]) -> dict[str, User]:
    # Un mot de passe par palier de rôle (SEED_ADMIN_PASSWORD, SEED_MANAGER_PASSWORD,
    # SEED_TECHNICIAN_PASSWORD, SEED_USER_PASSWORD), partagé par tous les comptes de
    # démonstration de ce rôle — comme c'était déjà le cas pour Technicien/Utilisateur.
    admin_password, admin_generated = _resolve_seed_password(settings.seed_admin_password)
    manager_password, manager_generated = _resolve_seed_password(settings.seed_manager_password)
    technician_password, technician_generated = _resolve_seed_password(settings.seed_technician_password)
    user_password, user_generated = _resolve_seed_password(settings.seed_user_password)
    generated_by_role = {
        "Administrateur": admin_generated,
        "Responsable IT": manager_generated,
        "Technicien": technician_generated,
        "Utilisateur": user_generated,
    }

    users_data = [
        # (prénom, nom, email, mot de passe, rôle, service)
        ("Amina", "Diallo", settings.seed_admin_email, admin_password, "Administrateur", "Service Informatique"),
        ("Karim", "Benali", "karim.benali@itsupport.example", manager_password, "Responsable IT", "Service Informatique"),
        ("Fatou", "Ndiaye", "fatou.ndiaye@itsupport.example", technician_password, "Technicien", "Service Informatique"),
        ("Yacine", "Mansour", "yacine.mansour@itsupport.example", technician_password, "Technicien", "Service Informatique"),
        ("Chloé", "Fontaine", "chloe.fontaine@itsupport.example", technician_password, "Technicien", "Service Informatique"),
        ("Lucas", "Moreau", "lucas.moreau@itsupport.example", user_password, "Utilisateur", "Comptabilité"),
        ("Sophie", "Lefèvre", "sophie.lefevre@itsupport.example", user_password, "Utilisateur", "Ressources Humaines"),
        ("Mehdi", "Cherif", "mehdi.cherif@itsupport.example", user_password, "Utilisateur", "Commercial"),
        ("Julie", "Bernard", "julie.bernard@itsupport.example", user_password, "Utilisateur", "Logistique"),
        ("Thomas", "Girard", "thomas.girard@itsupport.example", user_password, "Utilisateur", "Direction Générale"),
    ]

    # (rôle, email) des comptes créés avec un mot de passe généré aléatoirement.
    # Le mot de passe lui-même n'est JAMAIS retenu ici ni journalisé nulle part :
    # seule la variable d'environnement correspondante permet de le connaître.
    generated_accounts: list[tuple[str, str]] = []

    users = {}
    for first_name, last_name, email, password, role_name, dept_name in users_data:
        user, created = get_or_create(
            db, User, email=email,
            defaults={
                "role_id": roles[role_name].id,
                "department_id": departments[dept_name].id,
                "first_name": first_name,
                "last_name": last_name,
                "password_hash": hash_password(password),
                "phone": "06 00 00 00 00",
                "is_active": True,
            },
        )
        users[email] = user

        if created and generated_by_role[role_name]:
            generated_accounts.append((role_name, email))

    if generated_accounts:
        # Log volontairement dépourvu de tout mot de passe : seul le fait qu'un
        # mot de passe ait été généré est journalisé, jamais sa valeur.
        print("[seed] Mot de passe genere aleatoirement (SEED_*_PASSWORD absent) pour :")
        for role_name, email in generated_accounts:
            print(f"[seed]   - {role_name}: {email}")
        print("[seed] Definissez la variable SEED_*_PASSWORD correspondante pour connaitre/fixer ce mot de passe.")

    return users


def seed_teams(db: Session, users: dict[str, User]) -> dict[str, Team]:
    equipe_reseau, _ = get_or_create(db, Team, name="Équipe Réseau", defaults={"description": "Prise en charge des incidents réseau et connectivité."})
    equipe_support, _ = get_or_create(db, Team, name="Équipe Support Niveau 1", defaults={"description": "Support de premier niveau (matériel, logiciel, comptes)."})

    equipe_reseau.members = [users["yacine.mansour@itsupport.example"]]
    equipe_support.members = [users["fatou.ndiaye@itsupport.example"], users["chloe.fontaine@itsupport.example"]]
    db.flush()
    return {"Équipe Réseau": equipe_reseau, "Équipe Support Niveau 1": equipe_support}


def seed_equipment(db: Session, users: dict[str, User], departments: dict[str, Department]) -> list[Equipment]:
    data = [
        ("AST-0001", "Ordinateur portable", "Dell", "Latitude 5440", "SN-DL5440-001", "lucas.moreau@itsupport.example", "Comptabilité", "Windows 11 Pro"),
        ("AST-0002", "Ordinateur portable", "HP", "EliteBook 840", "SN-HP840-002", "sophie.lefevre@itsupport.example", "Ressources Humaines", "Windows 11 Pro"),
        ("AST-0003", "Ordinateur de bureau", "Lenovo", "ThinkCentre M70", "SN-LNM70-003", "mehdi.cherif@itsupport.example", "Commercial", "Windows 10 Pro"),
        ("AST-0004", "Imprimante", "Canon", "imageRUNNER 2530", "SN-CAN2530-004", None, "Logistique", None),
        ("AST-0005", "Ordinateur portable", "Apple", "MacBook Air M2", "SN-MBA-005", "thomas.girard@itsupport.example", "Direction Générale", "macOS Sonoma"),
        ("AST-0006", "Téléphone", "Samsung", "Galaxy A54", "SN-SGA54-006", "julie.bernard@itsupport.example", "Logistique", "Android 14"),
    ]
    equipments = []
    for asset_number, type_, brand, model, serial, user_email, dept_name, os in data:
        equipment, _ = get_or_create(
            db, Equipment, asset_number=asset_number,
            defaults={
                "type": type_, "brand": brand, "model": model, "serial_number": serial,
                "user_id": users[user_email].id if user_email else None,
                "department_id": departments[dept_name].id,
                "operating_system": os,
                "purchase_date": date(2024, 3, 15),
                "warranty_end_date": date(2027, 3, 15),
                "status": "En service",
            },
        )
        equipments.append(equipment)
    return equipments


def seed_tickets(
    db: Session, users: dict[str, User], categories: dict[str, Category], priorities: dict[str, Priority],
    statuses: dict[str, Status], teams: dict[str, Team], slas: dict[str, SLA], equipments: list[Equipment],
) -> None:
    if db.query(Ticket).count() > 0:
        return  # Les tickets de démonstration existent déjà

    now = datetime.now(timezone.utc)
    tickets_data = [
        {
            "title": "Impossible de se connecter au Wi-Fi du bureau",
            "description": "Depuis ce matin, mon ordinateur portable ne parvient plus à se connecter au réseau Wi-Fi de l'entreprise.",
            "requester": "sophie.lefevre@itsupport.example",
            "technician": "yacine.mansour@itsupport.example",
            "team": "Équipe Réseau",
            "category": "Connexion Wi-Fi",
            "priority": "Haute",
            "status": "En cours",
            "equipment": equipments[1],
            "age_days": 1,
        },
        {
            "title": "L'imprimante du service Logistique n'imprime plus",
            "description": "L'imprimante Canon affiche une erreur de bourrage papier qui ne se résorbe pas après redémarrage.",
            "requester": "julie.bernard@itsupport.example",
            "technician": "fatou.ndiaye@itsupport.example",
            "team": "Équipe Support Niveau 1",
            "category": "Imprimante",
            "priority": "Normale",
            "status": "Résolu",
            "equipment": equipments[3],
            "age_days": 5,
            "solution": "Remplacement du toner et nettoyage du bac d'alimentation papier. Test d'impression concluant.",
        },
        {
            "title": "Mot de passe Windows oublié",
            "description": "Je n'arrive plus à me connecter à ma session Windows, j'ai oublié mon mot de passe.",
            "requester": "mehdi.cherif@itsupport.example",
            "technician": "chloe.fontaine@itsupport.example",
            "team": "Équipe Support Niveau 1",
            "category": "Mot de passe",
            "priority": "Normale",
            "status": "Fermé",
            "equipment": equipments[2],
            "age_days": 10,
            "solution": "Réinitialisation du mot de passe et procédure de changement à la première connexion.",
        },
        {
            "title": "Demande d'installation de Microsoft Project",
            "description": "Merci d'installer Microsoft Project sur mon poste pour le suivi des plannings de projets.",
            "requester": "thomas.girard@itsupport.example",
            "technician": None,
            "team": None,
            "category": "Logiciel métier",
            "priority": "Basse",
            "status": "Nouveau",
            "equipment": equipments[4],
            "age_days": 0,
        },
        {
            "title": "Serveur de fichiers inaccessible pour toute l'équipe comptable",
            "description": "Depuis 14h, personne dans le service comptabilité ne peut accéder au partage réseau \\\\SERVEUR\\COMPTA.",
            "requester": "lucas.moreau@itsupport.example",
            "technician": "yacine.mansour@itsupport.example",
            "team": "Équipe Réseau",
            "category": "Partage de fichiers",
            "priority": "Critique",
            "status": "Ouvert",
            "equipment": None,
            "age_days": 0,
        },
        {
            "title": "Demande de création de compte pour un nouvel employé",
            "description": "Un nouveau collaborateur rejoint le service commercial lundi prochain, merci de créer ses accès.",
            "requester": "mehdi.cherif@itsupport.example",
            "technician": "fatou.ndiaye@itsupport.example",
            "team": "Équipe Support Niveau 1",
            "category": "Création de compte",
            "priority": "Normale",
            "status": "En attente",
            "equipment": None,
            "age_days": 2,
        },
    ]

    for data in tickets_data:
        created_at = now - timedelta(days=data["age_days"], hours=2)
        ticket = Ticket(
            reference=generate_ticket_reference(db),
            title=data["title"],
            description=data["description"],
            requester_id=users[data["requester"]].id,
            technician_id=users[data["technician"]].id if data["technician"] else None,
            team_id=teams[data["team"]].id if data["team"] else None,
            category_id=categories[data["category"]].id,
            priority_id=priorities[data["priority"]].id,
            status_id=statuses[data["status"]].id,
            equipment_id=data["equipment"].id if data["equipment"] else None,
            sla_id=slas[data["priority"]].id,
            solution=data.get("solution"),
            created_at=created_at,
        )
        if data["status"] in ("En cours", "Ouvert"):
            ticket.first_response_at = created_at + timedelta(minutes=20)
        if data["status"] in ("Résolu", "Fermé"):
            ticket.first_response_at = created_at + timedelta(minutes=20)
            ticket.resolved_at = created_at + timedelta(hours=3)
        if data["status"] == "Fermé":
            ticket.closed_at = created_at + timedelta(hours=6)

        db.add(ticket)
        db.flush()

        db.add(TicketHistory(ticket_id=ticket.id, user_id=ticket.requester_id, action="creation", new_value=ticket.reference))
        if ticket.technician_id:
            db.add(TicketHistory(ticket_id=ticket.id, user_id=ticket.technician_id, action="prise_en_charge", new_value=str(ticket.technician_id)))
            db.add(Comment(
                ticket_id=ticket.id, user_id=ticket.technician_id,
                content="Bonjour, je prends en charge votre demande, je reviens vers vous rapidement.",
                is_internal=False, created_at=created_at + timedelta(minutes=30),
            ))
        if ticket.solution:
            db.add(TicketHistory(ticket_id=ticket.id, user_id=ticket.technician_id, action="resolution", new_value="Résolu"))
            db.add(Comment(
                ticket_id=ticket.id, user_id=ticket.technician_id, content=ticket.solution,
                is_internal=False, created_at=ticket.resolved_at,
            ))

        if ticket.status.name == "Fermé":
            db.add(SatisfactionRating(ticket_id=ticket.id, user_id=ticket.requester_id, rating=5, comment="Merci pour la réactivité, problème résolu rapidement !"))

        db.add(Notification(
            user_id=ticket.requester_id, ticket_id=ticket.id,
            title="Ticket créé", message=f"Votre ticket {ticket.reference} a bien été enregistré.",
            type="creation_ticket", is_read=data["status"] != "Nouveau",
        ))


def seed_knowledge_base(db: Session, users: dict[str, User], categories: dict[str, Category]) -> None:
    if db.query(KnowledgeBaseArticle).count() > 0:
        return

    articles = [
        {
            "title": "Comment résoudre un problème de connexion Wi-Fi ?",
            "category": "Connexion Wi-Fi",
            "content": (
                "1. Vérifiez que le Wi-Fi est bien activé sur votre appareil.\n"
                "2. Redémarrez votre carte réseau ou votre ordinateur.\n"
                "3. Vérifiez que vous êtes connecté au bon réseau (nom du réseau de l'entreprise).\n"
                "4. Vérifiez la configuration IP (adresse obtenue automatiquement).\n"
                "5. Si le problème persiste, testez avec un câble Ethernet et contactez le support."
            ),
        },
        {
            "title": "Comment réinitialiser mon mot de passe Windows ?",
            "category": "Mot de passe",
            "content": (
                "1. Contactez le support informatique en précisant votre nom d'utilisateur.\n"
                "2. Un technicien procédera à la réinitialisation depuis l'annuaire de l'entreprise.\n"
                "3. Vous recevrez un mot de passe temporaire à changer dès la première connexion.\n"
                "4. Choisissez un nouveau mot de passe respectant la politique de sécurité (12 caractères minimum)."
            ),
        },
        {
            "title": "Que faire en cas de bourrage papier sur l'imprimante ?",
            "category": "Imprimante",
            "content": (
                "1. Éteignez l'imprimante avant toute intervention.\n"
                "2. Ouvrez délicatement le capot d'accès au papier.\n"
                "3. Retirez la feuille coincée sans la déchirer.\n"
                "4. Refermez le capot et rallumez l'imprimante.\n"
                "5. Lancez une page de test. Si l'incident se reproduit, ouvrez un ticket."
            ),
        },
        {
            "title": "Comment demander l'installation d'un nouveau logiciel ?",
            "category": "Logiciel métier",
            "content": (
                "1. Créez un ticket dans la catégorie « Logiciel métier ».\n"
                "2. Précisez le nom, la version et la justification métier du logiciel souhaité.\n"
                "3. Votre demande sera étudiée puis validée par le Responsable IT.\n"
                "4. L'installation est ensuite planifiée avec un technicien."
            ),
        },
    ]
    for article in articles:
        db.add(KnowledgeBaseArticle(
            category_id=categories[article["category"]].id,
            author_id=users["fatou.ndiaye@itsupport.example"].id,
            title=article["title"],
            content=article["content"],
            status="Publié",
            views=12,
        ))


def run_seed() -> None:
    # Crée les tables si elles n'existent pas encore (filet de sécurité en complément d'Alembic)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        roles = seed_roles(db)
        departments = seed_departments(db)
        categories = seed_categories(db)
        priorities = seed_priorities(db)
        statuses = seed_statuses(db)
        slas = seed_slas(db, priorities)
        users = seed_users(db, roles, departments)
        teams = seed_teams(db, users)
        equipments = seed_equipment(db, users, departments)
        seed_tickets(db, users, categories, priorities, statuses, teams, slas, equipments)
        seed_knowledge_base(db, users, categories)

        db.add(AuditLog(user_id=users[settings.seed_admin_email].id, action="initialisation", entity_type="systeme", entity_id=None))
        db.commit()
        print("✅ Données de démonstration initialisées avec succès.")
    except Exception as exc:  # pragma: no cover
        db.rollback()
        print(f"❌ Erreur lors de l'initialisation des données de démonstration : {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
