from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.department import DepartmentOut
from app.schemas.role import RoleOut


class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    role_id: int
    department_id: int | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    is_active: bool = True


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    role_id: int | None = None
    department_id: int | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserSummary(BaseModel):
    """Version allégée de l'utilisateur, utilisée dans les objets imbriqués (tickets, commentaires...)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    role: RoleOut | None = None
    department: DepartmentOut | None = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class SelfProfileUpdate(BaseModel):
    """
    Champs qu'un utilisateur est autorisé à modifier lui-même depuis la page Profil.
    Volontairement restreint : ni rôle, ni service, ni statut actif, ni e-mail
    ne peuvent être changés par ce biais (évite toute élévation de privilège).
    """

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = None
