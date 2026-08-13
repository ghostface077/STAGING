from pydantic import BaseModel, ConfigDict


class PriorityBase(BaseModel):
    name: str
    level: int
    description: str | None = None


class PriorityCreate(PriorityBase):
    pass


class PriorityUpdate(BaseModel):
    name: str | None = None
    level: int | None = None
    description: str | None = None


class PriorityOut(PriorityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
