"""
Regroupe l'ensemble des modèles SQLAlchemy afin qu'ils soient tous enregistrés
sur `Base.metadata` avant toute génération de migration Alembic ou création
de session (voir app/database.py).
"""
from app.models.role import Role
from app.models.department import Department
from app.models.user import User
from app.models.team import Team, team_users
from app.models.category import Category
from app.models.priority import Priority
from app.models.status import Status
from app.models.sla import SLA
from app.models.equipment import Equipment
from app.models.ticket import Ticket
from app.models.comment import Comment
from app.models.attachment import Attachment
from app.models.ticket_history import TicketHistory
from app.models.notification import Notification
from app.models.knowledge_base import KnowledgeBaseArticle
from app.models.satisfaction_rating import SatisfactionRating
from app.models.audit_log import AuditLog

__all__ = [
    "Role",
    "Department",
    "User",
    "Team",
    "team_users",
    "Category",
    "Priority",
    "Status",
    "SLA",
    "Equipment",
    "Ticket",
    "Comment",
    "Attachment",
    "TicketHistory",
    "Notification",
    "KnowledgeBaseArticle",
    "SatisfactionRating",
    "AuditLog",
]
