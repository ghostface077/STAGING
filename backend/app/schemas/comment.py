from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserSummary


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)
    is_internal: bool = False


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1)


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_type: str
    file_size: int
    created_at: datetime


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    content: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime
    user: UserSummary
    attachments: list[AttachmentOut] = []
