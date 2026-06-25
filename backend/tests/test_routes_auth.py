from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import MockDB, TEST_USER_EMAIL, TEST_USER_NAME, TEST_PASSWORD, _mock_db


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        payload = {
            "email": "newuser@test.com",
            "name": "New User",
            "password": "StrongPass123!",
        }
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "user" in data
        assert "token" not in data
        assert data["user"]["email"] == "newuser@test.com"
        assert data["user"]["name"] == "New User"

        # Cookie should be set
        assert "mindmirror_token" in resp.cookies

    async def test_register_duplicate(self, client: AsyncClient):
        payload = {
            "email": TEST_USER_EMAIL,
            "name": "Dup",
            "password": TEST_PASSWORD,
        }
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"email": "not-an-email", "name": "Test", "password": "StrongPass123!"},
        )
        assert resp.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"email": "test@test.com", "name": "Test", "password": "123"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def _setup_user(self):
        """Register a user in the mock DB with a known password."""
        from security import hash_password

        uid = "login-test-user-id"
        _mock_db.users[uid] = {
            "id": uid,
            "email": "login@test.com",
            "name": "Login User",
            "password_hash": hash_password("Password123!"),
        }

    async def test_login_success(self, client: AsyncClient):
        await self._setup_user()
        resp = await client.post(
            "/auth/login",
            json={"email": "login@test.com", "password": "Password123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "user" in data
        assert "token" not in data
        assert data["user"]["email"] == "login@test.com"

        # Cookie should be set
        assert "mindmirror_token" in resp.cookies

    async def test_login_wrong_password(self, client: AsyncClient):
        await self._setup_user()
        resp = await client.post(
            "/auth/login",
            json={"email": "login@test.com", "password": "WrongPassword!"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@test.com", "password": "Password123!"},
        )
        assert resp.status_code == 401


class TestMe:
    async def test_me_authenticated(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] is not None
        assert data["email"] is not None

    async def test_me_returns_user_data(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        data = resp.json()
        assert data["email"] == TEST_USER_EMAIL


class TestLogout:
    async def test_logout_clears_cookie(self, client: AsyncClient):
        resp = await client.post("/auth/logout")
        assert resp.status_code == 200
        assert resp.json() == {"detail": "Logged out"}
        set_cookie = resp.headers.get("set-cookie", "")
        assert "mindmirror_token" in set_cookie
        assert "Max-Age=0" in set_cookie
