from __future__ import annotations

import json
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from limits import limiter
from security import CurrentUser, get_current_user
from services.claude_service import stream_chat_response
from services.memory_service import (
    create_chat_thread,
    delete_chat_thread,
    get_chat_history,
    get_chat_thread,
    get_user_context,
    insert_chat_message,
    list_chat_threads,
    list_journal_entries,
    list_patterns,
    list_weekly_insights,
    update_chat_thread,
)

router = APIRouter()


class ChatMessageRequest(BaseModel):
    thread_id: str | None = None
    message: str = Field(min_length=1, max_length=2000)
    journal_entry_id: str | None = None


class ChatThreadCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    journal_entry_id: str | None = None


class ChatThreadUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


def _default_thread_title(message: str, journal_entry_id: str | None = None) -> str:
    if journal_entry_id:
        return "Journal follow-up"
    trimmed = " ".join(message.strip().split())
    return trimmed[:48] if trimmed else "New chat"


@router.get("/threads")
async def list_threads(
    current_user: CurrentUser = Depends(get_current_user),
    search: str | None = None,
    journal_only: bool = True,
) -> list[dict[str, Any]]:
    return await list_chat_threads(current_user.id, search=search, journal_only=journal_only)


@router.post("/threads")
async def create_thread(payload: ChatThreadCreateRequest, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    return await create_chat_thread(current_user.id, payload.title, payload.journal_entry_id)


@router.get("/threads/{thread_id}")
async def read_thread(thread_id: str, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    thread = await get_chat_thread(thread_id, current_user.id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Chat thread not found")
    return thread


@router.patch("/threads/{thread_id}")
async def rename_thread(
    thread_id: str,
    payload: ChatThreadUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    thread = await update_chat_thread(thread_id, current_user.id, payload.title)
    if thread is None:
        raise HTTPException(status_code=404, detail="Chat thread not found")
    return thread


@router.delete("/threads/{thread_id}")
async def remove_thread(thread_id: str, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, str]:
    await delete_chat_thread(thread_id, current_user.id)
    return {"status": "ok"}


@limiter.limit("30/minute")
@router.post("/message")
async def chat_message(
    request: Request,
    payload: ChatMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """Generate and stream a MindMirror response while persisting the conversation."""

    async def stream() -> AsyncGenerator[str, None]:
        journal_context = await _collect_context(current_user.id, payload.journal_entry_id, payload.thread_id)
        thread_id = payload.thread_id
        if thread_id is not None:
            existing_thread = await get_chat_thread(thread_id, current_user.id)
            if existing_thread is None:
                raise HTTPException(status_code=404, detail="Chat thread not found")
        if thread_id is None:
            created_thread = await create_chat_thread(
                current_user.id,
                _default_thread_title(payload.message, payload.journal_entry_id),
                payload.journal_entry_id,
            )
            thread_id = str(created_thread.get("id") or "")

        user_message_record = await insert_chat_message(
            {"user_id": current_user.id, "thread_id": thread_id, "role": "user", "content": payload.message}
        )
        assistant_chunks: list[str] = []
        async for token in stream_chat_response(
            payload.message,
            journal_context,
            journal_context.get("journal_entry"),
        ):
            assistant_chunks.append(token)
            yield f"data: {json.dumps({'type': 'token', 'value': token, 'thread_id': thread_id})}\n\n"
        assistant_record = await insert_chat_message(
            {"user_id": current_user.id, "thread_id": thread_id, "role": "assistant", "content": "".join(assistant_chunks)}
        )
        yield (
            f"data: {json.dumps({'type': 'done', 'thread_id': thread_id, 'user_message_id': user_message_record.get('id'), 'assistant_message_id': assistant_record.get('id')})}\n\n"
        )

    return StreamingResponse(stream(), media_type="text/event-stream")


async def _collect_context(user_id: str, journal_entry_id: str | None, thread_id: str | None) -> dict[str, Any]:
    """Build a compact emotional context block for local LLM prompt injection."""
    entries = await list_journal_entries(user_id, days=30)
    latest_entry = None
    if journal_entry_id:
        latest_entry = next((entry for entry in entries if str(entry.get("id")) == journal_entry_id), None)
    if latest_entry is None and entries:
        latest_entry = entries[0]
    messages = await get_chat_history(user_id, thread_id, limit=12) if thread_id else []
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
