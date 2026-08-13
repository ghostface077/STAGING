from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserSummary


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    entity_type: str
    entity_id: int | None
    ip_address: str | None
    created_at: datetime
    user: UserSummary | None = None
