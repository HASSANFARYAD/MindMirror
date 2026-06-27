from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _checkin_reminder_job() -> None:
    """Check for users who haven't journaled today and send a reminder."""
    from services.notification_service import get_users_due_for_checkin, has_checked_in_today, notify_user

    users = await get_users_due_for_checkin()
    for user in users:
        uid = user["id"]
        checked_in = await has_checked_in_today(uid)
        if checked_in:
            continue

        name = user.get("name") or "there"
        await notify_user(
            user_id=uid,
            title="How are you feeling? 🌅",
            body=f"Hey {name}, take a moment to check in with yourself today.",
            send_email=True,
        )
        await asyncio.sleep(1)


async def _alert_notification_job() -> None:
    """Check for users with high-severity alerts and notify them."""
    from services.memory_service import _fetch

    rows = await _fetch(
        """
        SELECT DISTINCT ep.user_id, ep.description, u.email, u.name
        FROM emotional_patterns ep
        JOIN users u ON u.id = ep.user_id
        WHERE ep.pattern_type = 'alert'
          AND ep.severity = 'high'
          AND ep.detected_at >= NOW() - INTERVAL '24 hours'
          AND u.notifications_enabled = TRUE
          AND (u.last_notification_sent_at IS NULL
               OR u.last_notification_sent_at < ep.detected_at)
        """
    )
    for row in rows:
        from services.notification_service import notify_user
        user = dict(row)
        await notify_user(
            user_id=user["user_id"],
            title="MindMirror Alert 💙",
            body=user.get("description", "We noticed you might be struggling. Reach out to someone you trust."),
            send_email=True,
        )
        await asyncio.sleep(1)


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler

    _scheduler = AsyncIOScheduler()

    _scheduler.add_job(
        _checkin_reminder_job,
        IntervalTrigger(hours=1),
        id="checkin_reminder",
        replace_existing=True,
        misfire_grace_time=300,
    )

    _scheduler.add_job(
        _alert_notification_job,
        IntervalTrigger(hours=6),
        id="alert_notification",
        replace_existing=True,
        misfire_grace_time=300,
    )

    _scheduler.start()
    logger.info("Notification scheduler started (check-in: hourly, alerts: every 6h)")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Notification scheduler stopped")
