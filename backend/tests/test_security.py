from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException, Request
from fastapi.responses import Response

from security import (
    COOKIE_MAX_AGE,
    COOKIE_NAME,
    CurrentUser,
    _decode_token,
    clear_auth_cookie,
    create_access_token,
    get_current_user,
    hash_password,
    set_auth_cookie,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "TestPassword123!"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_invalid_hash_returns_false(self):
        assert verify_password("anything", "not-a-valid-hash") is False

    def test_empty_password_fails(self):
        assert verify_password("", "") is False


class TestJWT:
    def test_create_token(self):
        token = create_access_token("user-1", "user@test.com")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_token_decodes(self):
        token = create_access_token("user-1", "user@test.com")
        payload = jwt.decode(token, "test-secret-value-for-tests-only", algorithms=["HS256"])
        assert payload["sub"] == "user-1"
        assert payload["email"] == "user@test.com"
        assert "exp" in payload

    def test_token_expires(self):
        token = create_access_token("user-1", "user@test.com", expires_hours=0)
        payload = jwt.decode(token, "test-secret-value-for-tests-only", algorithms=["HS256"], options={"verify_exp": False})
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp <= datetime.now(timezone.utc) + timedelta(seconds=5)

    def test_decode_token_valid(self):
        token = create_access_token("user-1", "user@test.com")
        uid, email = _decode_token(token)
        assert uid == "user-1"
        assert email == "user@test.com"

    def test_decode_token_invalid(self):
        with pytest.raises(HTTPException) as exc:
            _decode_token("not-a-valid-token")
        assert exc.value.status_code == 401

    def test_decode_token_missing_payload(self):
        token = jwt.encode({"foo": "bar"}, "test-secret-value-for-tests-only", algorithm="HS256")
        with pytest.raises(HTTPException) as exc:
            _decode_token(token)
        assert exc.value.status_code == 401


class TestAuthCookie:
    def test_set_auth_cookie(self):
        resp = Response()
        token = create_access_token("user-1", "user@test.com")
        set_auth_cookie(resp, token)

        set_cookie = resp.headers.get("set-cookie")
        assert set_cookie is not None
        assert COOKIE_NAME in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie
        assert f"Max-Age={COOKIE_MAX_AGE}" in set_cookie
        assert "secure" not in set_cookie.lower()  # not in production mode

    def test_set_auth_cookie_secure(self):
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
            resp = Response()
            token = create_access_token("user-1", "user@test.com")
            set_auth_cookie(resp, token)
            assert "secure" in resp.headers.get("set-cookie", "").lower()

    def test_clear_auth_cookie(self):
        resp = Response()
        clear_auth_cookie(resp)
        set_cookie = resp.headers.get("set-cookie")
        assert set_cookie is not None
        assert COOKIE_NAME in set_cookie
        assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()


class TestGetCurrentUser:
    async def test_with_bearer_header(self):
        token = create_access_token(
            TEST_USER_ID := "00000000-0000-0000-0000-000000000001",
            "test@mindmirror.app",
        )
        request = MagicMock(spec=Request)
        request.cookies = {}

        with patch("services.memory_service.get_user_by_id") as mock_get:
            mock_get.return_value = {"id": TEST_USER_ID, "email": "test@mindmirror.app", "name": "Test"}
            result = await get_current_user(request, authorization=f"Bearer {token}")
            assert isinstance(result, CurrentUser)
            assert result.id == TEST_USER_ID
            assert result.email == "test@mindmirror.app"

    async def test_with_cookie(self):
        token = create_access_token(
            TEST_USER_ID := "00000000-0000-0000-0000-000000000001",
            "test@mindmirror.app",
        )
        request = MagicMock(spec=Request)
        request.cookies = {COOKIE_NAME: token}

        with patch("services.memory_service.get_user_by_id") as mock_get:
            mock_get.return_value = {"id": TEST_USER_ID, "email": "test@mindmirror.app", "name": "Test"}
            result = await get_current_user(request)
            assert isinstance(result, CurrentUser)
            assert result.id == TEST_USER_ID

    async def test_no_auth_provided(self):
        request = MagicMock(spec=Request)
        request.cookies = {}
        with pytest.raises(HTTPException) as exc:
            await get_current_user(request)
        assert exc.value.status_code == 401

    async def test_cookie_preferred_over_header(self):
        """If both cookie and header are present, cookie takes priority."""
        user_id = "00000000-0000-0000-0000-000000000001"
        token = create_access_token(user_id, "test@mindmirror.app")
        request = MagicMock(spec=Request)
        request.cookies = {COOKIE_NAME: token}

        with patch("services.memory_service.get_user_by_id") as mock_get:
            mock_get.return_value = {"id": user_id, "email": "test@mindmirror.app", "name": "Test"}
            result = await get_current_user(request)
            assert isinstance(result, CurrentUser)

    async def test_user_not_found(self):
        token = create_access_token("nonexistent-user", "missing@test.com")
        request = MagicMock(spec=Request)
        request.cookies = {COOKIE_NAME: token}

        with patch("services.memory_service.get_user_by_id") as mock_get:
            mock_get.return_value = None
            with pytest.raises(HTTPException) as exc:
                await get_current_user(request)
            assert exc.value.status_code == 401

    async def test_invalid_token_in_header(self):
        request = MagicMock(spec=Request)
        request.cookies = {}
        with pytest.raises(HTTPException) as exc:
            await get_current_user(request, authorization="Bearer not-a-valid-jwt")
        assert exc.value.status_code == 401
