from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from fastapi import APIRouter, Header, HTTPException, status

from models.user import UserCreate, UserOut
from services.memory_service import upsert_user

router = APIRouter()


def _issue_token(user_id: str, email: str) -> str:
    """Create a signed JWT for the user session."""
    secret = os.environ.get("JWT_SECRET", "dev-secret")
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@router.post("/register", response_model=dict)
async def register_user(payload: UserCreate) -> dict:
    """Register or upsert a user profile and return an access token."""
    user = await upsert_user(str(payload.email), payload.name)
    token = _issue_token(str(user["id"]), str(user["email"]))
    return {"user": UserOut(**user).model_dump(), "token": token}


@router.post("/login", response_model=dict)
async def login_user(payload: UserCreate) -> dict:
    """Return a token for a user record to keep the flow simple during setup."""
    user = await upsert_user(str(payload.email), payload.name)
    token = _issue_token(str(user["id"]), str(user["email"]))
    return {"user": UserOut(**user).model_dump(), "token": token}


@router.get("/me", response_model=UserOut)
async def me(authorization: str | None = Header(default=None)) -> UserOut:
    """Expose a minimal profile endpoint for session hydration."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    secret = os.environ.get("JWT_SECRET", "dev-secret")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    return UserOut(id=str(payload.get("sub") or ""), email=str(payload.get("email") or ""), name=None)
