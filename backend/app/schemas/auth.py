from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = None
    department_id: int | None = None


class TokenResponse(BaseModel):
    """Réponse de connexion/inscription (correctif #12) : ne contient plus le
    jeton lui-même — access token et refresh token sont posés en cookies
    httpOnly, jamais exposés dans le corps de la réponse où un script pourrait
    les lire."""

    user: UserOut
