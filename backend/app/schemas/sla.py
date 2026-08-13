from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.priority import PriorityOut


class SLABase(BaseModel):
    name: str
    priority_id: int
    first_response_minutes: int
    resolution_minutes: int
    is_active: bool = True


class SLACreate(SLABase):
    pass


class SLAUpdate(BaseModel):
    name: str | None = None
    priority_id: int | None = None
    first_response_minutes: int | None = None
    resolution_minutes: int | None = None
    is_active: bool | None = None


class SLAOut(SLABase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    priority: PriorityOut | None = None


class SLAProgress(BaseModel):
    """État calculé du SLA pour un ticket donné (utilisé pour l'affichage visuel du SLA)."""

    sla_id: int | None
    sla_name: str | None
    first_response_deadline: datetime | None
    resolution_deadline: datetime | None
    first_response_met: bool | None
    minutes_remaining: int | None
    percent_elapsed: float | None
    state: str  # "normal" | "attention" | "critique" | "depasse" | "aucun"
