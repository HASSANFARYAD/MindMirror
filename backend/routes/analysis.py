from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
from statistics import mean
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from rate_limit import limiter
from security import CurrentUser, get_current_user
from services.claude_service import get_weekly_insight
from services.memory_service import get_emotional_map, list_journal_entries, list_patterns, list_weekly_insights
from services.sentiment_service import analyze_preview

router = APIRouter()


class EmotionalMapPoint(BaseModel):
    """Return chart-ready data points for the dashboard timeline."""

    date: date
    sentiment_score: float
    dominant_emotion: str
    emotions: dict[str, float]
    cognitive_distortions: list[dict[str, Any]] = Field(default_factory=list)
    snippet: str | None = None


class PreviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


def _parse_created_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.min


def _normalize_emotions(value: Any) -> dict[str, float]:
    if isinstance(value, dict):
        return {str(key): float(val) for key, val in value.items()}
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        if isinstance(parsed, dict):
            return {str(key): float(val) for key, val in parsed.items()}
    return {}


def _normalize_distortions(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
        except Exception:
            return []
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    return []


def _dominant_emotion(emotions: dict[str, float]) -> str:
    if not emotions:
        return "neutral"
    return max(emotions.items(), key=lambda item: item[1])[0]


def _entry_sentiment(entry: dict[str, Any]) -> float:
    return float(entry.get("sentiment_score") or 0.0)


def _build_entry_metric(entry: dict[str, Any]) -> dict[str, Any]:
    emotions = _normalize_emotions(entry.get("emotions"))
    distortions = _normalize_distortions(entry.get("cognitive_distortions"))
    created = _parse_created_at(entry.get("created_at"))
    return {
        "created_at": created,
        "sentiment_score": _entry_sentiment(entry),
        "dominant_emotion": str(entry.get("dominant_emotion") or _dominant_emotion(emotions) or "neutral"),
        "emotion_from_distribution": _dominant_emotion(emotions),
        "emotions": emotions,
        "cognitive_distortions": distortions,
        "distortion_count": len(distortions),
        "content": str(entry.get("content") or ""),
    }


def _summarize_slice(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        return {
            "avg_sentiment": 0.0,
            "dominant_emotion": "neutral",
            "distortion_avg": 0.0,
            "entry_count": 0,
            "top_distortion": "none",
        }

    sentiments = [item["sentiment_score"] for item in entries]
    emotions = Counter(item["dominant_emotion"] for item in entries)
    distortions = [item["distortion_count"] for item in entries]
    distortion_types = Counter(distortion["type"] for item in entries for distortion in item["cognitive_distortions"] if distortion.get("type"))
    return {
        "avg_sentiment": round(mean(sentiments), 3),
        "dominant_emotion": emotions.most_common(1)[0][0] if emotions else "neutral",
        "distortion_avg": round(mean(distortions), 1),
        "entry_count": len(entries),
        "top_distortion": distortion_types.most_common(1)[0][0] if distortion_types else "none",
    }


def _build_growth_summary(start: dict[str, Any], now: dict[str, Any]) -> str:
    sentiment_delta = round(now["avg_sentiment"] - start["avg_sentiment"], 2)
    sentiment_phrase = "improved" if sentiment_delta >= 0 else "softened"

    if start["distortion_avg"] == 0 and now["distortion_avg"] == 0:
        distortion_phrase = "kept cognitive distortions at zero in your most recent entries"
    elif start["distortion_avg"] <= 0:
        distortion_phrase = f"now averages {now['distortion_avg']:.1f} distortions per entry"
    else:
        reduction = max(start["distortion_avg"] - now["distortion_avg"], 0.0)
        percent = round((reduction / start["distortion_avg"]) * 100) if start["distortion_avg"] else 0
        distortion_phrase = (
            f"reduced cognitive distortions from {start['distortion_avg']:.1f} to {now['distortion_avg']:.1f} per entry"
            if percent == 0
            else f"reduced cognitive distortions by {percent}% from {start['distortion_avg']:.1f} to {now['distortion_avg']:.1f} per entry"
        )

    return (
        f"Your emotional tone has {sentiment_phrase} from {start['avg_sentiment']:+.2f} to {now['avg_sentiment']:+.2f}, "
        f"your leading emotion shifted from {start['dominant_emotion']} to {now['dominant_emotion']}, and you've {distortion_phrase}."
    )


def _build_growth_story(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(entries) < 10:
        return None

    ordered = sorted((_build_entry_metric(entry) for entry in entries), key=lambda item: item["created_at"])
    start_slice = _summarize_slice(ordered[:5])
    now_slice = _summarize_slice(ordered[-5:])
    return {
        "show": True,
        "started": start_slice,
        "now": now_slice,
        "summary": _build_growth_summary(start_slice, now_slice),
    }


def _format_date(value: Any) -> str:
    created = _parse_created_at(value)
    if created == datetime.min:
        return ""
    return created.date().isoformat()


def _range_to_days(range_value: str) -> int | None:
    if range_value == "all":
        return None
    if range_value in {"7", "30"}:
        return int(range_value)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="range must be 7, 30, or all")


def _build_entries_summary(entries: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for entry in entries:
        metric = _build_entry_metric(entry)
        snippet = metric["content"].replace("\n", " ").strip()
        if len(snippet) > 160:
            snippet = f"{snippet[:157]}..."
        lines.append(
            f"- {metric['created_at'].date().isoformat()} | sentiment {metric['sentiment_score']:+.2f} | "
            f"emotion {metric['dominant_emotion']} | distortions {metric['distortion_count']} | {snippet}"
        )
    return "\n".join(lines)[:6000]


@router.get("/emotional-map")
async def emotional_map(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """Return 30-day emotional map data for the dashboard."""
    data = await get_emotional_map(current_user.id, days=30)
    data["patterns"] = data.get("patterns") or await list_patterns(current_user.id, limit=12)
    data["weekly_insights"] = data.get("weekly_insights") or await list_weekly_insights(current_user.id, limit=4)
    all_entries = await list_journal_entries(current_user.id, days=None)
    growth_story = _build_growth_story(all_entries)
    if growth_story is not None:
        data["growth_story"] = growth_story
    return data


@limiter.limit("30/minute")
@router.post("/preview")
async def preview_emotion(
    request: Request,
    payload: PreviewRequest,
) -> dict[str, Any]:
    """Return a lightweight emotional preview without writing to the database."""
    return await analyze_preview(payload.text)


@limiter.limit("5/hour")
@router.get("/export")
async def export_insights(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    range: str = "30",
) -> dict[str, Any]:
    """Return a therapist-ready export summary for the selected date range."""
    days = _range_to_days(range)
    entries = await list_journal_entries(current_user.id, days=days)
    metrics = [_build_entry_metric(entry) for entry in entries]
    ordered_metrics = sorted(metrics, key=lambda item: item["created_at"])

    sentiments = [item["sentiment_score"] for item in ordered_metrics]
    emotion_counts = Counter(item["dominant_emotion"] for item in ordered_metrics)
    distortion_counts = Counter(
        distortion["type"] for item in ordered_metrics for distortion in item["cognitive_distortions"] if distortion.get("type")
    )
    growth_moments = [
        f"{item['created_at'].date().isoformat()}: sentiment {item['sentiment_score']:+.2f} with {item['dominant_emotion']} leading and {item['distortion_count']} distortions"
        for item in ordered_metrics
        if item["sentiment_score"] > 0 or item["distortion_count"] == 0
    ][:6]

    entries_summary = _build_entries_summary(ordered_metrics)
    user_name = current_user.name or current_user.email
    weekly_insights_text = await get_weekly_insight(entries_summary, user_name, tone="weekly insight")
    therapist_summary = await get_weekly_insight(entries_summary, user_name, tone="therapist summary")

    if ordered_metrics:
        start_date = _format_date(ordered_metrics[0]["created_at"])
        end_date = _format_date(ordered_metrics[-1]["created_at"])
        average_sentiment = round(mean(sentiments), 3)
    else:
        start_date = ""
        end_date = ""
        average_sentiment = 0.0

    return {
        "range_key": range,
        "range_label": "All time" if range == "all" else f"Last {range} days",
        "date_range_covered": {
            "start": start_date,
            "end": end_date,
        },
        "generated_at": datetime.utcnow().isoformat(),
        "average_sentiment_score": average_sentiment,
        "dominant_emotions": [
            {"emotion": emotion, "count": count} for emotion, count in emotion_counts.most_common()
        ],
        "cognitive_distortions": [
            {"type": distortion, "count": count} for distortion, count in distortion_counts.most_common()
        ],
        "growth_moments_identified": growth_moments,
        "weekly_insights_text": weekly_insights_text,
        "total_journal_entries_analyzed": len(ordered_metrics),
        "therapist_summary": therapist_summary,
        "disclaimer": "This summary is informational only and is not a medical device or a substitute for professional care.",
    }
