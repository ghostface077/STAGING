from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.department import DepartmentOut
from app.schemas.user import UserSummary


class EquipmentBase(BaseModel):
    asset_number: str
    type: str
    brand: str
    model: str
    serial_number: str | None = None
    user_id: int | None = None
    department_id: int | None = None
    operating_system: str | None = None
    purchase_date: date | None = None
    warranty_end_date: date | None = None
    status: str = "En service"


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    asset_number: str | None = None
    type: str | None = None
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    user_id: int | None = None
    department_id: int | None = None
    operating_system: str | None = None
    purchase_date: date | None = None
    warranty_end_date: date | None = None
    status: str | None = None


class EquipmentOut(EquipmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    user: UserSummary | None = None
    department: DepartmentOut | None = None
