from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserSummary


class TicketHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    action: str
    old_value: str | None
    new_value: str | None
    created_at: datetime
    user: UserSummary | None = None
