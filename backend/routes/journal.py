from __future__ import annotations

import base64

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status

from rate_limit import limiter
from models.journal import JournalCreate, JournalEntryOut
from security import CurrentUser, get_current_user
from services.memory_service import get_journal_entry, list_journal_entries, save_journal_entry
from services.pattern_service import analyze_user_patterns
from services.sentiment_service import analyze_entry
from services.whisper_service import transcribe_audio

router = APIRouter()
MAX_AUDIO_BYTES = 10 * 1024 * 1024


@limiter.limit("10/minute")
@router.post("/voice-transcribe")
async def voice_transcribe(
    request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    """Transcribe an uploaded voice note and return plain text."""
    content = await file.read()
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio file is too large")
    extension = (file.filename or "voice.webm").rsplit(".", 1)[-1]
    transcript = await transcribe_audio(content, extension)
    return {"transcript": transcript}


@limiter.limit("10/minute")
@router.post("/entry", response_model=JournalEntryOut)
async def create_journal_entry(
    request: Request,
    payload: JournalCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
) -> JournalEntryOut:
    """Store a journal entry, run analysis, and schedule pattern detection."""
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Journal content cannot be empty")
    transcript = None
    if payload.voice_file:
        try:
            voice_bytes = base64.b64decode(payload.voice_file)
            if len(voice_bytes) > MAX_AUDIO_BYTES:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio file is too large")
            transcript = await transcribe_audio(voice_bytes)
            if transcript:
                content = f"{content}\n\n[Voice transcript]\n{transcript}"
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Voice transcription failed: {exc}") from exc

    analysis = await analyze_entry(content)
    entry = await save_journal_entry(current_user.id, content, {**analysis, "voice_transcript": transcript})
    background_tasks.add_task(_run_pattern_analysis, current_user.id)
    return JournalEntryOut(**entry)


async def _run_pattern_analysis(user_id: str) -> None:
    """Recompute user patterns in the background after a journal submission."""
    entries = await list_journal_entries(user_id, days=30)
    await analyze_user_patterns(user_id, entries)


@router.get("/entry/{entry_id}", response_model=JournalEntryOut)
async def read_journal_entry(entry_id: str, current_user: CurrentUser = Depends(get_current_user)) -> JournalEntryOut:
    """Load a single stored journal entry."""
    entry = await get_journal_entry(entry_id, current_user.id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return JournalEntryOut(**entry)


@router.get("/entries", response_model=list[JournalEntryOut])
async def list_user_entries(current_user: CurrentUser = Depends(get_current_user)) -> list[JournalEntryOut]:
    """Return the user's recent journal entries."""
    entries = await list_journal_entries(current_user.id, days=30)
    return [JournalEntryOut(**entry) for entry in entries]
