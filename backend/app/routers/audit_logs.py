"""Consultation du journal d'audit global (réservée à l'administrateur)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_admin
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogOut

router = APIRouter(prefix="/api/audit-logs", tags=["Journal d'audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    entity_type: str | None = None,
    user_id: int | None = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog).options(joinedload(AuditLog.user))
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    return query.order_by(AuditLog.created_at.desc()).limit(500).all()
