"""
SSO Service Layer.
Contains business logic for SSO operations.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx

from app.api.dto.decode_dto import (
    FetchUserDataResponseDTO,
    GetMyProfileRequestDTO,
    ProfileMetadataDTO,
    ProfileMetadataResponseDTO,
    SSOValidateRequestDTO,
    SSOValidateResponseDTO,
    UserSearchRequestDTO,
)
from app.core.config import settings
from app.core.decode_external_service import (
    get_decode_profile_external,
    search_users_external,
    validate_sso_token_external,
)
from app.core.logging import get_logger
from app.infrastructure.cache import get_cache_service

logger = get_logger(__name__)


class DecodeService:
    """Service class for SSO operations."""

    def __init__(self):
        """Initialize SSO service."""

    async def verify_sso_token(
        self, request: SSOValidateRequestDTO
    ) -> SSOValidateResponseDTO:
        """
        Verify SSO token.
        """
        print(f"Verifying SSO token: {request.sso_token}")
        sso_token = request.sso_token
        decode_validation_response = await validate_sso_token_external(sso_token)

        if not decode_validation_response:
            return {
                "success": False,
                "statusCode": 500,
                "message": "Failed to validate SSO token with external service",
            }

        access_token = decode_validation_response.data.access_token
        session_token = decode_validation_response.data.session_token
        user_id = decode_validation_response.data.user_id
        from datetime import timezone

        from dateutil import parser

        # Ensure both datetimes are timezone-aware for subtraction
        expires_at = decode_validation_response.data.expires_at
        if isinstance(expires_at, str):
            expires_at = parser.isoparse(expires_at)
        now = datetime.now(timezone.utc)
        expires_countdown = expires_at - now
        session_id = str(uuid.uuid4())[:8]
        cache_key = f"deid_session_id:{session_id}"

        cache_service = await get_cache_service()
        await cache_service.set(
            cache_key,
            {
                "access_token": access_token,
                "session_token": session_token,
                "user_id": user_id,
            },
            expire=timedelta(seconds=expires_countdown.total_seconds()),
        )

        return {
            "success": True,
            "statusCode": 200,
            "message": "SSO token validated successfully",
            "data": session_id,
        }

    async def get_my_profile(
        self, request: GetMyProfileRequestDTO
    ) -> FetchUserDataResponseDTO:
        """
        Get my profile from Decode.
        """
        user_id = request
        decode_profile_response = await get_decode_profile_external(user_id)
        if not decode_profile_response:
            return FetchUserDataResponseDTO(
                success=False,
                statusCode=500,
                message="Failed to get profile from Decode",
                data=None,
                requestId=None,
            )

        # Parse the response data into the DTO
        try:
            return FetchUserDataResponseDTO(
                success=True,
                statusCode=200,
                message="Profile fetched successfully",
                data=decode_profile_response.get("data"),
                requestId=None,
            )
        except Exception as e:
            print(f"Error parsing user data: {e}")
            return FetchUserDataResponseDTO(
                success=False,
                statusCode=500,
                message="Failed to parse user data",
                data=None,
                requestId=None,
            )

    async def fetch_profile_metadata_from_ipfs(
        self, ipfs_hash: str
    ) -> ProfileMetadataResponseDTO:
        """
        Fetch profile metadata from IPFS using Pinata.

        Args:
            ipfs_hash: The IPFS hash to fetch metadata for

        Returns:
            ProfileMetadataResponseDTO: The profile metadata response
        """
        try:
            # Clean the IPFS hash (remove ipfs:// prefix if present)
            clean_hash = ipfs_hash.replace("ipfs://", "")

            print(f"Cleaned hash: {clean_hash}")

            # Fallback to public IPFS gateway
            metadata = await self._fetch_from_public_gateway(clean_hash)
            if metadata:
                return ProfileMetadataResponseDTO(
                    success=True,
                    statusCode=200,
                    message="Profile metadata fetched successfully",
                    data=metadata,
                    requestId=None,
                )

            return ProfileMetadataResponseDTO(
                success=False,
                statusCode=404,
                message="Profile metadata not found",
                data=None,
                requestId=None,
            )

        except Exception as e:
            logger.error(f"Error fetching profile metadata from IPFS: {e}")
            return ProfileMetadataResponseDTO(
                success=False,
                statusCode=500,
                message=f"Failed to fetch profile metadata: {str(e)}",
                data=None,
                requestId=None,
            )

    async def _fetch_from_public_gateway(
        self, ipfs_hash: str
    ) -> Optional[ProfileMetadataDTO]:
        """Fetch metadata from public IPFS gateway."""
        try:
            # Try multiple public gateways
            gateways = [
                f"{settings.IPFS_GATEWAY_URL}{ipfs_hash}",
                f"https://ipfs.io/ipfs/{ipfs_hash}",
                f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}",
                f"https://cloudflare-ipfs.com/ipfs/{ipfs_hash}",
            ]

            for gateway_url in gateways:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(gateway_url)
                        print(f"IPFS Fetch Response: {response}")
                        response.raise_for_status()

                        metadata_dict = response.json()
                        return self._parse_metadata_dict(metadata_dict)

                except Exception as e:
                    logger.warning(f"Failed to fetch from {gateway_url}: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Error fetching from public gateways: {e}")
            return None

    def _parse_metadata_dict(self, metadata_dict: Dict[str, Any]) -> ProfileMetadataDTO:
        """Parse metadata dictionary into ProfileMetadataDTO."""
        try:
            # Handle nested data structure if present
            data = metadata_dict.get("data", metadata_dict)
            print(f"Raw metadata data: {json.dumps(data, indent=2, default=str)}")

            # Parse primary wallet with field name mapping
            primary_wallet_data = data.get("primary_wallet", {})
            primary_wallet = self._parse_wallet_data(primary_wallet_data)

            # Parse wallets list
            wallets_data = data.get("wallets", [])
            wallets = []
            for wallet_data in wallets_data:
                wallet = self._parse_wallet_data(wallet_data)
                wallets.append(wallet)

            return ProfileMetadataDTO(
                username=data.get("username", ""),
                display_name=data.get("display_name", ""),
                bio=data.get("bio", ""),
                avatar_ipfs_hash=data.get("avatar_ipfs_hash", ""),
                primary_wallet=primary_wallet,
                wallets=wallets,
                decode_user_id=data.get("decode_user_id", ""),
            )

        except Exception as e:
            logger.error(f"Error parsing metadata: {e}")
            raise ValueError(f"Invalid metadata format: {str(e)}")

    def _parse_wallet_data(self, wallet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse wallet data with field name mapping for DTO compatibility."""
        # Map field names to match DTO expectations
        wallet_id = wallet_data.get("id") or wallet_data.get("_id", "")
        created_at = wallet_data.get("created_at") or wallet_data.get(
            "createdAt", datetime.now()
        )
        updated_at = wallet_data.get("updated_at") or wallet_data.get(
            "updatedAt", datetime.now()
        )
        version = wallet_data.get("version") or wallet_data.get("__v", 0)

        return {
            "_id": wallet_id,  # DTO expects _id
            "address": wallet_data.get("address", ""),
            "user_id": wallet_data.get("user_id", ""),
            "name_service": wallet_data.get("name_service"),
            "is_primary": wallet_data.get("is_primary", True),
            "createdAt": created_at,  # DTO expects createdAt
            "updatedAt": updated_at,  # DTO expects updatedAt
            "__v": version,  # DTO expects __v
        }

    async def search_users(
        self, session_id: str, email_or_username: str, page: int = 0, limit: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Search users using Decode API.

        Args:
            session_id: Session ID to get access token from Redis
            email_or_username: Email or username to search for
            page: Page number (0-indexed)
            limit: Number of results per page

        Returns:
            Optional[Dict[str, Any]]: Raw response from Decode API or None if failed
        """
        try:
            # Get access token from Redis cache
            cache_service = await get_cache_service()
            cache_key = f"deid_session_id:{session_id}"
            session_data = await cache_service.get(cache_key)

            if not session_data:
                logger.error(f"Session not found in cache: {session_id}")
                return None

            access_token = session_data.get("access_token")
            if not access_token:
                logger.error(f"Access token not found in session: {session_id}")
                return None

            # Call external search service
            result = await search_users_external(
                access_token, email_or_username, page, limit
            )

            if result is None:
                logger.error(f"Failed to search users for: {email_or_username}")
                return None

            logger.info(f"Successfully searched users for: {email_or_username}")
            return result

        except Exception as e:
            logger.error(f"Error in search_users: {e}")
            return None
