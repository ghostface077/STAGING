from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserSummary


class TeamBase(BaseModel):
    name: str
    description: str | None = None


class TeamCreate(TeamBase):
    member_ids: list[int] = []


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    member_ids: list[int] | None = None


class TeamOut(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    members: list[UserSummary] = []
