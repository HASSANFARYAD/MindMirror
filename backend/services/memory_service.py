from __future__ import annotations

import asyncio
import json
import os
import re
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import UUID
from typing import Any

import asyncpg

_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()
_schema_path = Path(__file__).resolve().parents[1] / "database" / "schema.sql"


def _default_database_url() -> str:
    return "postgresql://mindmirror_user:mindmirror_pass@postgres:5432/mindmirror"


def _record_to_dict(record: asyncpg.Record | None) -> dict[str, Any] | None:
    if record is None:
        return None
    data = dict(record)
    for key, value in list(data.items()):
        if isinstance(value, UUID):
            data[key] = str(value)
            continue
        if isinstance(value, str):
            try:
                if key in {"emotions", "cognitive_distortions", "top_triggers"} and value.startswith(("{", "[")):
                    data[key] = json.loads(value)
            except Exception:
                pass
    return data


def _rows_to_dicts(rows: list[asyncpg.Record]) -> list[dict[str, Any]]:
    return [item for row in rows if (item := _record_to_dict(row)) is not None]


async def init_pool() -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool

    async with _pool_lock:
        if _pool is None:
            database_url = os.environ.get("DATABASE_URL", _default_database_url())
            last_error: Exception | None = None
            for attempt in range(10):
                try:
                    _pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10)
                    break
                except Exception as exc:  # pragma: no cover - startup resilience
                    last_error = exc
                    if attempt < 9:
                        await asyncio.sleep(2)
            if _pool is None and last_error is not None:
                raise last_error
    return _pool


async def ensure_base_schema() -> None:
    """Create the base tables and any missing schema objects idempotently."""
    pool = await _get_pool()

    async with pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

        if not await _table_exists(conn, "users"):
            await conn.execute(
                """
                CREATE TABLE users (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  email TEXT UNIQUE NOT NULL,
                  name TEXT,
                  password_hash TEXT,
                  created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

        if not await _table_exists(conn, "journal_entries"):
            await conn.execute(
                """
                CREATE TABLE journal_entries (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  user_id UUID REFERENCES users(id),
                  content TEXT NOT NULL,
                  voice_transcript TEXT,
                  sentiment_score FLOAT,
                  sentiment_label TEXT,
                  emotions JSONB,
                  cognitive_distortions JSONB,
                  created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

        if not await _table_exists(conn, "chat_threads"):
            await conn.execute(
                """
                CREATE TABLE chat_threads (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  user_id UUID REFERENCES users(id),
                  journal_entry_id UUID REFERENCES journal_entries(id),
                  title TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT NOW(),
                  updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

        if not await _table_exists(conn, "chat_messages"):
            await conn.execute(
                """
                CREATE TABLE chat_messages (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  user_id UUID REFERENCES users(id),
                  thread_id UUID REFERENCES chat_threads(id) ON DELETE CASCADE,
                  role TEXT CHECK (role IN ('user', 'assistant')),
                  content TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

        if not await _table_exists(conn, "emotional_patterns"):
            await conn.execute(
                """
                CREATE TABLE emotional_patterns (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  user_id UUID REFERENCES users(id),
                  pattern_type TEXT,
                  description TEXT,
                  detected_at TIMESTAMP DEFAULT NOW(),
                  severity TEXT
                )
                """
            )

        if not await _table_exists(conn, "weekly_insights"):
            await conn.execute(
                """
                CREATE TABLE weekly_insights (
                  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  user_id UUID REFERENCES users(id),
                  week_start DATE,
                  dominant_emotion TEXT,
                  avg_sentiment FLOAT,
                  top_triggers JSONB,
                  cbt_recommendation TEXT,
                  generated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token TEXT")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token_expires_at TIMESTAMP")
        await conn.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS thread_id UUID")


async def _table_exists(conn: asyncpg.Connection, table_name: str) -> bool:
    return bool(await conn.fetchval("SELECT to_regclass($1) IS NOT NULL", f"public.{table_name}"))


async def _get_pool() -> asyncpg.Pool:
    return await init_pool()


async def _fetchrow(query: str, *args: Any) -> asyncpg.Record | None:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def _fetch(query: str, *args: Any) -> list[asyncpg.Record]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        return list(await conn.fetch(query, *args))


async def _execute(query: str, *args: Any) -> str:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def ensure_user_exists(user_id: str) -> None:
    row = await _fetchrow("SELECT id FROM users WHERE id = $1 LIMIT 1", user_id)
    if row is None:
        raise ValueError("User not found")


async def upsert_user(email: str, name: str | None = None, password_hash: str | None = None) -> dict[str, Any]:
    row = await _fetchrow(
        """
        INSERT INTO users (email, name, password_hash)
        VALUES ($1, $2, $3)
        ON CONFLICT (email)
        DO UPDATE SET
          name = COALESCE(EXCLUDED.name, users.name),
          password_hash = COALESCE(EXCLUDED.password_hash, users.password_hash)
        RETURNING *
        """,
        email,
        name,
        password_hash,
    )
    if row is None:
        return {"id": "", "email": email, "name": name}
    return _record_to_dict(row) or {"id": "", "email": email, "name": name}


async def get_user_by_email(email: str) -> dict[str, Any] | None:
    row = await _fetchrow("SELECT * FROM users WHERE email = $1 LIMIT 1", email)
    return _record_to_dict(row)


async def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    row = await _fetchrow("SELECT * FROM users WHERE id = $1 LIMIT 1", user_id)
    return _record_to_dict(row)


async def insert_journal_entry(payload: dict[str, Any]) -> dict[str, Any]:
    row = await _fetchrow(
        """
        INSERT INTO journal_entries (
            user_id, content, voice_transcript, sentiment_score,
            sentiment_label, emotions, cognitive_distortions
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        payload.get("user_id"),
        payload.get("content"),
        payload.get("voice_transcript"),
        payload.get("sentiment_score"),
        payload.get("sentiment_label"),
        json.dumps(payload.get("emotions")) if isinstance(payload.get("emotions"), (dict, list)) else payload.get("emotions"),
        json.dumps(payload.get("cognitive_distortions"))
        if isinstance(payload.get("cognitive_distortions"), (dict, list))
        else payload.get("cognitive_distortions"),
    )
    return _record_to_dict(row) if row else payload


async def save_journal_entry(user_id: str, content: str, analysis_result: dict[str, Any]) -> dict[str, Any]:
    await ensure_user_exists(user_id)
    payload = {
        "user_id": user_id,
        "content": content,
        "voice_transcript": analysis_result.get("voice_transcript"),
        "sentiment_score": analysis_result.get("sentiment_score"),
        "sentiment_label": analysis_result.get("sentiment_label"),
        "emotions": analysis_result.get("emotions"),
        "cognitive_distortions": analysis_result.get("cognitive_distortions"),
    }
    return await insert_journal_entry(payload)


async def get_recent_entries(user_id: str, days: int = 14) -> list[dict[str, Any]]:
    rows = await _fetch(
        """
        SELECT *
        FROM journal_entries
        WHERE user_id = $1
          AND created_at >= NOW() - ($2 * INTERVAL '1 day')
        ORDER BY created_at DESC
        """,
        user_id,
        days,
    )
    return _rows_to_dicts(rows)


async def list_journal_entries(user_id: str, days: int | None = 30) -> list[dict[str, Any]]:
    if days is None:
        rows = await _fetch(
            """
            SELECT *
            FROM journal_entries
            WHERE user_id = $1
            ORDER BY created_at DESC
            """,
            user_id,
        )
        return _rows_to_dicts(rows)
    return await get_recent_entries(user_id, days=days)


async def get_journal_entry(entry_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    if user_id is None:
        row = await _fetchrow("SELECT * FROM journal_entries WHERE id = $1 LIMIT 1", entry_id)
    else:
        row = await _fetchrow("SELECT * FROM journal_entries WHERE id = $1 AND user_id = $2 LIMIT 1", entry_id, user_id)
    return _record_to_dict(row)

async def ensure_chat_schema() -> None:
    await _execute(
        """
        CREATE TABLE IF NOT EXISTS chat_threads (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES users(id),
          journal_entry_id UUID REFERENCES journal_entries(id),
          title TEXT NOT NULL,
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    await _execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS thread_id UUID")


async def create_chat_thread(user_id: str, title: str, journal_entry_id: str | None = None) -> dict[str, Any]:
    await ensure_user_exists(user_id)
    row = await _fetchrow(
        """
        INSERT INTO chat_threads (user_id, title, journal_entry_id)
        VALUES ($1, $2, $3)
        RETURNING *
        """,
        user_id,
        title,
        journal_entry_id,
    )
    return _record_to_dict(row) if row else {"user_id": user_id, "title": title, "journal_entry_id": journal_entry_id}


async def list_chat_threads(user_id: str, search: str | None = None, journal_only: bool = True) -> list[dict[str, Any]]:
    rows = await _fetch(
        """
        SELECT
          t.*,
          COALESCE(
            (SELECT COUNT(*) FROM chat_messages m WHERE m.thread_id = t.id),
            0
          ) AS message_count,
          COALESCE(
            (SELECT content FROM chat_messages m WHERE m.thread_id = t.id ORDER BY created_at DESC LIMIT 1),
            ''
          ) AS last_message_preview,
          COALESCE(
            (SELECT MAX(created_at) FROM chat_messages m WHERE m.thread_id = t.id),
            t.updated_at,
            t.created_at
          ) AS last_activity_at
        FROM chat_threads t
        WHERE t.user_id = $1
          AND ($2::boolean = false OR t.journal_entry_id IS NOT NULL)
          AND (
            $3::text IS NULL
            OR t.title ILIKE '%' || $3 || '%'
            OR EXISTS (
              SELECT 1
              FROM chat_messages m
              WHERE m.thread_id = t.id
                AND m.content ILIKE '%' || $3 || '%'
            )
          )
        ORDER BY last_activity_at DESC
        """,
        user_id,
        journal_only,
        search.strip() if search and search.strip() else None,
    )
    return _rows_to_dicts(rows)


async def get_chat_thread(thread_id: str, user_id: str) -> dict[str, Any] | None:
    thread_row = await _fetchrow(
        """
        SELECT *
        FROM chat_threads
        WHERE id = $1
          AND user_id = $2
        LIMIT 1
        """,
        thread_id,
        user_id,
    )
    thread = _record_to_dict(thread_row)
    if thread is None:
        return None
    message_rows = await _fetch(
        """
        SELECT *
        FROM chat_messages
        WHERE thread_id = $1
          AND user_id = $2
        ORDER BY created_at ASC
        """,
        thread_id,
        user_id,
    )
    thread["messages"] = _rows_to_dicts(message_rows)
    return thread


async def update_chat_thread(thread_id: str, user_id: str, title: str) -> dict[str, Any] | None:
    row = await _fetchrow(
        """
        UPDATE chat_threads
        SET title = $3,
            updated_at = NOW()
        WHERE id = $1
          AND user_id = $2
        RETURNING *
        """,
        thread_id,
        user_id,
        title,
    )
    return _record_to_dict(row)


async def delete_chat_thread(thread_id: str, user_id: str) -> None:
    await _execute(
        """
        DELETE FROM chat_threads
        WHERE id = $1
          AND user_id = $2
        """,
        thread_id,
        user_id,
    )


async def save_chat_message(user_id: str, thread_id: str, role: str, content: str) -> dict[str, Any]:
    await ensure_user_exists(user_id)
    thread = await _fetchrow("SELECT id FROM chat_threads WHERE id = $1 AND user_id = $2 LIMIT 1", thread_id, user_id)
    if thread is None:
        raise ValueError("Chat thread not found")
    row = await _fetchrow(
        """
        INSERT INTO chat_messages (user_id, thread_id, role, content)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        user_id,
        thread_id,
        role,
        content,
    )
    await _execute(
        """
        UPDATE chat_threads
        SET updated_at = NOW()
        WHERE id = $1
          AND user_id = $2
        """,
        thread_id,
        user_id,
    )
    return _record_to_dict(row) if row else {"user_id": user_id, "thread_id": thread_id, "role": role, "content": content}


async def insert_chat_message(payload: dict[str, Any]) -> dict[str, Any]:
    return await save_chat_message(
        str(payload.get("user_id") or ""),
        str(payload.get("thread_id") or ""),
        str(payload.get("role") or "user"),
        str(payload.get("content") or ""),
    )


async def get_chat_history(user_id: str, thread_id: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = await _fetch(
        """
        SELECT *
        FROM chat_messages
        WHERE user_id = $1
          AND thread_id = $2
        ORDER BY created_at DESC
        LIMIT $3
        """,
        user_id,
        thread_id,
        limit,
    )
    return _rows_to_dicts(list(reversed(rows)))


async def list_chat_messages(user_id: str, thread_id: str, limit: int = 20) -> list[dict[str, Any]]:
    return await get_chat_history(user_id, thread_id, limit=limit)


def _normalize_emotions(value: Any) -> dict[str, float]:
    if isinstance(value, dict):
        return {str(key): float(val) for key, val in value.items()}
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return {str(key): float(val) for key, val in parsed.items()}
        except Exception:
            return {}
    return {}


def _dominant_emotion(emotions: dict[str, float] | None) -> str:
    if not emotions:
        return "neutral"
    return max(emotions.items(), key=lambda item: item[1])[0]


def _text_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[a-z']{4,}", text.lower())
    stopwords = {
        "that",
        "with",
        "from",
        "this",
        "have",
        "will",
        "your",
        "about",
        "there",
        "what",
        "when",
        "they",
        "them",
        "then",
        "than",
        "into",
        "been",
        "were",
        "because",
        "could",
        "would",
        "should",
        "feel",
        "feeling",
    }
    return [token for token in tokens if token not in stopwords]


async def get_user_context(user_id: str) -> dict[str, Any]:
    user_row = await _fetchrow("SELECT name FROM users WHERE id = $1 LIMIT 1", user_id)
    entries = await _fetch(
        """
        SELECT content, sentiment_score, emotions, created_at
        FROM journal_entries
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 7
        """,
        user_id,
    )
    entries_list = _rows_to_dicts(entries)

    sentiments = [float(entry.get("sentiment_score") or 0.0) for entry in entries_list]
    average_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
    if average_sentiment > 0.15:
        trend = "improving"
    elif average_sentiment < -0.15:
        trend = "strained"
    else:
        trend = "mixed"

    emotion_counter: Counter[str] = Counter()
    trigger_counter: Counter[str] = Counter()
    for entry in entries_list:
        emotions = _normalize_emotions(entry.get("emotions"))
        dominant = _dominant_emotion(emotions)
        if dominant:
            emotion_counter[str(dominant)] += 1

        if float(entry.get("sentiment_score") or 0.0) < 0:
            trigger_counter.update(_text_keywords(str(entry.get("content") or "")))

    dominant_emotion = emotion_counter.most_common(1)[0][0] if emotion_counter else "neutral"
    triggers = [word for word, _ in trigger_counter.most_common(5)]
    last_journal = ""
    if entries_list:
        last_journal = str(entries_list[0].get("content") or "")[:200]

    return {
        "name": str((dict(user_row) if user_row else {}).get("name") or "there"),
        "trend": trend,
        "dominant_emotion": dominant_emotion,
        "triggers": triggers,
        "last_journal": last_journal,
    }


async def save_weekly_insight(user_id: str, insight_data: dict[str, Any]) -> dict[str, Any]:
    await ensure_user_exists(user_id)
    row = await _fetchrow(
        """
        INSERT INTO weekly_insights (
            user_id, week_start, dominant_emotion, avg_sentiment, top_triggers,
            cbt_recommendation, generated_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, COALESCE($7, NOW()))
        RETURNING *
        """,
        user_id,
        insight_data.get("week_start"),
        insight_data.get("dominant_emotion"),
        insight_data.get("avg_sentiment"),
        json.dumps(insight_data.get("top_triggers"))
        if isinstance(insight_data.get("top_triggers"), (dict, list))
        else insight_data.get("top_triggers"),
        insight_data.get("cbt_recommendation"),
        insight_data.get("generated_at"),
    )
    return _record_to_dict(row) if row else {"user_id": user_id, **insight_data}


async def set_verification_token(user_id: str, token: str, expires_at: datetime) -> None:
    await _execute(
        """
        UPDATE users
        SET verification_token = $2,
            verification_token_expires_at = $3
        WHERE id = $1
        """,
        user_id,
        token,
        expires_at,
    )


async def get_user_by_verification_token(token: str) -> dict[str, Any] | None:
    row = await _fetchrow(
        """
        SELECT *
        FROM users
        WHERE verification_token = $1
          AND verification_token_expires_at > NOW()
        LIMIT 1
        """,
        token,
    )
    return _record_to_dict(row)


async def mark_email_verified(user_id: str) -> None:
    await _execute(
        """
        UPDATE users
        SET email_verified = TRUE,
            verification_token = NULL,
            verification_token_expires_at = NULL
        WHERE id = $1
        """,
        user_id,
    )


async def upsert_weekly_insight(payload: dict[str, Any]) -> dict[str, Any]:
    return await save_weekly_insight(str(payload.get("user_id") or ""), payload)


async def get_weekly_insight(user_id: str) -> dict[str, Any] | None:
    row = await _fetchrow(
        """
        SELECT *
        FROM weekly_insights
        WHERE user_id = $1
        ORDER BY generated_at DESC
        LIMIT 1
        """,
        user_id,
    )
    return _record_to_dict(row)


async def list_weekly_insights(user_id: str, limit: int = 4) -> list[dict[str, Any]]:
    rows = await _fetch(
        """
        SELECT *
        FROM weekly_insights
        WHERE user_id = $1
        ORDER BY generated_at DESC
        LIMIT $2
        """,
        user_id,
        limit,
    )
    return _rows_to_dicts(rows)


async def insert_pattern(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = str(payload.get("user_id") or "")
    if user_id:
        await ensure_user_exists(user_id)
    row = await _fetchrow(
        """
        INSERT INTO emotional_patterns (user_id, pattern_type, description, severity)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        payload.get("user_id"),
        payload.get("pattern_type"),
        payload.get("description"),
        payload.get("severity"),
    )
    return _record_to_dict(row) if row else payload


async def list_patterns(user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = await _fetch(
        """
        SELECT *
        FROM emotional_patterns
        WHERE user_id = $1
        ORDER BY detected_at DESC
        LIMIT $2
        """,
        user_id,
        limit,
    )
    return _rows_to_dicts(rows)


async def get_emotional_map(user_id: str, days: int = 30) -> dict[str, Any]:
    entries = await get_recent_entries(user_id, days=days)
    timeline = []
    for entry in reversed(entries[:30]):
        emotions = _normalize_emotions(entry.get("emotions"))
        timeline.append(
            {
                "date": (entry.get("created_at").date() if isinstance(entry.get("created_at"), datetime) else date.today()).isoformat(),
                "sentiment_score": float(entry.get("sentiment_score") or 0.0),
                "dominant_emotion": entry.get("dominant_emotion") or _dominant_emotion(emotions),
                "emotions": emotions,
                "snippet": str(entry.get("content") or "")[:140],
            }
        )

    labels = ["joy", "sadness", "fear", "anger", "surprise", "neutral", "disgust"]
    totals = {label: 0.0 for label in labels}
    count = max(len(entries[:7]), 1)
    for entry in entries[:7]:
        emotions = _normalize_emotions(entry.get("emotions"))
        for label in labels:
            totals[label] += float(emotions.get(label, 0.0))

    radar = [{"emotion": label, "score": round(totals[label] / count, 3)} for label in labels]
    patterns = await list_patterns(user_id, limit=12)
    insights = await list_weekly_insights(user_id, limit=4)
    return {"timeline": timeline, "radar": radar, "patterns": patterns, "weekly_insights": insights}
