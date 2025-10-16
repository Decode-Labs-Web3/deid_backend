"""
Social Link Service Layer.
Contains business logic for social account verification and linking with MongoDB storage.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from app.api.dto.social_dto import (
    DiscordUserInfoDTO,
    GitHubUserInfoDTO,
    GoogleUserInfoDTO,
    SocialLinkDataDTO,
    SocialLinkStatsDTO,
    SocialPlatform,
    SocialVerificationResponseDTO,
    VerificationStatus,
)
from app.core.config import settings
from app.core.logging import get_logger
from app.domain.models.social_link import (
    SocialLinkCreateModel,
    SocialLinkQueryModel,
    SocialLinkUpdateModel,
)
from app.domain.repositories.social_link_repository import social_link_repository
from app.infrastructure.blockchain.signature_utils import sign_message_with_private_key

logger = get_logger(__name__)


class SocialLinkService:
    """Service class for social account verification and linking."""

    def __init__(self):
        """Initialize social link service."""
        self.discord_api_base = "https://discord.com/api/v10"
        self.discord_oauth_base = "https://discord.com/oauth2"
        self.github_api_base = "https://api.github.com"
        self.github_oauth_base = "https://github.com/login/oauth"
        self.google_oauth_base = "https://accounts.google.com/o/oauth2/v2"
        self.google_api_base = "https://www.googleapis.com"

    async def get_discord_oauth_url(self, user_id: str) -> str:
        """
        Generate Discord OAuth authorization URL.

        Args:
            user_id: User's wallet address or unique identifier

        Returns:
            Discord OAuth authorization URL
        """
        if not settings.DISCORD_CLIENT_ID:
            raise ValueError("Discord client ID not configured")

        # Create state parameter with user_id for CSRF protection
        state = f"deid_{user_id}"

        params = {
            "client_id": settings.DISCORD_CLIENT_ID,
            "redirect_uri": settings.DISCORD_REDIRECT_URI,
            "response_type": "code",
            "scope": "identify email",
            "state": state,
        }

        auth_url = f"{self.discord_oauth_base}/authorize?{urlencode(params)}"
        logger.info(f"Generated Discord OAuth URL for user {user_id}")

        return auth_url

    async def handle_discord_oauth_callback(
        self, code: str, state: str
    ) -> SocialVerificationResponseDTO:
        """
        Handle Discord OAuth callback and verify user account.

        Args:
            code: Authorization code from Discord
            state: State parameter for CSRF protection

        Returns:
            SocialVerificationResponseDTO with verification data
        """
        try:
            print(f"🔍 DEBUG: Discord OAuth callback received")
            print(f"   Code: {code[:20]}...")
            print(f"   State: {state}")

            # Extract user_id from state parameter
            if not state.startswith("deid_"):
                print(f"❌ Invalid state parameter: {state}")
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Invalid state parameter",
                    data=None,
                    request_id=None,
                )

            user_id = state[5:]  # Remove "deid_" prefix
            print(f"   Extracted user_id: {user_id}")

            # Exchange code for access token
            print(f"🔄 Exchanging code for access token...")
            access_token = await self._exchange_discord_code_for_token(code)
            if not access_token:
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Failed to exchange code for access token",
                    data=None,
                    request_id=None,
                )

            # Get Discord user info
            discord_user = await self._get_discord_user_info(access_token)
            if not discord_user:
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Failed to get Discord user information",
                    data=None,
                    request_id=None,
                )

            # Check if social link already exists
            existing_link = await social_link_repository.get_social_link(
                user_id=user_id, platform=SocialPlatform.DISCORD
            )

            if existing_link:
                # Check if this is the same Discord account
                if existing_link.account_id == discord_user.id:
                    # Same account - return already linked status
                    return SocialVerificationResponseDTO(
                        success=True,
                        status_code=200,
                        message="Discord account already linked",
                        data={
                            **self._convert_to_dto(existing_link),
                            "status": VerificationStatus.ALREADY_LINKED.value,
                        },
                        request_id=str(uuid.uuid4()),
                    )
                else:
                    # Different Discord account - update with new verification
                    signature_data = await self._generate_verification_signature(
                        account_id=discord_user.id
                    )

                    if signature_data:
                        update_data = SocialLinkUpdateModel(
                            username=discord_user.username,
                            email=discord_user.email,
                            signature=signature_data["signature"],
                            verification_hash=signature_data["verification_hash"],
                            status=VerificationStatus.VERIFIED,
                        )

                        updated_link = await social_link_repository.update_social_link(
                            user_id=user_id,
                            platform=SocialPlatform.DISCORD,
                            update_data=update_data,
                        )

                        if updated_link:
                            return SocialVerificationResponseDTO(
                                success=True,
                                status_code=200,
                                message="Discord account re-verified successfully",
                                data=self._convert_to_dto(updated_link),
                                request_id=str(uuid.uuid4()),
                            )
            else:
                # Create new social link
                signature_data = await self._generate_verification_signature(
                    account_id=discord_user.id
                )

                if signature_data:
                    # Create avatar URL if avatar hash exists
                    avatar_url = None
                    if discord_user.avatar:
                        avatar_url = f"https://cdn.discordapp.com/avatars/{discord_user.id}/{discord_user.avatar}.png"

                    create_data = SocialLinkCreateModel(
                        user_id=user_id,
                        platform=SocialPlatform.DISCORD,
                        account_id=discord_user.id,
                        username=discord_user.username,
                        email=discord_user.email,
                        display_name=f"{discord_user.username}#{discord_user.discriminator}",
                        avatar_url=avatar_url,
                        signature=signature_data["signature"],
                        verification_hash=signature_data["verification_hash"],
                        status=VerificationStatus.VERIFIED,
                    )

                    created_link = await social_link_repository.create_social_link(
                        create_data
                    )

                    if created_link:
                        return SocialVerificationResponseDTO(
                            success=True,
                            status_code=200,
                            message="Discord account verified successfully",
                            data=self._convert_to_dto(created_link),
                            request_id=str(uuid.uuid4()),
                        )

            return SocialVerificationResponseDTO(
                success=False,
                status_code=500,
                message="Failed to save verification data",
                data=None,
                request_id=None,
            )

        except Exception as e:
            logger.error(f"Error in Discord OAuth callback: {e}")
            return SocialVerificationResponseDTO(
                success=False,
                status_code=500,
                message=f"Internal server error: {str(e)}",
                data=None,
                request_id=None,
            )

    async def _exchange_discord_code_for_token(self, code: str) -> Optional[str]:
        """Exchange Discord authorization code for access token."""
        try:
            if not settings.DISCORD_CLIENT_SECRET:
                raise ValueError("Discord client secret not configured")

            # Use proper form data encoding
            data = {
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.DISCORD_REDIRECT_URI,
            }

            print(f"🔍 DEBUG: Exchanging code for token")
            print(f"   Client ID: {settings.DISCORD_CLIENT_ID}")
            print(f"   Client Secret: {settings.DISCORD_CLIENT_SECRET[:10]}...")
            print(f"   Code: {code[:20]}...")
            print(f"   Redirect URI: {settings.DISCORD_REDIRECT_URI}")
            print(f"   Token URL: {self.discord_oauth_base}/token")
            print(f"   Request Data: {data}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try different approaches
                print(f"🔄 Attempting token exchange...")

                # Method 1: Standard form data
                try:
                    response = await client.post(
                        f"{self.discord_api_base}/oauth2/token",
                        data=data,
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                            "User-Agent": "DEiD-Social-Link/1.0",
                        },
                    )

                    print(f"🔍 DEBUG: Token exchange response")
                    print(f"   Status Code: {response.status_code}")
                    print(
                        f"   Content-Type: {response.headers.get('content-type', 'unknown')}"
                    )
                    print(f"   Response Length: {len(response.text)}")
                    print(f"   Response Preview: {response.text[:200]}...")

                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            token_data = response.json()
                            print(f"✅ JSON response received: {token_data}")

                            access_token = token_data.get("access_token")
                            if access_token:
                                print(
                                    f"✅ Access token received: {access_token[:20]}..."
                                )
                                return access_token
                            else:
                                print(f"❌ No access token in response: {token_data}")
                                return None
                        else:
                            print(
                                f"❌ Non-JSON response received (Content-Type: {content_type})"
                            )
                            print(
                                f"   This suggests Discord doesn't recognize the redirect URI"
                            )
                            return None
                    else:
                        print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                        return None

                except httpx.HTTPStatusError as e:
                    print(f"❌ HTTP Error: {e.response.status_code}")
                    print(f"   Response: {e.response.text[:200]}")
                    return None
                except Exception as e:
                    print(f"❌ Request Error: {e}")
                    return None

        except Exception as e:
            logger.error(f"Error exchanging Discord code for token: {e}")
            print(f"🔍 DEBUG: Exception details")
            print(f"   Exception type: {type(e).__name__}")
            print(f"   Exception message: {str(e)}")
            return None

    async def _get_discord_user_info(
        self, access_token: str
    ) -> Optional[DiscordUserInfoDTO]:
        """Get Discord user information using access token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.discord_api_base}/users/@me",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()

                user_data = response.json()
                return DiscordUserInfoDTO(
                    id=user_data["id"],
                    username=user_data["username"],
                    discriminator=user_data.get("discriminator", "0"),
                    email=user_data.get("email"),
                    verified=user_data.get("verified", False),
                    avatar=user_data.get("avatar"),
                )

        except Exception as e:
            logger.error(f"Error getting Discord user info: {e}")
            return None

    async def get_github_oauth_url(self, user_id: str) -> str:
        """
        Generate GitHub OAuth authorization URL.

        Args:
            user_id: User's wallet address or unique identifier

        Returns:
            GitHub OAuth authorization URL
        """
        if not settings.GITHUB_CLIENT_ID:
            raise ValueError("GitHub client ID not configured")

        # Create state parameter with user_id for CSRF protection
        state = f"deid_{user_id}"

        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "user:email",
            "state": state,
        }

        auth_url = f"{self.github_oauth_base}/authorize?{urlencode(params)}"
        logger.info(f"Generated GitHub OAuth URL for user {user_id}")

        return auth_url

    async def handle_github_oauth_callback(
        self, code: str, state: str
    ) -> SocialVerificationResponseDTO:
        """
        Handle GitHub OAuth callback and verify user account.

        Args:
            code: Authorization code from GitHub
            state: State parameter for CSRF protection

        Returns:
            SocialVerificationResponseDTO with verification data
        """
        try:
            print(f"🔍 DEBUG: GitHub OAuth callback received")
            print(f"   Code: {code[:20]}...")
            print(f"   State: {state}")

            # Extract user_id from state parameter
            if not state.startswith("deid_"):
                print(f"❌ Invalid state parameter: {state}")
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Invalid state parameter",
                    data=None,
                    request_id=None,
                )

            user_id = state[5:]  # Remove "deid_" prefix
            print(f"   Extracted user_id: {user_id}")

            # Exchange code for access token
            print(f"🔄 Exchanging code for access token...")
            access_token = await self._exchange_github_code_for_token(code)
            if not access_token:
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Failed to exchange code for access token",
                    data=None,
                    request_id=None,
                )

            # Get GitHub user info
            github_user = await self._get_github_user_info(access_token)
            if not github_user:
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Failed to get GitHub user information",
                    data=None,
                    request_id=None,
                )

            # Check if social link already exists
            existing_link = await social_link_repository.get_social_link(
                user_id=user_id, platform=SocialPlatform.GITHUB
            )

            if existing_link:
                # Check if this is the same GitHub account
                if existing_link.account_id == str(github_user.id):
                    # Same account - return already linked status
                    return SocialVerificationResponseDTO(
                        success=True,
                        status_code=200,
                        message="GitHub account already linked",
                        data={
                            **self._convert_to_dto(existing_link),
                            "status": VerificationStatus.ALREADY_LINKED.value,
                        },
                        request_id=str(uuid.uuid4()),
                    )
                else:
                    # Different GitHub account - update with new verification
                    signature_data = await self._generate_verification_signature(
                        account_id=str(github_user.id)
                    )

                    if signature_data:
                        update_data = SocialLinkUpdateModel(
                            username=github_user.login,
                            email=github_user.email,
                            signature=signature_data["signature"],
                            verification_hash=signature_data["verification_hash"],
                            status=VerificationStatus.VERIFIED,
                        )

                        updated_link = await social_link_repository.update_social_link(
                            user_id=user_id,
                            platform=SocialPlatform.GITHUB,
                            update_data=update_data,
                        )

                        if updated_link:
                            return SocialVerificationResponseDTO(
                                success=True,
                                status_code=200,
                                message="GitHub account re-verified successfully",
                                data=self._convert_to_dto(updated_link),
                                request_id=str(uuid.uuid4()),
                            )
            else:
                # Create new social link
                signature_data = await self._generate_verification_signature(
                    account_id=str(github_user.id)
                )

                if signature_data:
                    create_data = SocialLinkCreateModel(
                        user_id=user_id,
                        platform=SocialPlatform.GITHUB,
                        account_id=str(github_user.id),
                        username=github_user.login,
                        email=github_user.email,
                        display_name=github_user.name,
                        avatar_url=github_user.avatar_url,
                        signature=signature_data["signature"],
                        verification_hash=signature_data["verification_hash"],
                        status=VerificationStatus.VERIFIED,
                    )

                    created_link = await social_link_repository.create_social_link(
                        create_data
                    )

                    if created_link:
                        return SocialVerificationResponseDTO(
                            success=True,
                            status_code=200,
                            message="GitHub account verified successfully",
                            data=self._convert_to_dto(created_link),
                            request_id=str(uuid.uuid4()),
                        )

            return SocialVerificationResponseDTO(
                success=False,
                status_code=500,
                message="Failed to save verification data",
                data=None,
                request_id=None,
            )

        except Exception as e:
            logger.error(f"Error in GitHub OAuth callback: {e}")
            return SocialVerificationResponseDTO(
                success=False,
                status_code=500,
                message=f"Internal server error: {str(e)}",
                data=None,
                request_id=None,
            )

    async def _exchange_github_code_for_token(self, code: str) -> Optional[str]:
        """Exchange GitHub authorization code for access token."""
        try:
            if not settings.GITHUB_CLIENT_SECRET:
                raise ValueError("GitHub client secret not configured")

            data = {
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            }

            print(f"🔍 DEBUG: Exchanging GitHub code for token")
            print(f"   Client ID: {settings.GITHUB_CLIENT_ID}")
            print(f"   Client Secret: {settings.GITHUB_CLIENT_SECRET[:10]}...")
            print(f"   Code: {code[:20]}...")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.github_oauth_base}/access_token",
                    data=data,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "DEiD-Social-Link/1.0",
                    },
                )

                print(f"🔍 DEBUG: GitHub token exchange response")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response Preview: {response.text[:200]}...")

                if response.status_code == 200:
                    token_data = response.json()
                    print(f"✅ Token response received: {token_data}")

                    access_token = token_data.get("access_token")
                    if access_token:
                        print(f"✅ Access token received: {access_token[:20]}...")
                        return access_token
                    else:
                        print(f"❌ No access token in response: {token_data}")
                        return None
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                    return None

        except Exception as e:
            logger.error(f"Error exchanging GitHub code for token: {e}")
            print(f"🔍 DEBUG: Exception details")
            print(f"   Exception type: {type(e).__name__}")
            print(f"   Exception message: {str(e)}")
            return None

    async def _get_github_user_info(
        self, access_token: str
    ) -> Optional[GitHubUserInfoDTO]:
        """Get GitHub user information using access token."""
        try:
            async with httpx.AsyncClient() as client:
                # Get user info from GitHub API
                response = await client.get(
                    f"{self.github_api_base}/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "DEiD-Social-Link/1.0",
                    },
                )
                response.raise_for_status()

                user_data = response.json()
                return GitHubUserInfoDTO(
                    id=user_data["id"],
                    login=user_data["login"],
                    name=user_data.get("name"),
                    email=user_data.get("email"),
                    avatar_url=user_data.get("avatar_url"),
                    bio=user_data.get("bio"),
                    blog=user_data.get("blog"),
                    location=user_data.get("location"),
                    public_repos=user_data.get("public_repos", 0),
                    public_gists=user_data.get("public_gists", 0),
                    followers=user_data.get("followers", 0),
                    following=user_data.get("following", 0),
                    created_at=user_data.get("created_at", ""),
                    updated_at=user_data.get("updated_at", ""),
                )

        except Exception as e:
            logger.error(f"Error getting GitHub user info: {e}")
            return None

    async def get_google_oauth_url(self, user_id: str) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            user_id: User's wallet address or unique identifier

        Returns:
            Google OAuth authorization URL
        """
        if not settings.GOOGLE_CLIENT_ID:
            raise ValueError("Google client ID not configured")

        # Create state parameter with user_id for CSRF protection
        state = f"deid_{user_id}"

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
        }

        auth_url = f"{self.google_oauth_base}/auth?{urlencode(params)}"
        logger.info(f"Generated Google OAuth URL for user {user_id}")

        return auth_url

    async def handle_google_oauth_callback(
        self, code: str, state: str
    ) -> SocialVerificationResponseDTO:
        """
        Handle Google OAuth callback and verify user account.

        Args:
            code: Authorization code from Google
            state: State parameter for CSRF protection

        Returns:
            SocialVerificationResponseDTO with verification data
        """
        try:
            print(f"🔍 DEBUG: Google OAuth callback received")
            print(f"   Code: {code[:20]}...")
            print(f"   State: {state}")

            # Extract user_id from state parameter
            if not state.startswith("deid_"):
                print(f"❌ Invalid state parameter: {state}")
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Invalid state parameter",
                    data=None,
                    request_id=None,
                )

            user_id = state[5:]  # Remove "deid_" prefix
            print(f"   Extracted user_id: {user_id}")

            # Exchange code for access token
            print(f"🔄 Exchanging code for access token...")
            access_token = await self._exchange_google_code_for_token(code)
            if not access_token:
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Failed to exchange code for access token",
                    data=None,
                    request_id=None,
                )

            # Get Google user info
            google_user = await self._get_google_user_info(access_token)
            if not google_user:
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Failed to get Google user information",
                    data=None,
                    request_id=None,
                )

            # Check if social link already exists
            existing_link = await social_link_repository.get_social_link(
                user_id=user_id, platform=SocialPlatform.GOOGLE
            )

            if existing_link:
                # Check if this is the same Google account
                if existing_link.account_id == google_user.id:
                    # Same account - return already linked status
                    return SocialVerificationResponseDTO(
                        success=True,
                        status_code=200,
                        message="Google account already linked",
                        data={
                            **self._convert_to_dto(existing_link),
                            "status": VerificationStatus.ALREADY_LINKED.value,
                        },
                        request_id=str(uuid.uuid4()),
                    )
                else:
                    # Different Google account - update with new verification
                    signature_data = await self._generate_verification_signature(
                        account_id=google_user.id
                    )

                    if signature_data:
                        update_data = SocialLinkUpdateModel(
                            username=google_user.email,
                            email=google_user.email,
                            signature=signature_data["signature"],
                            verification_hash=signature_data["verification_hash"],
                            status=VerificationStatus.VERIFIED,
                        )

                        updated_link = await social_link_repository.update_social_link(
                            user_id=user_id,
                            platform=SocialPlatform.GOOGLE,
                            update_data=update_data,
                        )

                        if updated_link:
                            return SocialVerificationResponseDTO(
                                success=True,
                                status_code=200,
                                message="Google account re-verified successfully",
                                data=self._convert_to_dto(updated_link),
                                request_id=str(uuid.uuid4()),
                            )
            else:
                # Create new social link
                signature_data = await self._generate_verification_signature(
                    account_id=google_user.id
                )

                if signature_data:
                    create_data = SocialLinkCreateModel(
                        user_id=user_id,
                        platform=SocialPlatform.GOOGLE,
                        account_id=google_user.id,
                        username=google_user.email,
                        email=google_user.email,
                        display_name=google_user.name,
                        avatar_url=google_user.picture,
                        signature=signature_data["signature"],
                        verification_hash=signature_data["verification_hash"],
                        status=VerificationStatus.VERIFIED,
                    )

                    created_link = await social_link_repository.create_social_link(
                        create_data
                    )

                    if created_link:
                        return SocialVerificationResponseDTO(
                            success=True,
                            status_code=200,
                            message="Google account verified successfully",
                            data=self._convert_to_dto(created_link),
                            request_id=str(uuid.uuid4()),
                        )

            return SocialVerificationResponseDTO(
                success=False,
                status_code=500,
                message="Failed to save verification data",
                data=None,
                request_id=None,
            )

        except Exception as e:
            logger.error(f"Error in Google OAuth callback: {e}")
            return SocialVerificationResponseDTO(
                success=False,
                status_code=500,
                message=f"Internal server error: {str(e)}",
                data=None,
                request_id=None,
            )

    async def _exchange_google_code_for_token(self, code: str) -> Optional[str]:
        """Exchange Google authorization code for access token."""
        try:
            if not settings.GOOGLE_CLIENT_SECRET:
                raise ValueError("Google client secret not configured")

            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }

            print(f"🔍 DEBUG: Exchanging Google code for token")
            print(f"   Client ID: {settings.GOOGLE_CLIENT_ID}")
            print(f"   Client Secret: {settings.GOOGLE_CLIENT_SECRET[:10]}...")
            print(f"   Code: {code[:20]}...")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "DEiD-Social-Link/1.0",
                    },
                )

                print(f"🔍 DEBUG: Google token exchange response")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response Preview: {response.text[:200]}...")

                if response.status_code == 200:
                    token_data = response.json()
                    print(f"✅ Token response received: {token_data}")

                    access_token = token_data.get("access_token")
                    if access_token:
                        print(f"✅ Access token received: {access_token[:20]}...")
                        return access_token
                    else:
                        print(f"❌ No access token in response: {token_data}")
                        return None
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                    return None

        except Exception as e:
            logger.error(f"Error exchanging Google code for token: {e}")
            print(f"🔍 DEBUG: Exception details")
            print(f"   Exception type: {type(e).__name__}")
            print(f"   Exception message: {str(e)}")
            return None

    async def _get_google_user_info(
        self, access_token: str
    ) -> Optional[GoogleUserInfoDTO]:
        """Get Google user information using access token."""
        try:
            async with httpx.AsyncClient() as client:
                # Get user info from Google API
                response = await client.get(
                    f"{self.google_api_base}/oauth2/v2/userinfo",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                        "User-Agent": "DEiD-Social-Link/1.0",
                    },
                )
                response.raise_for_status()

                user_data = response.json()
                return GoogleUserInfoDTO(
                    id=user_data["id"],
                    email=user_data["email"],
                    verified_email=user_data.get("verified_email", False),
                    name=user_data.get("name"),
                    given_name=user_data.get("given_name"),
                    family_name=user_data.get("family_name"),
                    picture=user_data.get("picture"),
                    locale=user_data.get("locale"),
                )

        except Exception as e:
            logger.error(f"Error getting Google user info: {e}")
            return None

    async def _generate_verification_signature(
        self, account_id: str
    ) -> Optional[Dict[str, str]]:
        """Generate signature for social verification using existing signature utils."""
        try:
            # Use the same private key as sync profile service (EVM_PRIVATE_KEY)
            if not settings.EVM_PRIVATE_KEY:
                raise ValueError("EVM private key not configured")

            # Sign the Discord account ID using existing signature utils
            verification_message = account_id

            # Sign the message using existing signature utils (same as sync profile service)
            signature, signer_address, message_hash = sign_message_with_private_key(
                message=verification_message, private_key=settings.EVM_PRIVATE_KEY
            )

            return {
                "signature": signature,
                "signer_address": signer_address,
                "verification_hash": message_hash,
            }

        except Exception as e:
            logger.error(f"Error generating verification signature: {e}")
            return None

    async def confirm_onchain_verification(
        self,
        tx_hash: str,
        platform: str,
    ) -> SocialVerificationResponseDTO:
        """
        Confirm onchain verification and update status.

        Args:
            tx_hash: Transaction hash from smart contract
            platform: Social platform
            account_id: Social account ID

        Returns:
            SocialVerificationResponseDTO with confirmation result
        """
        try:
            # Find the social link in database
            social_link = await social_link_repository.get_social_link(
                user_id="",  # We need to find by platform and account_id
                platform=SocialPlatform(platform),
            )

            # Since we can't query by account_id directly, we need to find it
            # This is a limitation of the current model - we might need to add an index
            # For now, we'll need to implement a different approach

            # Update status to onchain
            update_data = SocialLinkUpdateModel(
                status=VerificationStatus.ONCHAIN, tx_hash=tx_hash
            )

            # We need to find the link first - this is a design issue
            # Let's implement a workaround by storing the user_id in the verification process

            return SocialVerificationResponseDTO(
                success=False,
                status_code=501,
                message="Onchain confirmation requires user_id - implementation needed",
                data=None,
                request_id=None,
            )

        except Exception as e:
            logger.error(f"Error confirming onchain verification: {e}")
            return SocialVerificationResponseDTO(
                success=False,
                status_code=500,
                message=f"Internal server error: {str(e)}",
                data=None,
                request_id=None,
            )

    async def confirm_onchain_verification_with_user_id(
        self, user_id: str, tx_hash: str, platform: str, account_id: str
    ) -> SocialVerificationResponseDTO:
        """
        Confirm onchain verification with user_id.

        Args:
            user_id: User's wallet address or unique identifier
            tx_hash: Transaction hash from smart contract
            platform: Social platform
            account_id: Social account ID

        Returns:
            SocialVerificationResponseDTO with confirmation result
        """
        try:
            # Find the social link in database
            social_link = await social_link_repository.get_social_link(
                user_id=user_id, platform=SocialPlatform(platform)
            )

            if not social_link:
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=404,
                    message="Social link not found",
                    data=None,
                    request_id=None,
                )

            # Verify account_id matches
            if social_link.account_id != account_id:
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=400,
                    message="Account ID mismatch",
                    data=None,
                    request_id=None,
                )

            # Update status to onchain
            update_data = SocialLinkUpdateModel(
                status=VerificationStatus.ONCHAIN, tx_hash=tx_hash
            )

            updated_link = await social_link_repository.update_social_link(
                user_id=user_id,
                platform=SocialPlatform(platform),
                update_data=update_data,
            )

            if updated_link:
                return SocialVerificationResponseDTO(
                    success=True,
                    status_code=200,
                    message="Onchain verification confirmed successfully",
                    data=self._convert_to_dto(updated_link),
                    request_id=str(uuid.uuid4()),
                )
            else:
                return SocialVerificationResponseDTO(
                    success=False,
                    status_code=500,
                    message="Failed to update social link",
                    data=None,
                    request_id=None,
                )

        except Exception as e:
            logger.error(f"Error confirming onchain verification: {e}")
            return SocialVerificationResponseDTO(
                success=False,
                status_code=500,
                message=f"Internal server error: {str(e)}",
                data=None,
                request_id=None,
            )

    async def get_user_social_links(
        self, user_id: str, status: Optional[VerificationStatus] = None
    ) -> List[SocialLinkDataDTO]:
        """
        Get all social links for a user.

        Args:
            user_id: User's wallet address or unique identifier
            status: Optional status filter

        Returns:
            List of social link data DTOs
        """
        try:
            social_links = await social_link_repository.get_user_social_links(
                user_id=user_id, status=status
            )

            return [self._convert_to_dto(link) for link in social_links]

        except Exception as e:
            logger.error(f"Error getting user social links: {e}")
            return []

    async def get_user_social_link_stats(self, user_id: str) -> SocialLinkStatsDTO:
        """
        Get social link statistics for a user.

        Args:
            user_id: User's wallet address or unique identifier

        Returns:
            Social link statistics
        """
        try:
            stats = await social_link_repository.get_social_link_stats(user_id)
            return SocialLinkStatsDTO(**stats)

        except Exception as e:
            logger.error(f"Error getting social link stats: {e}")
            return SocialLinkStatsDTO(
                total=0, verified=0, onchain=0, pending=0, failed=0
            )

    def _convert_to_dto(self, social_link) -> Dict[str, Any]:
        """Convert social link model to DTO dictionary."""
        return {
            "id": social_link.id,
            "user_id": social_link.user_id,
            "platform": social_link.platform.value,
            "account_id": social_link.account_id,
            "username": social_link.username,
            "email": social_link.email,
            "display_name": social_link.display_name,
            "avatar_url": social_link.avatar_url,
            "signature": social_link.signature,
            "verification_hash": social_link.verification_hash,
            "status": social_link.status.value,
            "tx_hash": social_link.tx_hash,
            "block_number": social_link.block_number,
            "created_at": social_link.created_at,
            "updated_at": social_link.updated_at,
        }
