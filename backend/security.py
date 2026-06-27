from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException, Request, Response, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)

COOKIE_NAME = "mindmirror_token"
COOKIE_MAX_AGE = 24 * 60 * 60  # 24 hours in seconds


class CurrentUser(BaseModel):
    id: str
    email: str
    name: str | None = None
    email_verified: bool = False


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


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
        secure=os.environ.get("ENVIRONMENT", "development") == "production",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False


def _decode_token(token: str) -> tuple[str, str]:
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = str(payload.get("sub") or "").strip()
    email = str(payload.get("email") or "").strip()
    if not user_id or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return user_id, email


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> CurrentUser:
    token: str | None = None

    auth_str = authorization if isinstance(authorization, str) else None
    if auth_str and auth_str.lower().startswith("bearer "):
        token = auth_str.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user_id, email = _decode_token(token)

    from services.memory_service import get_user_by_id

    user = await get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return CurrentUser(
        id=user_id,
        email=email,
        name=user.get("name"),
        email_verified=bool(user.get("email_verified", False)),
    )
