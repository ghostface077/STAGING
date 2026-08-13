from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SatisfactionCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class SatisfactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    rating: int
    comment: str | None
    created_at: datetime
