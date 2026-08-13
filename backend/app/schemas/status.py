from pydantic import BaseModel, ConfigDict


class StatusBase(BaseModel):
    name: str
    description: str | None = None


class StatusCreate(StatusBase):
    pass


class StatusUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class StatusOut(StatusBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
