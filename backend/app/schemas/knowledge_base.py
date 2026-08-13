from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryOut
from app.schemas.user import UserSummary


class KnowledgeBaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    category_id: int | None = None
    status: str = "Brouillon"


class KnowledgeBaseUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category_id: int | None = None
    status: str | None = None


class KnowledgeBaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    status: str
    views: int
    created_at: datetime
    updated_at: datetime
    category: CategoryOut | None = None
    author: UserSummary | None = None
