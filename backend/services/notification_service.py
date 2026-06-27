from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timezone

from services.memory_service import _execute, _fetch, _fetchrow, _get_pool

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY: str | None = None
VAPID_PUBLIC_KEY: str | None = None
VAPID_CLAIM_EMAIL: str | None = None


def init_vapid() -> None:
    global VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIM_EMAIL
    private = os.environ.get("VAPID_PRIVATE_KEY", "").strip()
    public = os.environ.get("VAPID_PUBLIC_KEY", "").strip()
    email = os.environ.get("VAPID_CLAIM_EMAIL", "").strip()
    if private and public:
        VAPID_PRIVATE_KEY = private
        VAPID_PUBLIC_KEY = public
        VAPID_CLAIM_EMAIL = email or "mailto:admin@mindmirror.app"


def _ensure_vapid() -> None:
    if VAPID_PRIVATE_KEY is None:
        init_vapid()
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        logger.warning("VAPID keys not configured — push notifications disabled")

# ─── Push subscription CRUD ────────────────────────────────────────────

SUBSCRIPTION_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, endpoint)
)
"""


async def ensure_push_schema() -> None:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SUBSCRIPTION_SCHEMA_SQL)
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT FALSE")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_checkin_date DATE")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_notification_sent_at TIMESTAMP")


async def save_push_subscription(user_id: str, endpoint: str, p256dh: str, auth: str) -> dict | None:
    row = await _fetchrow(
        """
        INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id, endpoint)
        DO UPDATE SET p256dh = EXCLUDED.p256dh, auth = EXCLUDED.auth
        RETURNING *
        """,
        user_id, endpoint, p256dh, auth,
    )
    return dict(row) if row else None


async def delete_push_subscription(user_id: str, endpoint: str) -> None:
    await _execute(
        "DELETE FROM push_subscriptions WHERE user_id = $1 AND endpoint = $2",
        user_id, endpoint,
    )


async def list_push_subscriptions(user_id: str) -> list[dict]:
    rows = await _fetch(
        "SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = $1",
        user_id,
    )
    return [dict(r) for r in rows]


async def list_all_subscriptions() -> list[dict]:
    rows = await _fetch(
        """
        SELECT ps.user_id, ps.endpoint, ps.p256dh, ps.auth, u.email, u.name, u.notifications_enabled
        FROM push_subscriptions ps
        JOIN users u ON u.id = ps.user_id
        WHERE u.notifications_enabled = TRUE
        """
    )
    return [dict(r) for r in rows]

# ─── Send push notification ────────────────────────────────────────────


async def send_push_notification(
    endpoint: str,
    p256dh: str,
    auth: str,
    title: str,
    body: str,
    icon: str = "/icons/icon-192.svg",
    tag: str = "mindmirror",
) -> bool:
    _ensure_vapid()
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        return False

    try:
        from pywebpush import webpush, WebPushException

        data = json.dumps({"title": title, "body": body, "icon": icon, "tag": tag, "requireInteraction": True})
        sub_info = {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}
        webpush(
            subscription_info=sub_info,
            data=data,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIM_EMAIL or "mailto:admin@mindmirror.app"},
        )
        return True
    except WebPushException as exc:
        if exc.response and exc.response.status_code in (410, 404):
            logger.info("Push subscription expired/gone, will be cleaned up")
        else:
            logger.warning("Push send failed: %s", exc)
        return False
    except Exception as exc:
        logger.warning("Push notification error: %s", exc)
        return False


async def notify_user(
    user_id: str,
    title: str,
    body: str,
    send_email: bool = True,
) -> None:
    subs = await list_push_subscriptions(user_id)
    for sub in subs:
        await send_push_notification(
            endpoint=sub["endpoint"],
            p256dh=sub["p256dh"],
            auth=sub["auth"],
            title=title,
            body=body,
        )

    if send_email:
        try:
            from services.email_service import send_notification_email
            from models.user import UserOut
            row = await _fetchrow("SELECT email, name FROM users WHERE id = $1", user_id)
            if row:
                user = UserOut(id=user_id, email=row["email"], name=row.get("name"))
                send_notification_email(user, title, body)
        except Exception as exc:
            logger.warning("Failed to send notification email: %s", exc)

    now = datetime.now(timezone.utc)
    await _execute(
        "UPDATE users SET last_notification_sent_at = $2 WHERE id = $1",
        user_id, now,
    )

# ─── Check-in tracking ────────────────────────────────────────────────


async def has_checked_in_today(user_id: str) -> bool:
    row = await _fetchrow(
        "SELECT id FROM journal_entries WHERE user_id = $1 AND created_at::date = CURRENT_DATE LIMIT 1",
        user_id,
    )
    return row is not None


async def get_users_due_for_checkin() -> list[dict]:
    rows = await _fetch(
        """
        SELECT id, email, name, notifications_enabled, last_notification_sent_at
        FROM users
        WHERE notifications_enabled = TRUE
          AND (last_notification_sent_at IS NULL
               OR last_notification_sent_at < NOW() - INTERVAL '12 hours')
        """
    )
    return [dict(r) for r in rows]


async def mark_checkin_date(user_id: str) -> None:
    await _execute(
        "UPDATE users SET last_checkin_date = $2 WHERE id = $1",
        user_id, date.today(),
    )
