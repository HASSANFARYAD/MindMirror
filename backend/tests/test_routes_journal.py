from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestCreateJournalEntry:
    async def test_create_entry_success(self, client: AsyncClient):
        resp = await client.post(
            "/journal/entry",
            json={"content": "Today was a really good day. I felt happy and productive."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Today was a really good day. I felt happy and productive."
        assert "sentiment_score" in data
        assert "sentiment_label" in data
        assert "emotions" in data
        assert "cognitive_distortions" in data
        assert data["user_id"] is not None

    async def test_create_entry_empty_content(self, client: AsyncClient):
        resp = await client.post(
            "/journal/entry",
            json={"content": ""},
        )
        assert resp.status_code == 422

    async def test_create_entry_whitespace(self, client: AsyncClient):
        resp = await client.post(
            "/journal/entry",
            json={"content": "   "},
        )
        assert resp.status_code == 400

    async def test_create_entry_very_long(self, client: AsyncClient):
        long_text = "A" * 10001
        resp = await client.post(
            "/journal/entry",
            json={"content": long_text},
        )
        assert resp.status_code == 422

    async def test_create_entry_no_body(self, client: AsyncClient):
        resp = await client.post("/journal/entry", json={})
        assert resp.status_code == 422


class TestGetJournalEntry:
    async def test_get_entry_by_id(self, client: AsyncClient):
        create_resp = await client.post(
            "/journal/entry",
            json={"content": "Entry to retrieve by ID."},
        )
        entry_id = create_resp.json()["id"]

        resp = await client.get(f"/journal/entry/{entry_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == entry_id

    async def test_get_nonexistent_entry(self, client: AsyncClient):
        resp = await client.get("/journal/entry/00000000-0000-0000-0000-000000000999")
        assert resp.status_code == 404

    async def test_get_entry_invalid_uuid(self, client: AsyncClient):
        resp = await client.get("/journal/entry/not-a-uuid")
        assert resp.status_code in (404, 422)


class TestListEntries:
    async def test_list_entries_empty(self, client: AsyncClient):
        resp = await client.get("/journal/entries")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_entries_after_creation(self, client: AsyncClient):
        await client.post("/journal/entry", json={"content": "First entry."})
        await client.post("/journal/entry", json={"content": "Second entry."})

        resp = await client.get("/journal/entries")
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) == 2


class TestVoiceTranscribe:
    async def test_transcribe_no_file(self, client: AsyncClient):
        resp = await client.post("/journal/voice-transcribe")
        assert resp.status_code in (400, 422)

    async def test_transcribe_too_large(self, client: AsyncClient):
        # Create a file that exceeds the 10MB limit
        large_data = b"0" * (11 * 1024 * 1024)
        resp = await client.post(
            "/journal/voice-transcribe",
            files={"file": ("voice.webm", large_data, "audio/webm")},
        )
        assert resp.status_code == 413
