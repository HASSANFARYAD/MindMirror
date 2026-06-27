from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from tests.conftest import _mock_db


class TestChatThreads:
    async def test_create_thread(self, client: AsyncClient):
        resp = await client.post(
            "/chat/threads",
            json={"title": "My first chat", "journal_entry_id": None},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "My first chat"
        assert "id" in data

    async def test_create_thread_with_journal(self, client: AsyncClient):
        # Create a journal entry first
        journal_resp = await client.post(
            "/journal/entry",
            json={"content": "Journal for chat thread."},
        )
        journal_id = journal_resp.json()["id"]

        resp = await client.post(
            "/chat/threads",
            json={"title": "Follow-up", "journal_entry_id": journal_id},
        )
        assert resp.status_code == 200
        assert resp.json()["journal_entry_id"] == journal_id

    async def test_list_threads_empty(self, client: AsyncClient):
        resp = await client.get("/chat/threads")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_threads_after_creation(self, client: AsyncClient):
        await client.post("/chat/threads", json={"title": "Thread 1"})
        await client.post("/chat/threads", json={"title": "Thread 2"})
        resp = await client.get("/chat/threads?journal_only=false")
        assert len(resp.json()) == 2

    async def test_list_threads_filter_by_search(self, client: AsyncClient):
        await client.post("/chat/threads", json={"title": "Anxiety talk"})
        await client.post("/chat/threads", json={"title": "Gratitude journal"})
        resp = await client.get("/chat/threads?search=anxiety&journal_only=false")
        titles = [t["title"] for t in resp.json()]
        assert "Anxiety talk" in titles
        assert "Gratitude journal" not in titles

    async def test_get_thread(self, client: AsyncClient):
        create_resp = await client.post("/chat/threads", json={"title": "My thread"})
        thread_id = create_resp.json()["id"]

        resp = await client.get(f"/chat/threads/{thread_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == thread_id
        assert "messages" in resp.json()

    async def test_get_nonexistent_thread(self, client: AsyncClient):
        resp = await client.get("/chat/threads/00000000-0000-0000-0000-000000000999")
        assert resp.status_code == 404

    async def test_rename_thread(self, client: AsyncClient):
        create_resp = await client.post("/chat/threads", json={"title": "Old title"})
        thread_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/chat/threads/{thread_id}",
            json={"title": "New title"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New title"

    async def test_delete_thread(self, client: AsyncClient):
        create_resp = await client.post("/chat/threads", json={"title": "To delete"})
        thread_id = create_resp.json()["id"]

        resp = await client.delete(f"/chat/threads/{thread_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Verify it's gone
        get_resp = await client.get(f"/chat/threads/{thread_id}")
        assert get_resp.status_code == 404


class TestChatMessage:
    async def test_send_message_creates_thread(self, client: AsyncClient):
        resp = await client.post(
            "/chat/message",
            json={"message": "I'm feeling anxious about my presentation."},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        body = resp.text
        assert "data:" in body
        assert "type" in body
        assert "token" in body or "done" in body

    async def test_send_message_in_thread(self, client: AsyncClient):
        thread_resp = await client.post("/chat/threads", json={"title": "Test chat"})
        thread_id = thread_resp.json()["id"]

        resp = await client.post(
            "/chat/message",
            json={"message": "Hello!", "thread_id": thread_id},
        )
        assert resp.status_code == 200

        # Verify message was stored
        thread = await client.get(f"/chat/threads/{thread_id}")
        messages = thread.json().get("messages", [])
        assert len(messages) > 0
        assert messages[-2]["role"] == "user"
        assert messages[-2]["content"] == "Hello!"

    async def test_send_empty_message(self, client: AsyncClient):
        resp = await client.post(
            "/chat/message",
            json={"message": ""},
        )
        assert resp.status_code == 422

    async def test_send_to_nonexistent_thread(self, client: AsyncClient):
        resp = await client.post(
            "/chat/message",
            json={
                "message": "Hello",
                "thread_id": "00000000-0000-0000-0000-000000000999",
            },
        )
        assert resp.status_code == 404
