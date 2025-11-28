import urllib.parse

import pytest

from app.api.services.social_link_service import SocialLinkService
from app.core.config import settings

pytestmark = pytest.mark.anyio("asyncio")


@pytest.mark.anyio
async def test_x_oauth_url_generates_pkce_and_caches_verifier(
    async_client, monkeypatch
):
    """Validate that the X OAuth endpoint triggers PKCE generation and cache storage."""

    monkeypatch.setattr(settings, "X_CLIENT_ID", "client_test", raising=False)
    monkeypatch.setattr(
        settings, "X_REDIRECT_URI", "https://example.com/callback", raising=False
    )

    verifier_store = {}

    async def fake_cache_set(key, value, expire=None):
        verifier_store[key] = {"value": value, "expire": expire}
        return True

    def fake_pkce_pair(self):
        return ("verifier123", "challenge456")

    monkeypatch.setattr(
        "app.api.services.social_link_service.cache_service.set", fake_cache_set
    )
    monkeypatch.setattr(
        SocialLinkService, "_generate_pkce_pair", fake_pkce_pair, raising=False
    )

    response = await async_client.get("/api/v1/social/x/oauth-url")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    parsed = urllib.parse.urlparse(data["oauth_url"])
    query = urllib.parse.parse_qs(parsed.query)
    assert query["code_challenge"][0] == "challenge456"
    assert query["state"][0].startswith("deid_user-test-123")

    # Code verifier should be stored with a TTL (10 minutes = 600 seconds)
    assert len(verifier_store) == 1
    stored = next(iter(verifier_store.values()))
    assert stored["value"] == "verifier123"
    assert stored["expire"] == 600
