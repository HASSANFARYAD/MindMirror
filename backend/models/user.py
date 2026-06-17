from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Validate an incoming auth or profile creation payload."""

    email: str
    name: str | None = None
    password: str | None = Field(default=None, min_length=8)


class UserOut(BaseModel):
    """Return a minimal, safe user representation to the frontend."""

    id: str
    email: str
    name: str | None = None
