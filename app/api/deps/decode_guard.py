"""
Decode Authentication Guard for FastAPI.
Provides session validation, Redis caching, and role-based access control.
"""

import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.cache import get_cache_service

logger = get_logger(__name__)

# Security scheme for session ID
security = HTTPBearer(auto_error=False)

# User role types
UserRole = str  # 'user' | 'admin' | 'moderator'


class AuthenticatedUser:
    """Authenticated user data structure."""

    def __init__(self, user_id: str, email: str, username: str, role: UserRole):
        self.user_id = user_id
        self.email = email
        self.username = username
        self.role = role
        self.display_name: Optional[str] = None
        self.bio: Optional[str] = None
        self.avatar_ipfs_hash: Optional[str] = None
        self.last_login: Optional[datetime] = None
        self.is_active: Optional[bool] = None


class SessionCacheDoc:
    """Session cache document structure."""

    def __init__(
        self,
        session_token: str,
        access_token: str,
        user: Optional[AuthenticatedUser] = None,
        expires_at: Optional[datetime] = None,
    ):
        self.session_token = session_token
        self.access_token = access_token
        self.user = user
        self.expires_at = expires_at


class AuthServiceResponse:
    """Auth service response structure."""

    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ):
        self.success = success
        self.data = data
        self.message = message


class DecodeAuthGuard:
    """Decode authentication guard with session validation and caching."""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 5 * 60 * 1000  # 5 minutes in milliseconds
        self.auth_service_url = (
            f"http://{settings.DECODE_AUTH_HOST}:{settings.DECODE_AUTH_PORT}"
        )

    def extract_session_id_from_cookie(self, request: Request) -> Optional[str]:
        """Extract session ID directly from cookies."""
        session_id = request.cookies.get("deid_session_id")

        # Debug logging
        all_cookies = dict(request.cookies)
        logger.debug(
            f"Cookie extraction - Request origin: {request.headers.get('origin', 'N/A')}, "
            f"Request host: {request.headers.get('host', 'N/A')}, "
            f"All cookies: {list(all_cookies.keys())}, "
            f"Session ID found: {session_id is not None}"
        )

        if not session_id:
            logger.warning(
                f"Session ID not found in cookies. Available cookies: {list(all_cookies.keys())}, "
                f"Origin: {request.headers.get('origin', 'N/A')}, "
                f"Host: {request.headers.get('host', 'N/A')}"
            )

        return session_id

    async def get_session_from_redis(
        self, session_id: str
    ) -> Optional[SessionCacheDoc]:
        """Get session data from Redis cache."""
        try:
            cache_service = await get_cache_service()
            session_key = f"deid_session_id:{session_id}"
            session_data = await cache_service.get(session_key)

            if not session_data:
                return None

            # The session data from Redis only contains access_token and session_token
            # We need to validate the access_token to get user data
            return SessionCacheDoc(
                session_token=session_data["session_token"],
                access_token=session_data["access_token"],
                user=None,  # Will be populated after token validation
                expires_at=None,  # Not stored in Redis, will be calculated
            )
        except Exception as e:
            logger.error(f"Failed to retrieve session from Redis: {e}")
            return None

    async def validate_access_token(self, access_token: str) -> AuthenticatedUser:
        """Validate access token with Decode auth service."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.auth_service_url}/auth/info/by-access-token",
                    json={"access_token": access_token},
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "DEID-Backend/1.0",
                    },
                )

                # Parse response once
                data = response.json()

                if response.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail={
                            "message": "Invalid or expired access token",
                            "error": "TOKEN_EXPIRED",
                        },
                    )

                if not data.get("success") or not data.get("data"):
                    raise HTTPException(
                        status_code=401,
                        detail={
                            "message": "Invalid access token",
                            "error": "INVALID_TOKEN",
                        },
                    )

                user_data = data["data"]

                return AuthenticatedUser(
                    user_id=user_data["_id"],
                    email=user_data["email"],
                    username=user_data["username"],
                    role=user_data.get("role", "user"),
                )

        except httpx.TimeoutException:
            logger.error("Auth service timeout")
            raise HTTPException(
                status_code=503,
                detail={
                    "message": "Authentication service timeout",
                    "error": "SERVICE_TIMEOUT",
                },
            )
        except httpx.ConnectError:
            logger.error("Auth service connection error")
            raise HTTPException(
                status_code=503,
                detail={
                    "message": "Authentication service unavailable",
                    "error": "SERVICE_UNAVAILABLE",
                },
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Token validation failed",
                    "error": "VALIDATION_ERROR",
                },
            )

    async def validate_session(self, session_id: str) -> AuthenticatedUser:
        """Validate session and return authenticated user."""
        # Check in-memory cache first
        cached = self.cache.get(session_id)
        if cached and cached["expires_at"] > datetime.now().timestamp() * 1000:
            return cached["user"]

        # Get session data from Redis
        session_data = await self.get_session_from_redis(session_id)
        if not session_data:
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Session not found or expired",
                    "error": "SESSION_NOT_FOUND",
                },
            )

        # Validate access token and get user data
        user = await self.validate_access_token(session_data.access_token)

        # Cache the result
        self.cache[session_id] = {
            "user": user,
            "expires_at": datetime.now().timestamp() * 1000 + self.cache_ttl,
        }

        return user

    async def refresh_session_and_rotate_cookie(
        self,
        old_session_id: str,
        session_token: str,
        response: Optional[Response] = None,
    ) -> Dict[str, Any]:
        """
        Refresh session with Decode auth, rotate Redis session, set new cookie.
        Returns dict with new_session_id and access_token.
        """
        refresh_url = f"{settings.DECODE_BACKEND_URL}/auth/session/refresh"
        try:
            async with httpx.AsyncClient(timeout=7.0) as client:
                r = await client.post(
                    refresh_url,
                    json={"session_token": session_token},
                    headers={"Content-Type": "application/json"},
                )
                data = r.json()
                if (
                    r.status_code != 200
                    or not data.get("success")
                    or not data.get("data")
                ):
                    raise HTTPException(
                        status_code=401,
                        detail={
                            "message": "Session refresh failed",
                            "error": "REFRESH_FAILED",
                        },
                    )

                payload = data["data"]
                new_access_token = payload.get("access_token")
                new_session_token = payload.get("session_token")
                expires_at_str = payload.get("expires_at")
                if not new_access_token or not new_session_token or not expires_at_str:
                    raise HTTPException(
                        status_code=401,
                        detail={
                            "message": "Invalid refresh payload",
                            "error": "REFRESH_INVALID",
                        },
                    )

                # Compute TTL
                from dateutil import parser

                exp_dt = parser.isoparse(expires_at_str)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                ttl_seconds = max(1, int((exp_dt - now).total_seconds()))

                # Rotate Redis key: delete old, set new
                new_session_id = str(uuid.uuid4())[:8]
                new_key = f"deid_session_id:{new_session_id}"
                old_key = f"deid_session_id:{old_session_id}"

                cache_service = await get_cache_service()
                await cache_service.delete(old_key)
                await cache_service.set(
                    new_key,
                    {
                        "access_token": new_access_token,
                        "session_token": new_session_token,
                    },
                    expire=ttl_seconds,
                )

                # Set cookie if response provided
                if response is not None:
                    expires_cookie = now + timedelta(seconds=ttl_seconds)

                    # Get effective cookie domain based on environment
                    cookie_domain = settings.get_cookie_domain()

                    cookie_kwargs = {
                        "key": "deid_session_id",
                        "value": new_session_id,
                        "expires": expires_cookie,
                        "secure": settings.COOKIE_SECURE,
                        "httponly": settings.COOKIE_HTTPONLY,
                        "samesite": settings.COOKIE_SAMESITE,
                        "path": settings.COOKIE_PATH,
                    }

                    # Only set domain if configured
                    if cookie_domain:
                        cookie_kwargs["domain"] = cookie_domain
                        logger.debug(f"Cookie refresh: domain set to {cookie_domain}")
                    else:
                        logger.debug("Cookie refresh: domain not set (host-only)")

                    response.set_cookie(**cookie_kwargs)
                    logger.info(
                        f"Cookie refreshed: new_session_id={new_session_id}, "
                        f"domain={cookie_domain or 'None (host-only)'}, "
                        f"expires={expires_cookie}"
                    )

                # Update in-memory cache: remove old
                if old_session_id in self.cache:
                    del self.cache[old_session_id]

                return {
                    "new_session_id": new_session_id,
                    "access_token": new_access_token,
                }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Refresh session error: {e}")
            raise HTTPException(
                status_code=401,
                detail={"message": "Session refresh failed", "error": "REFRESH_ERROR"},
            )

    def check_role_access(
        self, user: AuthenticatedUser, required_roles: Optional[List[str]] = None
    ) -> None:
        """Check if user has required role access."""
        if not required_roles or len(required_roles) == 0:
            return  # No role requirements

        if user.role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": f"Access denied. Required roles: {', '.join(required_roles)}. Your role: {user.role}",
                    "error": "INSUFFICIENT_PERMISSIONS",
                },
            )

    async def authenticate(
        self,
        request: Request,
        required_roles: Optional[List[str]] = None,
        response: Optional[Response] = None,
    ) -> AuthenticatedUser:
        """Main authentication method."""
        # Extract session ID directly from cookie
        session_id = self.extract_session_id_from_cookie(request)

        # Enhanced debug logging
        logger.debug(
            f"Authentication attempt - Method: {request.method}, "
            f"URL: {request.url}, "
            f"Origin: {request.headers.get('origin', 'N/A')}, "
            f"Host: {request.headers.get('host', 'N/A')}, "
            f"Session ID: {session_id or 'NOT FOUND'}"
        )

        if not session_id:
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Session ID is required",
                    "error": "MISSING_SESSION_ID",
                },
            )

        try:
            # Try validate session and get user
            try:
                user = await self.validate_session(session_id)
            except HTTPException as e:
                # If token expired, attempt refresh using stored session_token
                if e.status_code == 401:
                    session_doc = await self.get_session_from_redis(session_id)
                    if session_doc and session_doc.session_token:
                        rotate = await self.refresh_session_and_rotate_cookie(
                            session_id, session_doc.session_token, response
                        )
                        # Use new access token to get user
                        user = await self.validate_access_token(rotate["access_token"])
                    else:
                        raise
                else:
                    raise
            # Check role-based access
            self.check_role_access(user, required_roles)

            # Log successful authentication
            logger.info(
                f"User {user.user_id} ({user.role}) accessed {request.method} {request.url}"
            )

            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Authentication failed",
                    "error": "AUTHENTICATION_ERROR",
                },
            )

    def clear_cache(self) -> None:
        """Clear in-memory cache."""
        self.cache.clear()

    def get_cache_size(self) -> int:
        """Get cache size."""
        return len(self.cache)


# Global guard instance
decode_auth_guard = DecodeAuthGuard()


# Dependency function for FastAPI
async def get_current_user(
    request: Request,
    required_roles: Optional[List[str]] = None,
    response: Response = None,
) -> AuthenticatedUser:
    """
    FastAPI dependency to get current authenticated user.

    Args:
        request: FastAPI request object
        required_roles: Optional list of required roles

    Returns:
        AuthenticatedUser: Authenticated user data

    Raises:
        HTTPException: If authentication fails
    """
    logger.debug("Getting current user via dependency")
    return await decode_auth_guard.authenticate(request, required_roles, response)


# Decorator functions for role-based access
def require_roles(*roles: str):
    """
    Decorator to require specific roles for an endpoint.

    Usage:
        @require_roles("admin", "moderator")
        async def admin_endpoint(current_user: AuthenticatedUser = Depends(get_current_user)):
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object in the arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # Try to get from kwargs
                request = kwargs.get("request")

            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            # Authenticate with required roles
            user = await decode_auth_guard.authenticate(request, list(roles))

            # Add user to kwargs
            kwargs["current_user"] = user

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_permissions(*permissions: str):
    """
    Decorator to require specific permissions for an endpoint.
    Note: This is a placeholder - implement permission logic as needed.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Implement permission checking logic
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def public_endpoint(func: Callable) -> Callable:
    """
    Decorator to mark an endpoint as public (no authentication required).
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper


# Convenience dependency functions
async def get_current_user_dependency() -> AuthenticatedUser:
    """Dependency for getting current user without role requirements."""
    return await get_current_user


async def get_admin_user(request: Request) -> AuthenticatedUser:
    """Dependency for getting current admin user."""
    return await decode_auth_guard.authenticate(request, ["admin"])


async def get_moderator_user(request: Request) -> AuthenticatedUser:
    """Dependency for getting current moderator or admin user."""
    return await decode_auth_guard.authenticate(request, ["admin", "moderator"])
