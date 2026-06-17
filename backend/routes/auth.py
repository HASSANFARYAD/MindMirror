from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from limits import limiter
from models.user import UserCreate, UserOut
from security import CurrentUser, create_access_token, get_current_user, hash_password, verify_password
from services.memory_service import get_user_by_email, upsert_user

router = APIRouter()


@limiter.limit("3/minute")
@router.post("/register", response_model=dict)
async def register_user(request: Request, payload: UserCreate) -> dict:
    """Register a user with a hashed password and return a signed token."""
    existing = await get_user_by_email(str(payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    password_hash = hash_password(payload.password)
    user = await upsert_user(str(payload.email), payload.name, password_hash=password_hash)
    token = create_access_token(str(user["id"]), str(user["email"]))
    return {"user": UserOut(**user).model_dump(), "token": token}


@limiter.limit("5/minute")
@router.post("/login", response_model=dict)
async def login_user(request: Request, payload: UserCreate) -> dict:
    """Validate a user password and return a signed token."""
    user = await get_user_by_email(str(payload.email))
    if user is None or not user.get("password_hash"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not verify_password(payload.password, str(user["password_hash"])):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(str(user["id"]), str(user["email"]))
    return {"user": UserOut(**user).model_dump(), "token": token}


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser = Depends(get_current_user)) -> UserOut:
    """Expose a minimal profile endpoint for session hydration."""
    return UserOut(**current_user.model_dump())
