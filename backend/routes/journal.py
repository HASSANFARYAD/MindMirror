from __future__ import annotations

import base64

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from models.journal import JournalCreate, JournalEntryOut
from services.memory_service import get_journal_entry, list_journal_entries, save_journal_entry
from services.pattern_service import analyze_user_patterns
from services.sentiment_service import analyze_entry
from services.whisper_service import transcribe_audio

router = APIRouter()


@router.post("/voice-transcribe")
async def voice_transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    """Transcribe an uploaded voice note and return plain text."""
    content = await file.read()
    extension = (file.filename or "voice.webm").rsplit(".", 1)[-1]
    transcript = await transcribe_audio(content, extension)
    return {"transcript": transcript}


@router.post("/entry", response_model=JournalEntryOut)
async def create_journal_entry(payload: JournalCreate, background_tasks: BackgroundTasks) -> JournalEntryOut:
    """Store a journal entry, run analysis, and schedule pattern detection."""
    content = payload.content.strip()
    transcript = None
    if payload.voice_file:
        try:
            voice_bytes = base64.b64decode(payload.voice_file)
            transcript = await transcribe_audio(voice_bytes)
            if transcript:
                content = f"{content}\n\n[Voice transcript]\n{transcript}"
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Voice transcription failed: {exc}") from exc

    analysis = await analyze_entry(content)
    entry = await save_journal_entry(payload.user_id, content, {**analysis, "voice_transcript": transcript})
    background_tasks.add_task(_run_pattern_analysis, payload.user_id)
    return JournalEntryOut(**entry)


async def _run_pattern_analysis(user_id: str) -> None:
    """Recompute user patterns in the background after a journal submission."""
    entries = await list_journal_entries(user_id, days=30)
    await analyze_user_patterns(user_id, entries)


@router.get("/entry/{entry_id}", response_model=JournalEntryOut)
async def read_journal_entry(entry_id: str) -> JournalEntryOut:
    """Load a single stored journal entry."""
    entry = await get_journal_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return JournalEntryOut(**entry)


@router.get("/entries/{user_id}", response_model=list[JournalEntryOut])
async def list_user_entries(user_id: str) -> list[JournalEntryOut]:
    """Return the user's recent journal entries."""
    entries = await list_journal_entries(user_id, days=30)
    return [JournalEntryOut(**entry) for entry in entries]
