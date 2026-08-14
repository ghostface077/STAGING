"""Suppression logique des tickets (correctif #09) : ajoute deleted_at et
deleted_by_id sur tickets, au lieu d'une suppression physique en cascade.

Revision ID: 0003_soft_delete
Revises: 0002_indexes
Create Date: 2026-08-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_soft_delete"
down_revision: Union[str, None] = "0002_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch_alter_table : équivalent à un ALTER TABLE direct sur PostgreSQL (la
    # cible réelle), mais indispensable pour que l'ajout de contrainte FK reste
    # exécutable sur SQLite également (utilisé par la suite de tests).
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("deleted_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_tickets_deleted_by_id_users", "users", ["deleted_by_id"], ["id"], ondelete="SET NULL"
        )
        # Indexé : chaque requête de liste (tickets, tableau de bord, rapports)
        # filtre désormais systématiquement sur deleted_at IS NULL/IS NOT NULL.
        batch_op.create_index("ix_tickets_deleted_at", ["deleted_at"])


def downgrade() -> None:
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.drop_index("ix_tickets_deleted_at")
        batch_op.drop_constraint("fk_tickets_deleted_by_id_users", type_="foreignkey")
        batch_op.drop_column("deleted_by_id")
        batch_op.drop_column("deleted_at")
