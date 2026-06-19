from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)


class CurrentUser(BaseModel):
    id: str
    email: str
    name: str | None = None


def get_jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET must be set")
    return secret


def create_access_token(user_id: str, email: str, expires_hours: int = 24) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = str(payload.get("sub") or "").strip()
    email = str(payload.get("email") or "").strip()
    if not user_id or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    from services.memory_service import get_user_by_id

    user = await get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return CurrentUser(id=user_id, email=email, name=user.get("name"))
