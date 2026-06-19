from pydantic import BaseModel, Field
from pydantic import EmailStr


class UserCreate(BaseModel):
    """Validate an incoming auth or profile creation payload."""

    email: EmailStr
    name: str | None = None
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    """Return a minimal, safe user representation to the frontend."""

    id: str
    email: str
    name: str | None = None
