"""
Tests for MoodleClient.get_user_by_field.

All HTTP interactions are mocked — no real Moodle server needed.

Covers:
  - Successful user lookup (returns user dict with email)
  - No user found (returns None)
  - Moodle API error handling
  - Missing token error
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.moodle_client import MoodleClient, MoodleAPIError


@pytest.fixture
def client():
    """MoodleClient with a test base URL and token."""
    return MoodleClient(
        base_url="https://moodle.test.edu",
        token="test_admin_token_123",
    )


# ======================================================================
# get_user_by_field
# ======================================================================

class TestGetUserByField:
    @pytest.mark.asyncio
    async def test_returns_user_when_found(self, client):
        """Moodle returns a list with one user dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": 42,
                "username": "22007928",
                "fullname": "Santhan Kumar",
                "email": "santhan@university.edu",
            }
        ]
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_http):
            user = await client.get_user_by_field("username", "22007928")

        assert user is not None
        assert user["email"] == "santhan@university.edu"
        assert user["id"] == 42

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, client):
        """Moodle returns an empty list when no user matches."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_http):
            user = await client.get_user_by_field("username", "nonexistent")

        assert user is None

    @pytest.mark.asyncio
    async def test_raises_on_moodle_error(self, client):
        """Moodle returns an error dict (e.g. invalid function)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "exception": "webservice_access_exception",
            "errorcode": "accessexception",
            "message": "Access denied",
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_http):
            with pytest.raises(MoodleAPIError):
                await client.get_user_by_field("username", "22007928")

    @pytest.mark.asyncio
    async def test_raises_when_no_token(self):
        """Should raise MoodleAPIError if no token is set."""
        client_no_token = MoodleClient(
            base_url="https://moodle.test.edu",
            token=None,
        )
        with pytest.raises(MoodleAPIError, match="No token"):
            await client_no_token.get_user_by_field("username", "22007928")

    @pytest.mark.asyncio
    async def test_correct_params_sent(self, client):
        """Verify the WS function name and params are correct."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "username": "test"}]
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_http):
            await client.get_user_by_field("username", "22007928")

        call_kwargs = mock_http.post.call_args
        sent_data = call_kwargs.kwargs.get("data") or call_kwargs[1].get("data")
        assert sent_data["wsfunction"] == "core_user_get_users_by_field"
        assert sent_data["field"] == "username"
        assert sent_data["values[0]"] == "22007928"
