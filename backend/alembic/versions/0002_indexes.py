"""Index de performance sur tickets et clés étrangères les plus sollicitées
(correctif #08).

Revision ID: 0002_indexes
Revises: 0001_initial
Create Date: 2026-08-13
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_indexes"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- tickets : colonnes filtrées/triées par list_tickets, le tableau de bord
    # et les rapports (correctif #08, partie audit) ---
    op.create_index("ix_tickets_status_id", "tickets", ["status_id"])
    op.create_index("ix_tickets_technician_id", "tickets", ["technician_id"])
    op.create_index("ix_tickets_requester_id", "tickets", ["requester_id"])
    op.create_index("ix_tickets_category_id", "tickets", ["category_id"])
    op.create_index("ix_tickets_priority_id", "tickets", ["priority_id"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])
    op.create_index("ix_tickets_status_created_at", "tickets", ["status_id", "created_at"])

    # --- clés étrangères réellement filtrées/jointes ailleurs dans l'application
    # (correctif #08, revue complémentaire) ---
    op.create_index("ix_comments_ticket_id", "comments", ["ticket_id"])
    op.create_index("ix_ticket_history_ticket_id", "ticket_history", ["ticket_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # Note : satisfaction_ratings.ticket_id est volontairement exclu — cette
    # colonne porte déjà une contrainte UNIQUE (0001_initial_schema.py), qui crée
    # implicitement un index ; en ajouter un second serait redondant.
    # attachments.ticket_id est volontairement exclu — jamais filtré ni joint
    # nulle part dans l'application (les pièces jointes sont chargées via
    # comment_id), un index dessus serait inutile.


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_ticket_history_ticket_id", table_name="ticket_history")
    op.drop_index("ix_comments_ticket_id", table_name="comments")

    op.drop_index("ix_tickets_status_created_at", table_name="tickets")
    op.drop_index("ix_tickets_created_at", table_name="tickets")
    op.drop_index("ix_tickets_priority_id", table_name="tickets")
    op.drop_index("ix_tickets_category_id", table_name="tickets")
    op.drop_index("ix_tickets_requester_id", table_name="tickets")
    op.drop_index("ix_tickets_technician_id", table_name="tickets")
    op.drop_index("ix_tickets_status_id", table_name="tickets")
