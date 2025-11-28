import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("ANYIO_BACKEND", "asyncio")

from app.main import app  # noqa: E402
from app.api.deps.decode_guard import AuthenticatedUser, get_current_user  # noqa: E402


@pytest.fixture
def test_user() -> AuthenticatedUser:
    """Reusable authenticated user for dependency overrides."""
    return AuthenticatedUser(
        user_id="user-test-123",
        email="qa@example.com",
        username="qa-user",
        role="user",
    )


@pytest.fixture(autouse=True)
def override_auth_dependency(test_user: AuthenticatedUser):
    """
    Override the decode auth dependency so protected routes
    can be exercised without hitting external auth services.
    """

    async def _override_current_user(
        request=None, required_roles=None, response=None
    ) -> AuthenticatedUser:
        return test_user

    app.dependency_overrides[get_current_user] = _override_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client():
    """Shared HTTPX async client with FastAPI lifespan handling."""
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
