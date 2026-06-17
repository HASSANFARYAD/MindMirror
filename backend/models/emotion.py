from datetime import date, datetime

from pydantic import BaseModel


class EmotionPoint(BaseModel):
    """Represent one day of chart-ready emotional data."""

    date: date
    sentiment_score: float
    dominant_emotion: str
    emotions: dict[str, float]
    snippet: str | None = None


class PatternOut(BaseModel):
    """Represent a detected pattern for dashboard cards."""

    id: str
    pattern_type: str
    description: str
    severity: str
    detected_at: datetime | None = None


class WeeklyInsightOut(BaseModel):
    """Represent an AI-generated weekly summary."""

    id: str
    week_start: date | None = None
    dominant_emotion: str | None = None
    avg_sentiment: float | None = None
    top_triggers: list[dict] | None = None
    cbt_recommendation: str | None = None
    generated_at: datetime | None = None

