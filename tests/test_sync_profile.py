import pytest

from app.api.services.sync_profile_service import SyncProfileService

pytestmark = pytest.mark.anyio("asyncio")


@pytest.mark.anyio
async def test_create_profile_endpoint_returns_prepared_payload(async_client, monkeypatch):
    """Smoke test ensuring the sync profile endpoint returns the service payload."""

    async def fake_prepare(self, user_id: str):
        return {
            "method": "createProfile(string,string,bytes)",
            "params": {"wallet": "0x000000000000000000000000000000000000dead"},
            "calldata": "0x1234",
        }

    monkeypatch.setattr(
        SyncProfileService, "create_profile_prepare", fake_prepare, raising=False
    )

    response = await async_client.post("/api/v1/sync/create-profile")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["method"] == "createProfile(string,string,bytes)"
