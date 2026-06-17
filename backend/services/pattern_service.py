from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from services.memory_service import insert_pattern, upsert_weekly_insight


def _dominant_emotion(emotions: dict[str, float] | None) -> str:
    """Return the highest-scoring emotion label from a stored emotion payload."""
    if not emotions:
        return "neutral"
    return max(emotions.items(), key=lambda item: item[1])[0]


def _parse_created_at(value: Any) -> datetime:
    """Normalize Supabase timestamps or datetime objects for comparison and sorting."""
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str) and value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    return datetime.min


async def analyze_user_patterns(user_id: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze recent entries for trigger patterns, cycles, growth, and alert states."""
    window_start = datetime.utcnow() - timedelta(days=14)
    recent = [entry for entry in entries if _parse_created_at(entry.get("created_at")) >= window_start]
    recent = sorted(recent, key=lambda item: _parse_created_at(item.get("created_at")))

    trigger_counter: Counter[str] = Counter()
    dow_scores: defaultdict[int, list[float]] = defaultdict(list)
    streak = 0
    patterns: list[dict[str, Any]] = []
    alert_condition = False

    trigger_terms = ["work", "family", "sleep", "money", "school", "relationship", "health"]

    for entry in recent:
        content = (entry.get("content") or "").lower()
        sentiment = float(entry.get("sentiment_score") or 0.0)
        created = entry.get("created_at")
        if created:
            dt = datetime.fromisoformat(str(created).replace("Z", "+00:00")).replace(tzinfo=None)
            dow_scores[dt.weekday()].append(sentiment)
        for term in trigger_terms:
            if term in content and sentiment < 0:
                trigger_counter[term] += 1
        if sentiment < -0.5:
            streak += 1
        else:
            streak = 0
        if streak >= 3:
            alert_condition = True

    recurring_triggers = [term for term, count in trigger_counter.items() if count >= 2]
    if recurring_triggers:
        description = f"Recurring negative dips appear around: {', '.join(recurring_triggers)}."
        patterns.append(
            {
                "pattern_type": "trigger",
                "description": description,
                "severity": "medium" if len(recurring_triggers) < 3 else "high",
            }
        )
        await insert_pattern(
            {
                "user_id": user_id,
                "pattern_type": "trigger",
                "description": description,
                "severity": "medium" if len(recurring_triggers) < 3 else "high",
            }
        )

    cyclic_day = None
    cyclic_score = None
    for weekday, values in dow_scores.items():
        if len(values) >= 2:
            avg = sum(values) / len(values)
            if cyclic_score is None or avg < cyclic_score:
                cyclic_day = weekday
                cyclic_score = avg
    if cyclic_day is not None and cyclic_score is not None and cyclic_score < -0.2:
        weekday_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][cyclic_day]
        description = f"Sentiment tends to dip on {weekday_name}s."
        patterns.append(
            {
                "pattern_type": "cycle",
                "description": description,
                "severity": "medium" if cyclic_score > -0.5 else "high",
            }
        )
        await insert_pattern(
            {
                "user_id": user_id,
                "pattern_type": "cycle",
                "description": description,
                "severity": "medium" if cyclic_score > -0.5 else "high",
            }
        )

    last_five = recent[-5:]
    if len(last_five) == 5 and all(float(item.get("sentiment_score") or 0.0) > 0 for item in last_five):
        description = "You have 5 days of sustained positive movement."
        patterns.append({"pattern_type": "growth", "description": description, "severity": "low"})
        await insert_pattern(
            {
                "user_id": user_id,
                "pattern_type": "growth",
                "description": description,
                "severity": "low",
            }
        )

    if alert_condition:
        description = "Three consecutive days fell below -0.5. Consider reaching out to someone you trust."
        patterns.append({"pattern_type": "alert", "description": description, "severity": "high"})
        await insert_pattern(
            {
                "user_id": user_id,
                "pattern_type": "alert",
                "description": description,
                "severity": "high",
            }
        )

    dominant_emotion_counts = Counter(
        _dominant_emotion(entry.get("emotions")) for entry in recent if entry.get("emotions")
    )
    dominant = dominant_emotion_counts.most_common(1)[0][0] if dominant_emotion_counts else "neutral"
    avg_sentiment = round(
        sum(float(entry.get("sentiment_score") or 0.0) for entry in recent) / max(len(recent), 1),
        3,
    )
    top_triggers = [{"term": term, "count": count} for term, count in trigger_counter.most_common(3)]
    recommendation = "Try a short thought record: situation, automatic thought, evidence, and balanced thought."
    await upsert_weekly_insight(
        {
            "user_id": user_id,
            "week_start": date.today() - timedelta(days=7),
            "dominant_emotion": dominant,
            "avg_sentiment": avg_sentiment,
            "top_triggers": top_triggers,
            "cbt_recommendation": recommendation,
        }
    )

    return {
        "patterns": patterns,
        "alert_condition": alert_condition,
        "dominant_emotion": dominant,
        "avg_sentiment": avg_sentiment,
        "top_triggers": top_triggers,
        "cbt_recommendation": recommendation,
    }
