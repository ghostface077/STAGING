from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryOut
from app.schemas.priority import PriorityOut
from app.schemas.sla import SLAOut, SLAProgress
from app.schemas.status import StatusOut
from app.schemas.team import TeamOut
from app.schemas.user import UserSummary


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=1)
    category_id: int
    priority_id: int
    equipment_id: int | None = None


class TicketUpdate(BaseModel):
    """Mise à jour libre des champs éditoriaux d'un ticket (hors actions de workflow dédiées)."""

    title: str | None = None
    description: str | None = None
    category_id: int | None = None
    equipment_id: int | None = None


class TicketAssignRequest(BaseModel):
    technician_id: int | None = None
    team_id: int | None = None


class TicketStatusRequest(BaseModel):
    status_id: int


class TicketPriorityRequest(BaseModel):
    priority_id: int


class TicketResolveRequest(BaseModel):
    solution: str = Field(min_length=1)


class TicketEscalateRequest(BaseModel):
    team_id: int | None = None
    technician_id: int | None = None
    reason: str | None = None


class TicketListItem(BaseModel):
    """Version allégée d'un ticket pour les listes/tableaux."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    title: str
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    requester: UserSummary
    technician: UserSummary | None = None
    team: TeamOut | None = None
    category: CategoryOut
    priority: PriorityOut
    status: StatusOut
    sla_progress: SLAProgress | None = None


class TicketOut(TicketListItem):
    description: str
    solution: str | None
    equipment_id: int | None
    sla: SLAOut | None = None
    closed_at: datetime | None
    first_response_at: datetime | None
