from __future__ import annotations

import json
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.claude_service import stream_chat_response
from services.memory_service import (
    get_chat_history,
    get_user_context,
    insert_chat_message,
    list_journal_entries,
    list_patterns,
    list_weekly_insights,
)

router = APIRouter()


class ChatMessageRequest(BaseModel):
    """Validate the chat message payload used by the frontend."""

    user_id: str
    message: str = Field(min_length=1)
    journal_entry_id: str | None = None


@router.post("/message")
async def chat_message(payload: ChatMessageRequest) -> StreamingResponse:
    """Generate and stream a MindMirror response while persisting the conversation."""

    async def stream() -> AsyncGenerator[str, None]:
        journal_context = await _collect_context(payload.user_id, payload.journal_entry_id)
        user_message_record = await insert_chat_message(
            {"user_id": payload.user_id, "role": "user", "content": payload.message}
        )
        assistant_chunks: list[str] = []
        async for token in stream_chat_response(
            payload.message,
            journal_context,
            journal_context.get("journal_entry"),
        ):
            assistant_chunks.append(token)
            yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"
        assistant_record = await insert_chat_message(
            {"user_id": payload.user_id, "role": "assistant", "content": "".join(assistant_chunks)}
        )
        yield (
            f"data: {json.dumps({'type': 'done', 'user_message_id': user_message_record.get('id'), 'assistant_message_id': assistant_record.get('id')})}\n\n"
        )

    return StreamingResponse(stream(), media_type="text/event-stream")


async def _collect_context(user_id: str, journal_entry_id: str | None) -> dict[str, Any]:
    """Build a compact emotional context block for local LLM prompt injection."""
    entries = await list_journal_entries(user_id, days=30)
    latest_entry = None
    if journal_entry_id:
        latest_entry = next((entry for entry in entries if str(entry.get("id")) == journal_entry_id), None)
    if latest_entry is None and entries:
        latest_entry = entries[0]
    messages = await get_chat_history(user_id, limit=12)
    patterns = await list_patterns(user_id, limit=6)
    insights = await list_weekly_insights(user_id, limit=1)
    user_context = await get_user_context(user_id)
    return {
        "name": user_context.get("name") or "there",
        "trend": user_context.get("trend") or "mixed",
        "dominant_emotion": user_context.get("dominant_emotion") or "neutral",
        "triggers": user_context.get("triggers") or [pattern.get("description") for pattern in patterns[:3]],
        "last_journal": user_context.get("last_journal") or (latest_entry or {}).get("content", "")[:200],
        "journal_entry": (latest_entry or {}).get("content", ""),
        "recent_messages": messages,
        "weekly_insights": insights,
    }
