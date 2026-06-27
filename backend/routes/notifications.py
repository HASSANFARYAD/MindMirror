from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from security import CurrentUser, get_current_user
from services.notification_service import (
    VAPID_PUBLIC_KEY,
    delete_push_subscription,
    ensure_push_schema,
    list_push_subscriptions,
    save_push_subscription,
)
from services.memory_service import _execute

router = APIRouter(prefix="/notifications", tags=["notifications"])


class PushSubscriptionIn(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class NotificationPrefsIn(BaseModel):
    notifications_enabled: bool


@router.get("/vapid-public-key")
async def get_vapid_public_key() -> dict:
    if not VAPID_PUBLIC_KEY:
        return {"publicKey": None}
    return {"publicKey": VAPID_PUBLIC_KEY}


@router.post("/subscribe")
async def subscribe_push(
    payload: PushSubscriptionIn,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    await ensure_push_schema()
    await save_push_subscription(current_user.id, payload.endpoint, payload.p256dh, payload.auth)
    return {"detail": "Subscribed"}


@router.post("/unsubscribe")
async def unsubscribe_push(
    payload: PushSubscriptionIn,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    await delete_push_subscription(current_user.id, payload.endpoint)
    return {"detail": "Unsubscribed"}


@router.get("/subscriptions")
async def get_subscriptions(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict]:
    return await list_push_subscriptions(current_user.id)


@router.get("/preferences")
async def get_preferences(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    from services.memory_service import _fetchrow
    row = await _fetchrow(
        "SELECT notifications_enabled FROM users WHERE id = $1",
        current_user.id,
    )
    enabled = bool(row["notifications_enabled"]) if row else False
    return {"notifications_enabled": enabled}


@router.put("/preferences")
async def update_preferences(
    payload: NotificationPrefsIn,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    await _execute(
        "UPDATE users SET notifications_enabled = $2 WHERE id = $1",
        current_user.id,
        payload.notifications_enabled,
    )
    return {"detail": "Preferences updated"}
