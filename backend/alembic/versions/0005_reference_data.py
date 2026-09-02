"""Données de référence indispensables : rôles, départements, catégories,
priorités, statuts, SLA.

Contrairement à app/seed.py (comptes/tickets/équipements fictifs de
démonstration, volontairement bloqué en production par
app/config.py::_validate_production_secrets), ces données ne sont PAS de la
donnée de démo : ce sont des pré-requis fonctionnels de l'application dans
TOUS les environnements. Avant cette migration, une base de production
fraîchement migrée n'avait aucun rôle — même l'auto-inscription (qui a
besoin du rôle "Utilisateur") échouait avec une 500 ("Le rôle par défaut est
introuvable"), alors que les conteneurs restaient `healthy` (aucun
healthcheck n'exerce ce chemin).

Idempotent vis-à-vis de app/seed.py : mêmes noms exacts pour roles/
departments/priorities/statuses/categories, retrouvés par get_or_create en
développement (aucun doublon).

Revision ID: 0005_reference_data
Revises: 0004_refresh_tokens
Create Date: 2026-09-02 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_reference_data"
down_revision: Union[str, None] = "0004_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLES = [
    ("Utilisateur", "Peut créer et suivre ses propres tickets."),
    ("Technicien", "Traite les tickets qui lui sont assignés ou disponibles."),
    ("Responsable IT", "Supervise les équipes, les SLA et les statistiques du support."),
    ("Administrateur", "Gère l'ensemble des paramètres et des données de l'application."),
]

DEPARTMENTS = [
    ("Direction Générale", "Direction et pilotage stratégique de l'organisation."),
    ("Ressources Humaines", "Gestion du personnel et des recrutements."),
    ("Comptabilité", "Gestion financière et comptable."),
    ("Service Informatique", "Support et infrastructure informatique."),
    ("Commercial", "Ventes et relation client."),
    ("Logistique", "Gestion des stocks et des livraisons."),
]

CATEGORIES = {
    "Matériel": ["Ordinateur", "Imprimante", "Périphériques", "Téléphonie"],
    "Logiciel": ["Système d'exploitation", "Suite bureautique", "Logiciel métier", "Messagerie"],
    "Réseau": ["Connexion Wi-Fi", "VPN", "Accès Internet", "Partage de fichiers"],
    "Compte": ["Mot de passe", "Création de compte", "Droits d'accès"],
}

PRIORITIES = [
    ("Basse", 1, "Impact limité, aucune urgence."),
    ("Normale", 2, "Impact modéré sur l'activité."),
    ("Haute", 3, "Impact important, traitement rapide requis."),
    ("Critique", 4, "Blocage majeur nécessitant une intervention immédiate."),
]

STATUSES = [
    ("Nouveau", "Ticket créé, en attente de traitement."),
    ("Ouvert", "Ticket pris en charge par un technicien."),
    ("En cours", "Le technicien travaille activement sur le ticket."),
    ("En attente", "En attente d'une information complémentaire."),
    ("Résolu", "Une solution a été apportée."),
    ("Fermé", "Le ticket est clos et confirmé."),
    ("Réouvert", "Le ticket a été réouvert après une résolution jugée insuffisante."),
    ("Annulé", "Le ticket a été annulé."),
]

# (nom, priorité associée, première réponse en minutes, résolution en minutes)
SLAS = [
    ("SLA Critique", "Critique", 15, 120),
    ("SLA Haute", "Haute", 30, 240),
    ("SLA Normale", "Normale", 120, 480),
    ("SLA Basse", "Basse", 240, 1440),
]

roles_table = sa.table("roles", sa.column("name", sa.String), sa.column("description", sa.Text))
departments_table = sa.table("departments", sa.column("name", sa.String), sa.column("description", sa.Text))
priorities_table = sa.table(
    "priorities", sa.column("name", sa.String), sa.column("level", sa.Integer), sa.column("description", sa.Text)
)
statuses_table = sa.table("statuses", sa.column("name", sa.String), sa.column("description", sa.Text))


def upgrade() -> None:
    bind = op.get_bind()

    # Idempotent au niveau de la migration entière (et pas seulement des lignes
    # individuelles, contrairement à seed.py::get_or_create) : si le rôle
    # "Utilisateur" existe déjà, on considère que toute cette donnée de
    # référence a déjà été insérée (par un environnement de dev déjà seedé
    # avant cette migration, ou par une exécution précédente) et on ne
    # retente rien. Sans ce garde-fou, un ré-application sur une base déjà
    # peuplée échouerait sur "roles_name_key" (contrainte unique) et, pour les
    # catégories (sans contrainte unique sur name), dupliquerait silencieusement
    # les lignes à chaque nouvelle exécution.
    already_present = bind.execute(sa.text("SELECT 1 FROM roles WHERE name = :name"), {"name": "Utilisateur"}).first()
    if already_present:
        return

    op.bulk_insert(roles_table, [{"name": name, "description": desc} for name, desc in ROLES])
    op.bulk_insert(departments_table, [{"name": name, "description": desc} for name, desc in DEPARTMENTS])
    op.bulk_insert(priorities_table, [{"name": name, "level": level, "description": desc} for name, level, desc in PRIORITIES])
    op.bulk_insert(statuses_table, [{"name": name, "description": desc} for name, desc in STATUSES])

    # Catégories parentes puis enfants : parent_id a besoin de l'id généré par
    # la parente, donc un aller-retour SQL (RETURNING) au lieu d'un bulk_insert.
    parent_ids: dict[str, int] = {}
    for parent_name in CATEGORIES:
        parent_ids[parent_name] = bind.execute(
            sa.text("INSERT INTO categories (name) VALUES (:name) RETURNING id"), {"name": parent_name}
        ).scalar_one()
    for parent_name, children in CATEGORIES.items():
        for child_name in children:
            bind.execute(
                sa.text("INSERT INTO categories (name, parent_id) VALUES (:name, :parent_id)"),
                {"name": child_name, "parent_id": parent_ids[parent_name]},
            )

    # slas.priority_id référence priorities.id : relire les ids par nom plutôt
    # que de les supposer, pour ne pas dépendre de l'ordre d'insertion ci-dessus.
    priority_ids = dict(bind.execute(sa.text("SELECT name, id FROM priorities")).fetchall())
    for name, priority_name, first_response, resolution in SLAS:
        bind.execute(
            sa.text(
                "INSERT INTO slas (name, priority_id, first_response_minutes, resolution_minutes, is_active) "
                "VALUES (:name, :priority_id, :first_response, :resolution, true)"
            ),
            {
                "name": name,
                "priority_id": priority_ids[priority_name],
                "first_response": first_response,
                "resolution": resolution,
            },
        )


def _delete_by_name(bind, table: str, names: list[str]) -> None:
    """Suppression par nom via bindparam(expanding=True) — pattern documenté par
    SQLAlchemy pour une clause IN en SQL textuel, sans dépendre d'une
    adaptation Python-list -> tableau Postgres spécifique au driver."""
    stmt = sa.text(f"DELETE FROM {table} WHERE name IN :names").bindparams(sa.bindparam("names", expanding=True))
    bind.execute(stmt, {"names": names})


def downgrade() -> None:
    bind = op.get_bind()
    _delete_by_name(bind, "slas", [s[0] for s in SLAS])
    all_category_names = list(CATEGORIES.keys()) + [child for children in CATEGORIES.values() for child in children]
    _delete_by_name(bind, "categories", all_category_names)
    _delete_by_name(bind, "statuses", [s[0] for s in STATUSES])
    _delete_by_name(bind, "priorities", [p[0] for p in PRIORITIES])
    _delete_by_name(bind, "departments", [d[0] for d in DEPARTMENTS])
    _delete_by_name(bind, "roles", [r[0] for r in ROLES])
