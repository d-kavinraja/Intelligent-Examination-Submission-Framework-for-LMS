import pytest

from app.services.moodle_client import MoodleClient


@pytest.mark.asyncio
async def test_get_user_by_username_returns_first_user(monkeypatch):
    client = MoodleClient(base_url="https://moodle.example.com", token="t1")

    async def fake_get_users_by_field(field, value, token=None):
        assert field == "username"
        assert value == "student1"
        return [
            {"username": "student1", "email": "student1@example.com"},
            {"username": "student1-2", "email": "other@example.com"},
        ]

    monkeypatch.setattr(client, "get_users_by_field", fake_get_users_by_field)

    user = await client.get_user_by_username("student1")

    assert user is not None
    assert user["username"] == "student1"


@pytest.mark.asyncio
async def test_get_user_by_username_returns_none_when_not_found(monkeypatch):
    client = MoodleClient(base_url="https://moodle.example.com", token="t1")

    async def fake_get_users_by_field(field, value, token=None):
        return []

    monkeypatch.setattr(client, "get_users_by_field", fake_get_users_by_field)

    user = await client.get_user_by_username("missing.user")

    assert user is None
