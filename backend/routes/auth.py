from __future__ import annotations

import asyncio
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from rate_limit import limiter
from models.user import UserCreate, UserOut
from security import (
    CurrentUser,
    clear_auth_cookie,
    create_access_token,
    get_current_user,
    hash_password,
    set_auth_cookie,
    verify_password,
)
from services.memory_service import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_verification_token,
    mark_email_verified,
    set_verification_token,
    upsert_user,
)

router = APIRouter()


def _generate_verification_token() -> str:
    return secrets.token_urlsafe(48)


async def _send_verification_email(user: UserOut) -> None:
    """Generate a verification token, persist it, and send the email via Resend."""
    resend_api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not resend_api_key:
        return

    token = _generate_verification_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    await set_verification_token(user.id, token, expires_at)

    from services.email_service import send_verification_email

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, send_verification_email, user, token)


@limiter.limit("3/minute")
@router.post("/register", response_model=dict)
async def register_user(
    request: Request,
    payload: UserCreate,
    response: Response,
) -> dict:
    """Register a user with a hashed password and set an HttpOnly session cookie."""
    existing = await get_user_by_email(str(payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    password_hash = hash_password(payload.password)
    user = await upsert_user(str(payload.email), payload.name, password_hash=password_hash)
    token = create_access_token(str(user["id"]), str(user["email"]))
    set_auth_cookie(response, token)

    user_obj = UserOut(**user)
    asyncio.create_task(_send_verification_email(user_obj))

    return {"user": user_obj.model_dump()}


@limiter.limit("5/minute")
@router.post("/login", response_model=dict)
async def login_user(
    request: Request,
    payload: UserCreate,
    response: Response,
) -> dict:
    """Validate credentials, set an HttpOnly session cookie, and return the user profile."""
    user = await get_user_by_email(str(payload.email))
    if user is None or not user.get("password_hash"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not verify_password(payload.password, str(user["password_hash"])):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(str(user["id"]), str(user["email"]))
    set_auth_cookie(response, token)
    return {"user": UserOut(**user).model_dump()}


@router.post("/logout")
async def logout(response: Response) -> dict:
    """Clear the HttpOnly session cookie."""
    clear_auth_cookie(response)
    return {"detail": "Logged out"}


@limiter.limit("3/minute")
@router.post("/send-verification")
async def send_verification(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Generate a new verification token and email it to the current user."""
    if current_user.email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")

    user = await get_user_by_id(current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_obj = UserOut(**user)
    asyncio.create_task(_send_verification_email(user_obj))
    return {"detail": "Verification email sent"}


@router.get("/verify-email")
async def verify_email(
    token: str = Query(..., min_length=1),
) -> dict:
    """Confirm a user's email via a signed verification token."""
    user = await get_user_by_verification_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    await mark_email_verified(str(user["id"]))
    return {"detail": "Email verified successfully"}


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser = Depends(get_current_user)) -> UserOut:
    """Expose a minimal profile endpoint for session hydration."""
    return UserOut(**current_user.model_dump())
