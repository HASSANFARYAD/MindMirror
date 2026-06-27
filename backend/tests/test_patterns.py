from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from services.pattern_service import (
    _dominant_emotion,
    _parse_created_at,
    analyze_user_patterns,
)


def make_entry(
    *,
    content: str = "Had a normal day.",
    sentiment_score: float = 0.0,
    emotions: dict | None = None,
    created_at: datetime | None = None,
) -> dict:
    return {
        "content": content,
        "sentiment_score": sentiment_score,
        "emotions": emotions or {"joy": 0.3, "sadness": 0.1},
        "created_at": (created_at or datetime.utcnow()).isoformat(),
    }


class TestUtilities:
    def test_dominant_emotion(self):
        assert _dominant_emotion({"joy": 0.8, "sadness": 0.2}) == "joy"

    def test_dominant_emotion_empty(self):
        assert _dominant_emotion(None) == "neutral"
        assert _dominant_emotion({}) == "neutral"

    def test_parse_created_at_datetime(self):
        dt = datetime(2025, 6, 1, 12, 0, 0)
        parsed = _parse_created_at(dt)
        assert parsed == dt

    def test_parse_created_at_iso_string(self):
        parsed = _parse_created_at("2025-06-01T12:00:00")
        assert parsed.year == 2025
        assert parsed.month == 6

    def test_parse_created_at_empty(self):
        assert _parse_created_at("") == datetime.min
        assert _parse_created_at(None) == datetime.min

    def test_parse_created_at_z_suffix(self):
        parsed = _parse_created_at("2025-06-01T12:00:00Z")
        assert parsed.year == 2025


class TestTriggerDetection:
    async def test_work_trigger(self):
        """Work mentioned multiple times with negative sentiment should be flagged."""
        entries = [
            make_entry(content="Work has been so stressful lately.", sentiment_score=-0.5),
            make_entry(content="Work is overwhelming me today.", sentiment_score=-0.6),
        ]
        result = await analyze_user_patterns("user-1", entries)
        assert len(result["patterns"]) >= 1
        trigger_types = [p["pattern_type"] for p in result["patterns"]]
        assert "trigger" in trigger_types

    async def test_multiple_triggers(self):
        entries = [
            make_entry(content="Work is terrible and family is stressing me out.", sentiment_score=-0.6),
            make_entry(content="Work is still awful.", sentiment_score=-0.4),
            make_entry(content="Money problems are getting to me.", sentiment_score=-0.5),
        ]
        result = await analyze_user_patterns("user-1", entries)
        trigger_types = [p["pattern_type"] for p in result["patterns"]]
        assert "trigger" in trigger_types

    async def test_no_trigger_for_positive(self):
        """Work mentioned with positive sentiment should NOT be flagged."""
        entries = [
            make_entry(content="Work is going great!", sentiment_score=0.7),
        ]
        result = await analyze_user_patterns("user-1", entries)
        trigger_types = [p["pattern_type"] for p in result["patterns"]]
        assert "trigger" not in trigger_types


class TestCycleDetection:
    async def test_cycle_on_low_day(self):
        """Repeated low sentiment on same weekday should be flagged."""
        now = datetime.utcnow()
        entries = [
            make_entry(  # Monday
                sentiment_score=-0.5,
                created_at=now - timedelta(days=now.weekday() + 7),
            ),
            make_entry(
                sentiment_score=-0.6,
                created_at=now - timedelta(days=now.weekday()),
            ),
        ]
        result = await analyze_user_patterns("user-1", entries)
        cycle_types = [p["pattern_type"] for p in result["patterns"]]
        assert "cycle" in cycle_types

    async def test_no_cycle_with_mixed_scores(self):
        now = datetime.utcnow()
        entries = [
            make_entry(sentiment_score=0.5, created_at=now - timedelta(days=8)),
            make_entry(sentiment_score=0.3, created_at=now - timedelta(days=1)),
        ]
        result = await analyze_user_patterns("user-1", entries)
        cycle_types = [p["pattern_type"] for p in result["patterns"]]
        assert "cycle" not in cycle_types


class TestGrowthDetection:
    async def test_growth_after_positive_streak(self):
        entries = [
            make_entry(sentiment_score=0.1, created_at=datetime.utcnow() - timedelta(days=i))
            for i in range(5, 0, -1)
        ]
        result = await analyze_user_patterns("user-1", entries)
        growth_types = [p["pattern_type"] for p in result["patterns"]]
        assert "growth" in growth_types

    async def test_no_growth_with_mixed(self):
        entries = [
            make_entry(sentiment_score=0.3, created_at=datetime.now() - timedelta(days=4)),
            make_entry(sentiment_score=-0.2, created_at=datetime.now() - timedelta(days=3)),
            make_entry(sentiment_score=0.5, created_at=datetime.now() - timedelta(days=2)),
            make_entry(sentiment_score=0.4, created_at=datetime.now() - timedelta(days=1)),
            make_entry(sentiment_score=0.6, created_at=datetime.now()),
        ]
        result = await analyze_user_patterns("user-1", entries)
        growth_types = [p["pattern_type"] for p in result["patterns"]]
        assert "growth" not in growth_types


class TestAlertDetection:
    async def test_alert_after_three_low_days(self):
        today = datetime.utcnow()
        entries = [
            make_entry(sentiment_score=-0.6, created_at=today - timedelta(days=2)),
            make_entry(sentiment_score=-0.7, created_at=today - timedelta(days=1)),
            make_entry(sentiment_score=-0.8, created_at=today),
        ]
        result = await analyze_user_patterns("user-1", entries)
        alert_types = [p["pattern_type"] for p in result["patterns"]]
        assert "alert" in alert_types

    async def test_no_alert_with_interrupted_streak(self):
        today = datetime.utcnow()
        entries = [
            make_entry(sentiment_score=-0.6, created_at=today - timedelta(days=2)),
            make_entry(sentiment_score=0.2, created_at=today - timedelta(days=1)),
            make_entry(sentiment_score=-0.8, created_at=today),
        ]
        result = await analyze_user_patterns("user-1", entries)
        alert_types = [p["pattern_type"] for p in result["patterns"]]
        assert "alert" not in alert_types


class TestEmptyEntries:
    async def test_no_entries(self):
        result = await analyze_user_patterns("user-1", [])
        assert result["patterns"] == []
        assert "alert_condition" in result
        assert result["dominant_emotion"] == "neutral"
        assert result["avg_sentiment"] == 0.0

    async def test_single_entry(self):
        result = await analyze_user_patterns("user-1", [make_entry()])
        assert isinstance(result["patterns"], list)
        assert result["avg_sentiment"] is not None

    async def test_always_returns_insight_data(self):
        result = await analyze_user_patterns("user-1", [])
        assert "dominant_emotion" in result
        assert "avg_sentiment" in result
        assert "top_triggers" in result
        assert "cbt_recommendation" in result
