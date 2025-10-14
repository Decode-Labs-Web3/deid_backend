"""
External service integration for Decode SSO validation.

This module provides functions to interact with the Decode SSO validation endpoint.
"""

from typing import Optional, Dict, Any
import httpx

from app.api.dto.decode_dto import SSOValidateResponseDTO, FetchUserDataResponseDTO
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

async def validate_sso_token_external(sso_token: str) -> Optional[SSOValidateResponseDTO]:
    """
    Validate SSO token with the external Decode service.

    Args:
        sso_token (str): The SSO token to validate.

    Returns:
        Optional[SSOValidateResponseDTO]: The response DTO if successful, None otherwise.

    Raises:
        httpx.HTTPError: If the request fails due to network or server error.
    """
    # Construct the SSO validation URL using the configured backend URL
    sso_validate_url = f"{settings.DECODE_BACKEND_URL}/auth/sso/validate"

    logger.info(f"Validating SSO token with external service: {sso_validate_url}")

    payload = {"sso_token": sso_token}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(sso_validate_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Parse response into DTO
            return SSOValidateResponseDTO.parse_obj(data)
        except httpx.HTTPStatusError as exc:
            logger.error(f"SSO validation failed with status {exc.response.status_code}: {exc.response.text}")
            return None
        except httpx.ConnectError as exc:
            logger.error(f"Failed to connect to external service: {exc}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected error during SSO validation: {exc}")
            return None

async def get_decode_profile_external(user_id: str) -> Optional[FetchUserDataResponseDTO]:
    """
    Get Decode profile with the external Decode service.
    """
    get_decode_profile_url = f"{settings.DECODE_BACKEND_URL}/users/profile/{user_id}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(get_decode_profile_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPStatusError as exc:
            logger.error(f"Failed to get profile from Decode: {exc.response.status_code}: {exc.response.text}")
            return None
        except httpx.ConnectError as exc:
            logger.error(f"Failed to connect to external service: {exc}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected error during profile fetch: {exc}")
            return None
