from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import _mock_db


class TestEmotionalMap:
    async def test_emotional_map_empty(self, client: AsyncClient):
        resp = await client.get("/analysis/emotional-map")
        assert resp.status_code == 200
        data = resp.json()
        assert "timeline" in data
        assert "radar" in data
        assert "patterns" in data
        assert "weekly_insights" in data

    async def test_emotional_map_with_entries(self, client: AsyncClient):
        # Create some journal entries
        for i in range(5):
            await client.post(
                "/journal/entry",
                json={"content": f"Feeling number {i}"},
            )

        resp = await client.get("/analysis/emotional-map")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["timeline"]) == 5
        assert len(data["radar"]) == 7  # 7 emotion buckets

    async def test_radar_always_7_emotions(self, client: AsyncClient):
        resp = await client.get("/analysis/emotional-map")
        radar = resp.json()["radar"]
        emotions = [r["emotion"] for r in radar]
        assert "joy" in emotions
        assert "sadness" in emotions
        assert "fear" in emotions
        assert "anger" in emotions
        assert "surprise" in emotions
        assert "neutral" in emotions
        assert "disgust" in emotions

    async def test_timeline_sorted_by_date(self, client: AsyncClient):
        await client.post("/journal/entry", json={"content": "Older entry."})
        await client.post("/journal/entry", json={"content": "Newer entry."})

        resp = await client.get("/analysis/emotional-map")
        timeline = resp.json()["timeline"]
        if len(timeline) >= 2:
            assert timeline[0]["date"] <= timeline[-1]["date"]


class TestPreview:
    async def test_preview_returns_emotion(self, client: AsyncClient):
        resp = await client.post(
            "/analysis/preview",
            json={"text": "I feel really happy today!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "dominant_emotion" in data
        assert "sentiment_score" in data
        assert data["dominant_emotion"] in ("joy", "sadness", "fear", "anger", "surprise", "neutral", "disgust")

    async def test_preview_no_distortions(self, client: AsyncClient):
        """Preview response should not include cognitive_distortions."""
        resp = await client.post(
            "/analysis/preview",
            json={"text": "I always fail. This is terrible."},
        )
        assert "cognitive_distortions" not in resp.json()

    async def test_preview_empty_text(self, client: AsyncClient):
        resp = await client.post("/analysis/preview", json={"text": ""})
        assert resp.status_code == 422

    async def test_preview_too_long(self, client: AsyncClient):
        resp = await client.post(
            "/analysis/preview",
            json={"text": "A" * 501},
        )
        assert resp.status_code == 422


class TestExport:
    async def test_export_empty(self, client: AsyncClient):
        resp = await client.get("/analysis/export?range=30")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_journal_entries_analyzed"] == 0
        assert "therapist_summary" in data
        assert "weekly_insights_text" in data
        assert "disclaimer" in data

    async def test_export_with_entries(self, client: AsyncClient):
        await client.post(
            "/journal/entry",
            json={"content": "Had a productive day. Feeling good."},
        )

        resp = await client.get("/analysis/export?range=30")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_journal_entries_analyzed"] == 1
        assert data["average_sentiment_score"] is not None

    async def test_export_invalid_range(self, client: AsyncClient):
        resp = await client.get("/analysis/export?range=invalid")
        assert resp.status_code == 400

    async def test_export_all_time(self, client: AsyncClient):
        resp = await client.get("/analysis/export?range=all")
        assert resp.status_code == 200
        assert resp.json()["range_key"] == "all"

    async def test_export_structure(self, client: AsyncClient):
        resp = await client.get("/analysis/export?range=7")
        data = resp.json()
        assert "date_range_covered" in data
        assert "average_sentiment_score" in data
        assert "dominant_emotions" in data
        assert "cognitive_distortions" in data
        assert "growth_moments_identified" in data
        assert "generated_at" in data
