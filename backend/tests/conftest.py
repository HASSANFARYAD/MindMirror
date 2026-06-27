from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

os.environ["JWT_SECRET"] = "test-secret-value-for-tests-only"
os.environ["AI_PROVIDER"] = "ollama"
os.environ["DATABASE_URL"] = "postgresql://fake:fake@localhost:9999/fake"
os.environ["RATE_LIMIT_ENABLED"] = "false"

# ---------------------------------------------------------------------------
# Mock heavy ML / AI modules so service imports don't trigger real loading
# ---------------------------------------------------------------------------
_transformers_mock = MagicMock()
_pipeline_mock = MagicMock(return_value=MagicMock())
_transformers_mock.pipeline = _pipeline_mock
sys.modules["transformers"] = _transformers_mock

# Mock whisper to avoid model download
sys.modules["faster_whisper"] = MagicMock()

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_EMAIL = "test@mindmirror.app"
TEST_USER_NAME = "Test User"
TEST_PASSWORD = "TestPass123!"


class MockDB:
    """In-memory mock for database operations used by tests."""

    def __init__(self) -> None:
        self.users: dict[str, dict[str, Any]] = {
            TEST_USER_ID: {
                "id": TEST_USER_ID,
                "email": TEST_USER_EMAIL,
                "name": TEST_USER_NAME,
                "password_hash": None,
            }
        }
        self.journal_entries: list[dict[str, Any]] = []
        self.chat_threads: list[dict[str, Any]] = []
        self.chat_messages: list[dict[str, Any]] = []
        self.patterns: list[dict[str, Any]] = []
        self.weekly_insights: list[dict[str, Any]] = []


_mock_db = MockDB()


def reset_mock_db() -> None:
    _mock_db.users = {
        TEST_USER_ID: {
            "id": TEST_USER_ID,
            "email": TEST_USER_EMAIL,
            "name": TEST_USER_NAME,
            "password_hash": None,
        }
    }
    _mock_db.journal_entries = []
    _mock_db.chat_threads = []
    _mock_db.chat_messages = []
    _mock_db.patterns = []
    _mock_db.weekly_insights = []


# ---------------------------------------------------------------------------
# Mock memory_service functions
# ---------------------------------------------------------------------------


async def _mock_get_user_by_email(email: str) -> dict[str, Any] | None:
    for user in _mock_db.users.values():
        if user["email"] == email:
            return dict(user)
    return None


async def _mock_get_user_by_id(user_id: str) -> dict[str, Any] | None:
    return _mock_db.users.get(user_id)


async def _mock_upsert_user(
    email: str, name: str | None = None, password_hash: str | None = None
) -> dict[str, Any]:
    from uuid import uuid4

    uid = str(uuid4())
    user = {"id": uid, "email": email, "name": name, "password_hash": password_hash}
    _mock_db.users[uid] = user
    return dict(user)


async def _mock_save_journal_entry(
    user_id: str, content: str, analysis_result: dict[str, Any]
) -> dict[str, Any]:
    from uuid import uuid4

    entry = {
        "id": str(uuid4()),
        "user_id": user_id,
        "content": content,
        "voice_transcript": analysis_result.get("voice_transcript"),
        "sentiment_score": analysis_result.get("sentiment_score"),
        "sentiment_label": analysis_result.get("sentiment_label"),
        "emotions": analysis_result.get("emotions"),
        "cognitive_distortions": analysis_result.get("cognitive_distortions"),
        "created_at": datetime.utcnow(),
    }
    _mock_db.journal_entries.append(entry)
    return dict(entry)


async def _mock_list_journal_entries(
    user_id: str, days: int | None = 30
) -> list[dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=days) if days else datetime.min
    return [
        dict(e)
        for e in _mock_db.journal_entries
        if e["user_id"] == user_id and e["created_at"] >= cutoff
    ]


async def _mock_get_journal_entry(
    entry_id: str, user_id: str | None = None
) -> dict[str, Any] | None:
    for e in _mock_db.journal_entries:
        if e["id"] == entry_id and (user_id is None or e["user_id"] == user_id):
            return dict(e)
    return None


async def _mock_create_chat_thread(
    user_id: str, title: str, journal_entry_id: str | None = None
) -> dict[str, Any]:
    from uuid import uuid4

    thread = {
        "id": str(uuid4()),
        "user_id": user_id,
        "title": title,
        "journal_entry_id": journal_entry_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "message_count": 0,
        "last_message_preview": None,
        "last_activity_at": datetime.utcnow(),
    }
    _mock_db.chat_threads.append(thread)
    return dict(thread)


async def _mock_list_chat_threads(
    user_id: str, search: str | None = None, journal_only: bool = False
) -> list[dict[str, Any]]:
    results = []
    for t in _mock_db.chat_threads:
        if t["user_id"] != user_id:
            continue
        if journal_only and not t.get("journal_entry_id"):
            continue
        if search:
            if search.lower() not in t["title"].lower():
                continue
        results.append(dict(t))
    return results


async def _mock_get_chat_thread(
    thread_id: str, user_id: str
) -> dict[str, Any] | None:
    for t in _mock_db.chat_threads:
        if t["id"] == thread_id and t["user_id"] == user_id:
            thread = dict(t)
            thread["messages"] = [
                dict(m)
                for m in _mock_db.chat_messages
                if m["thread_id"] == thread_id
            ]
            return thread
    return None


async def _mock_update_chat_thread(
    thread_id: str, user_id: str, title: str
) -> dict[str, Any] | None:
    for t in _mock_db.chat_threads:
        if t["id"] == thread_id and t["user_id"] == user_id:
            t["title"] = title
            t["updated_at"] = datetime.utcnow()
            return dict(t)
    return None


async def _mock_delete_chat_thread(thread_id: str, user_id: str) -> None:
    _mock_db.chat_threads[:] = [
        t for t in _mock_db.chat_threads if not (t["id"] == thread_id and t["user_id"] == user_id)
    ]
    _mock_db.chat_messages[:] = [
        m for m in _mock_db.chat_messages if m["thread_id"] != thread_id
    ]


async def _mock_insert_chat_message(payload: dict[str, Any]) -> dict[str, Any]:
    from uuid import uuid4

    msg = {
        "id": str(uuid4()),
        "user_id": payload.get("user_id"),
        "thread_id": payload.get("thread_id"),
        "role": payload.get("role"),
        "content": payload.get("content"),
        "created_at": datetime.utcnow(),
    }
    _mock_db.chat_messages.append(msg)
    return dict(msg)


async def _mock_get_chat_history(
    user_id: str, thread_id: str, limit: int = 20
) -> list[dict[str, Any]]:
    msgs = [
        dict(m)
        for m in _mock_db.chat_messages
        if m["thread_id"] == thread_id and m["user_id"] == user_id
    ]
    return msgs[-limit:]


async def _mock_list_patterns(
    user_id: str, limit: int = 20
) -> list[dict[str, Any]]:
    return [dict(p) for p in _mock_db.patterns[-limit:]]


async def _mock_insert_pattern(payload: dict[str, Any]) -> dict[str, Any]:
    from uuid import uuid4

    p = {
        "id": str(uuid4()),
        "user_id": payload.get("user_id"),
        "pattern_type": payload.get("pattern_type"),
        "description": payload.get("description"),
        "severity": payload.get("severity"),
        "detected_at": datetime.utcnow(),
    }
    _mock_db.patterns.append(p)
    return dict(p)


async def _mock_list_weekly_insights(
    user_id: str, limit: int = 4
) -> list[dict[str, Any]]:
    return [dict(i) for i in _mock_db.weekly_insights[-limit:]]


async def _mock_upsert_weekly_insight(payload: dict[str, Any]) -> dict[str, Any]:
    from uuid import uuid4

    i = {
        "id": str(uuid4()),
        "user_id": payload.get("user_id"),
        "week_start": payload.get("week_start"),
        "dominant_emotion": payload.get("dominant_emotion"),
        "avg_sentiment": payload.get("avg_sentiment"),
        "top_triggers": payload.get("top_triggers"),
        "cbt_recommendation": payload.get("cbt_recommendation"),
        "generated_at": datetime.utcnow(),
    }
    _mock_db.weekly_insights.append(i)
    return dict(i)


async def _mock_get_user_context(user_id: str) -> dict[str, Any]:
    return {
        "name": "Test User",
        "trend": "mixed",
        "dominant_emotion": "neutral",
        "triggers": ["work", "sleep"],
        "last_journal": "Had a productive day today.",
    }


async def _mock_get_emotional_map(user_id: str, days: int = 30) -> dict[str, Any]:
    entries = [e for e in _mock_db.journal_entries if e["user_id"] == user_id]
    labels = ["joy", "sadness", "fear", "anger", "surprise", "neutral", "disgust"]
    timeline = []
    for entry in entries[:30]:
        emotions = entry.get("emotions") or {}
        timeline.append({
            "date": entry.get("created_at").isoformat() if isinstance(entry.get("created_at"), datetime) else "",
            "sentiment_score": float(entry.get("sentiment_score") or 0.0),
            "dominant_emotion": entry.get("dominant_emotion") or "neutral",
            "emotions": {label: emotions.get(label, 0.0) for label in labels},
            "snippet": str(entry.get("content") or "")[:140],
        })
    totals = {label: 0.0 for label in labels}
    count = max(len(entries[:7]), 1)
    for entry in entries[:7]:
        emotions = entry.get("emotions") or {}
        for label in labels:
            totals[label] += float(emotions.get(label, 0.0))
    radar = [{"emotion": label, "score": round(totals[label] / count, 3)} for label in labels]
    patterns = await _mock_list_patterns(user_id, limit=12)
    insights = await _mock_list_weekly_insights(user_id, limit=4)
    return {"timeline": timeline, "radar": radar, "patterns": patterns, "weekly_insights": insights}


# ---------------------------------------------------------------------------
# Patch memory_service so routes never hit a real database
# ---------------------------------------------------------------------------
MEMORY_SERVICE_PATCHES = {
    "get_user_by_email": _mock_get_user_by_email,
    "get_user_by_id": _mock_get_user_by_id,
    "upsert_user": _mock_upsert_user,
    "save_journal_entry": _mock_save_journal_entry,
    "list_journal_entries": _mock_list_journal_entries,
    "get_journal_entry": _mock_get_journal_entry,
    "create_chat_thread": _mock_create_chat_thread,
    "list_chat_threads": _mock_list_chat_threads,
    "get_chat_thread": _mock_get_chat_thread,
    "update_chat_thread": _mock_update_chat_thread,
    "delete_chat_thread": _mock_delete_chat_thread,
    "insert_chat_message": _mock_insert_chat_message,
    "get_chat_history": _mock_get_chat_history,
    "list_patterns": _mock_list_patterns,
    "insert_pattern": _mock_insert_pattern,
    "list_weekly_insights": _mock_list_weekly_insights,
    "upsert_weekly_insight": _mock_upsert_weekly_insight,
    "get_user_context": _mock_get_user_context,
    "get_emotional_map": _mock_get_emotional_map,
}


@pytest.fixture(autouse=True)
def _reset_mock_db():
    reset_mock_db()
    yield


@pytest.fixture(autouse=True)
def mock_services():
    with (
        patch.multiple("services.memory_service", **MEMORY_SERVICE_PATCHES),
        patch("services.pattern_service.insert_pattern", _mock_insert_pattern),
        patch("services.pattern_service.upsert_weekly_insight", _mock_upsert_weekly_insight),
    ):
        yield


# ---------------------------------------------------------------------------
# Override fastapi dependency for get_current_user
# ---------------------------------------------------------------------------
from security import CurrentUser, get_current_user


async def _override_get_current_user() -> CurrentUser:
    return CurrentUser(id=TEST_USER_ID, email=TEST_USER_EMAIL, name=TEST_USER_NAME)


@pytest.fixture
def app(mock_services) -> FastAPI:
    from main import app

    app.dependency_overrides = {}
    app.dependency_overrides[get_current_user] = _override_get_current_user
    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict[str, str]:
    from security import create_access_token

    token = create_access_token(TEST_USER_ID, TEST_USER_EMAIL)
    return {"Authorization": f"Bearer {token}"}
