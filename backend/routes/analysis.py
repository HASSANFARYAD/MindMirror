from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from security import CurrentUser, get_current_user
from services.memory_service import get_emotional_map, list_patterns, list_weekly_insights

router = APIRouter()


class EmotionalMapPoint(BaseModel):
    """Return chart-ready data points for the dashboard timeline."""

    date: date
    sentiment_score: float
    dominant_emotion: str
    emotions: dict[str, float]
    snippet: str | None = None


@router.get("/emotional-map")
async def emotional_map(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """Return 30-day emotional map data for the dashboard."""
    data = await get_emotional_map(current_user.id, days=30)
    data["patterns"] = data.get("patterns") or await list_patterns(current_user.id, limit=12)
    data["weekly_insights"] = data.get("weekly_insights") or await list_weekly_insights(current_user.id, limit=4)
    return data


def _to_point(entry: dict[str, Any]) -> EmotionalMapPoint:
    """Convert a journal entry row into a chart point."""
    created = entry.get("created_at")
    if isinstance(created, str):
        created_date = datetime.fromisoformat(created.replace("Z", "+00:00")).date()
    elif isinstance(created, datetime):
        created_date = created.date()
    else:
        created_date = date.today()
    return EmotionalMapPoint(
        date=created_date,
        sentiment_score=float(entry.get("sentiment_score") or 0.0),
        dominant_emotion=_dominant_emotion(entry.get("emotions") or {}),
        emotions=entry.get("emotions") or {},
        snippet=(entry.get("content") or "")[:140],
    )


def _dominant_emotion(emotions: dict[str, float]) -> str:
    """Return the strongest label from an emotion distribution."""
    if not emotions:
        return "neutral"
    return max(emotions.items(), key=lambda item: item[1])[0]


def _weekly_emotion_averages(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute radar chart averages from the latest entries."""
    labels = ["joy", "sadness", "fear", "anger", "surprise", "neutral", "disgust"]
    totals = {label: 0.0 for label in labels}
    count = max(len(entries[:7]), 1)
    for entry in entries[:7]:
        emotions = entry.get("emotions") or {}
        for label in labels:
            totals[label] += float(emotions.get(label, 0.0))
    return [{"emotion": label, "score": round(totals[label] / count, 3)} for label in labels]
