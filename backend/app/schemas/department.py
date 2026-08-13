from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DepartmentBase(BaseModel):
    name: str
    description: str | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DepartmentOut(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
