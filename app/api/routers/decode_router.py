"""
Simple SSO Router for DEID Backend.
Focused on 2 main functions:
1. Fetching user data from Decode
2. Syncing user data to blockchain profile
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps.decode_guard import AuthenticatedUser, get_current_user
from app.api.dto.decode_dto import (
    FetchUserDataResponseDTO,
    ProfileMetadataResponseDTO,
    SSOValidateRequestDTO,
    SSOValidateResponseDTO,
)
from app.api.services.decode_service import DecodeService
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize service
decode_service = DecodeService()

# Create router
router = APIRouter()


# Decode Backend Service Router
@router.post("/sso-validate", response_model=SSOValidateResponseDTO)
async def sso_validate(
    request: SSOValidateRequestDTO, response: Response
) -> SSOValidateResponseDTO:
    """
    Validate SSO token.
    """
    verify_sso_token_response = await decode_service.verify_sso_token(request)

    print(f"Verify SSO Token Response: {verify_sso_token_response}")

    # Check if validation was successful
    if not verify_sso_token_response.get("success", False):
        return SSOValidateResponseDTO(
            success=False,
            statusCode=verify_sso_token_response.get("statusCode", 500),
            message=verify_sso_token_response.get("message", "Validation failed"),
            data=None,
            requestId=None,
        )

    # Extract session ID from response
    session_id = verify_sso_token_response.get("data")
    logger.info(f"SSO validation successful, session ID: {session_id}")

    # Set cookie with session ID
    # Calculate expiration time (default to 30 days from now)
    expires = datetime.now(timezone.utc) + timedelta(days=30)

    logger.info(f"Setting cookie: deid_session_id={session_id}, expires={expires}")

    response.set_cookie(
        key="deid_session_id",
        value=session_id,
        expires=expires,
        secure=True,
        httponly=True,
        samesite="none",
        domain="api.de-id.xyz",
    )

    logger.info(f"Cookie set successfully: deid_session_id={session_id}")

    # Return success response
    return SSOValidateResponseDTO(
        success=True,
        statusCode=200,
        message="SSO token validated successfully",
        data=None,
        requestId=session_id,
    )


@router.get("/my-profile", response_model=FetchUserDataResponseDTO)
async def my_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> FetchUserDataResponseDTO:
    """
    Get my profile from Decode.
    """
    get_my_profile_response = await decode_service.get_my_profile(current_user.user_id)
    return get_my_profile_response


@router.get("/profile-metadata/{ipfs_hash}", response_model=ProfileMetadataResponseDTO)
async def get_profile_metadata(ipfs_hash: str) -> ProfileMetadataResponseDTO:
    """
    Fetch profile metadata from IPFS using the provided hash.

    Args:
        ipfs_hash: The IPFS hash to fetch metadata for

    Returns:
        ProfileMetadataResponseDTO: The profile metadata response
    """
    logger.info(f"Fetching profile metadata for IPFS hash: {ipfs_hash}")

    try:
        # Validate IPFS hash format
        if not ipfs_hash or len(ipfs_hash) < 10:
            return ProfileMetadataResponseDTO(
                success=False,
                statusCode=400,
                message="Invalid IPFS hash format",
                data=None,
                requestId=None,
            )

        # Fetch metadata from IPFS
        response = await decode_service.fetch_profile_metadata_from_ipfs(ipfs_hash)

        logger.info(f"Profile metadata fetch result: success={response.success}")
        return response

    except Exception as e:
        logger.error(f"Error in profile metadata endpoint: {e}")
        return ProfileMetadataResponseDTO(
            success=False,
            statusCode=500,
            message=f"Internal server error: {str(e)}",
            data=None,
            requestId=None,
        )


@router.get("/user-search")
async def search_users(
    request: Request,
    email_or_username: str = Query(..., description="Email or username to search for"),
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results per page"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Search for users using Decode API.

    Args:
        request: FastAPI request object
        email_or_username: Email or username to search for
        page: Page number (0-indexed)
        limit: Number of results per page
        current_user: Authenticated user

    Returns:
        Raw response from Decode API
    """
    logger.info(
        f"Searching users for: {email_or_username} by user {current_user.user_id}"
    )

    try:
        # Extract session ID from cookie
        session_id = request.cookies.get("deid_session_id")
        if not session_id:
            return {
                "success": False,
                "statusCode": 401,
                "message": "Session ID not found",
                "data": None,
                "requestId": None,
            }

        # Call service to search users
        result = await decode_service.search_users(
            session_id, email_or_username, page, limit
        )

        if result is None:
            return {
                "success": False,
                "statusCode": 500,
                "message": "Failed to search users",
                "data": None,
                "requestId": None,
            }

        # Transform the response to make it more frontend-friendly
        # Move users array to the top level of data for easier access
        if (
            result.get("success")
            and result.get("data")
            and result.get("data").get("users")
        ):
            transformed_result = result.copy()
            transformed_result["data"] = result["data"]["users"]  # Flatten users array
            transformed_result["meta"] = result["data"].get(
                "meta", {}
            )  # Keep meta info
            logger.info(f"User search successful for: {email_or_username}")
            return transformed_result

        logger.info(f"User search successful for: {email_or_username}")
        return result

    except Exception as e:
        logger.error(f"Error in user search endpoint: {e}")
        return {
            "success": False,
            "statusCode": 500,
            "message": f"Internal server error: {str(e)}",
            "data": None,
            "requestId": None,
        }
