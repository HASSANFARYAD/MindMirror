from datetime import datetime

from pydantic import BaseModel, Field


class JournalCreate(BaseModel):
    """Validate a new journal entry request."""

    content: str = Field(min_length=1, max_length=10000)
    voice_file: str | None = None


class JournalEntryOut(BaseModel):
    """Return the stored journal entry and its analysis payload."""

    id: str
    user_id: str
    content: str
    voice_transcript: str | None = None
    sentiment_score: float | None = None
    sentiment_label: str | None = None
    emotions: dict[str, float] | None = None
    cognitive_distortions: list[dict] | None = None
    created_at: datetime | None = None
