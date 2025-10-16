"""
Social Link Router for DEID Backend.
Handles social account verification and linking endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.api.deps.decode_guard import AuthenticatedUser, get_current_user
from app.api.dto.social_dto import (
    DiscordOAuthCallbackRequestDTO,
    OnchainConfirmRequestDTO,
    SocialLinksListResponseDTO,
    SocialLinkStatsResponseDTO,
    SocialVerificationResponseDTO,
    VerificationStatus,
)
from app.api.services.social_link_service import SocialLinkService
from app.api.templates.oauth_response_templates import (
    get_oauth_already_linked_template,
    get_oauth_error_template,
    get_oauth_generic_error_template,
    get_oauth_success_template,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize service
social_link_service = SocialLinkService()

# Create router
router = APIRouter()


@router.get("/discord/oauth-url")
async def get_discord_oauth_url(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """
    Get Discord OAuth authorization URL.

    Args:
        current_user: Authenticated user

    Returns:
        Dict containing the OAuth URL
    """
    try:
        oauth_url = await social_link_service.get_discord_oauth_url(
            current_user.user_id
        )
        return {
            "success": True,
            "oauth_url": oauth_url,
            "message": "Discord OAuth URL generated successfully",
        }
    except Exception as e:
        logger.error(f"Error generating Discord OAuth URL: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate OAuth URL: {str(e)}"
        )


@router.get("/discord/callback", response_class=HTMLResponse)
async def discord_oauth_callback(
    code: str = Query(..., description="Authorization code from Discord"),
    state: str = Query(..., description="State parameter for CSRF protection"),
):
    """
    Handle Discord OAuth callback and return HTML response.

    Args:
        code: Authorization code from Discord
        state: State parameter for CSRF protection

    Returns:
        HTML response with success/error message
    """
    logger.info(
        f"Discord OAuth callback received - code: {code[:10]}..., state: {state}"
    )

    try:
        result = await social_link_service.handle_discord_oauth_callback(code, state)

        if result.success:
            # Check if account is already linked
            if result.data["status"] == "already_linked":
                # Already linked HTML response using template
                html_content = get_oauth_already_linked_template(
                    platform=result.data["platform"],
                    username=result.data["username"],
                    account_id=result.data["account_id"],
                    status=result.data["status"],
                )
                return HTMLResponse(content=html_content, status_code=200)
            else:
                # Success HTML response using template
                html_content = get_oauth_success_template(
                    platform=result.data["platform"],
                    username=result.data["username"],
                    account_id=result.data["account_id"],
                    status=result.data["status"],
                    signature=result.data["signature"],
                )
                return HTMLResponse(content=html_content, status_code=200)
        else:
            # Error HTML response using template
            html_content = get_oauth_error_template(
                platform="Discord",
                error_message=result.message,
                status_code=result.status_code,
            )
            return HTMLResponse(content=html_content, status_code=400)

    except Exception as e:
        logger.error(f"Error in Discord OAuth callback: {e}")
        # Generic error HTML response using template
        html_content = get_oauth_generic_error_template(str(e))
        return HTMLResponse(content=html_content, status_code=500)


@router.get("/github/oauth-url")
async def get_github_oauth_url(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """
    Get GitHub OAuth authorization URL.

    Args:
        current_user: Authenticated user

    Returns:
        Dict containing the OAuth URL
    """
    try:
        oauth_url = await social_link_service.get_github_oauth_url(current_user.user_id)
        return {
            "success": True,
            "oauth_url": oauth_url,
            "message": "GitHub OAuth URL generated successfully",
        }
    except Exception as e:
        logger.error(f"Error generating GitHub OAuth URL: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate OAuth URL: {str(e)}"
        )


@router.get("/github/callback", response_class=HTMLResponse)
async def github_oauth_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(..., description="State parameter for CSRF protection"),
):
    """
    Handle GitHub OAuth callback and return HTML response.

    Args:
        code: Authorization code from GitHub
        state: State parameter for CSRF protection

    Returns:
        HTML response with success/error message
    """
    logger.info(
        f"GitHub OAuth callback received - code: {code[:10]}..., state: {state}"
    )

    try:
        result = await social_link_service.handle_github_oauth_callback(code, state)

        if result.success:
            # Check if account is already linked
            if result.data["status"] == "already_linked":
                # Already linked HTML response using template
                html_content = get_oauth_already_linked_template(
                    platform=result.data["platform"],
                    username=result.data["username"],
                    account_id=result.data["account_id"],
                    status=result.data["status"],
                )
                return HTMLResponse(content=html_content, status_code=200)
            else:
                # Success HTML response using template
                html_content = get_oauth_success_template(
                    platform=result.data["platform"],
                    username=result.data["username"],
                    account_id=result.data["account_id"],
                    status=result.data["status"],
                    signature=result.data["signature"],
                )
                return HTMLResponse(content=html_content, status_code=200)
        else:
            # Error HTML response using template
            html_content = get_oauth_error_template(
                platform="GitHub",
                error_message=result.message,
                status_code=result.status_code,
            )
            return HTMLResponse(content=html_content, status_code=400)

    except Exception as e:
        logger.error(f"Error in GitHub OAuth callback: {e}")
        # Generic error HTML response using template
        html_content = get_oauth_generic_error_template(str(e))
        return HTMLResponse(content=html_content, status_code=500)


@router.get("/google/oauth-url")
async def get_google_oauth_url(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """
    Get Google OAuth authorization URL.

    Args:
        current_user: Authenticated user

    Returns:
        Dict containing the OAuth URL
    """
    try:
        oauth_url = await social_link_service.get_google_oauth_url(current_user.user_id)
        return {
            "success": True,
            "oauth_url": oauth_url,
            "message": "Google OAuth URL generated successfully",
        }
    except Exception as e:
        logger.error(f"Error generating Google OAuth URL: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate OAuth URL: {str(e)}"
        )


@router.get("/google/callback", response_class=HTMLResponse)
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter for CSRF protection"),
):
    """
    Handle Google OAuth callback and return HTML response.

    Args:
        code: Authorization code from Google
        state: State parameter for CSRF protection

    Returns:
        HTML response with success/error message
    """
    logger.info(
        f"Google OAuth callback received - code: {code[:10]}..., state: {state}"
    )

    try:
        result = await social_link_service.handle_google_oauth_callback(code, state)

        if result.success:
            # Check if account is already linked
            if result.data["status"] == "already_linked":
                # Already linked HTML response using template
                html_content = get_oauth_already_linked_template(
                    platform=result.data["platform"],
                    username=result.data["username"],
                    account_id=result.data["account_id"],
                    status=result.data["status"],
                )
                return HTMLResponse(content=html_content, status_code=200)
            else:
                # Success HTML response using template
                html_content = get_oauth_success_template(
                    platform=result.data["platform"],
                    username=result.data["username"],
                    account_id=result.data["account_id"],
                    status=result.data["status"],
                    signature=result.data["signature"],
                )
                return HTMLResponse(content=html_content, status_code=200)
        else:
            # Error HTML response using template
            html_content = get_oauth_error_template(
                platform="Google",
                error_message=result.message,
                status_code=result.status_code,
            )
            return HTMLResponse(content=html_content, status_code=400)

    except Exception as e:
        logger.error(f"Error in Google OAuth callback: {e}")
        # Generic error HTML response using template
        html_content = get_oauth_generic_error_template(str(e))
        return HTMLResponse(content=html_content, status_code=500)


@router.post("/onchain-confirm")
async def confirm_onchain_verification(
    request: OnchainConfirmRequestDTO,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SocialVerificationResponseDTO:
    """
    Confirm onchain verification.

    Args:
        request: Onchain confirmation request data
        current_user: Authenticated user

    Returns:
        SocialVerificationResponseDTO with confirmation result
    """
    logger.info(
        f"Onchain confirmation received - user_id: {current_user.user_id}, tx_hash: {request.tx_hash}, platform: {request.platform}, account_id: {request.account_id}"
    )

    try:
        result = await social_link_service.confirm_onchain_verification_with_user_id(
            user_id=current_user.user_id,
            tx_hash=request.tx_hash,
            platform=request.platform.value,
            account_id=request.account_id,
        )
        return result
    except Exception as e:
        logger.error(f"Error confirming onchain verification: {e}")
        return SocialVerificationResponseDTO(
            success=False,
            status_code=500,
            message=f"Internal server error: {str(e)}",
            data=None,
            request_id=None,
        )


@router.get("/links")
async def get_user_social_links(
    current_user: AuthenticatedUser = Depends(get_current_user),
    status: Optional[VerificationStatus] = Query(
        None, description="Filter by verification status"
    ),
) -> SocialLinksListResponseDTO:
    """
    Get all social links for a user.

    Args:
        current_user: Authenticated user
        status: Optional status filter

    Returns:
        SocialLinksListResponseDTO with list of social links
    """
    logger.info(
        f"Getting social links for user: {current_user.user_id}, status: {status}"
    )

    try:
        social_links = await social_link_service.get_user_social_links(
            current_user.user_id, status
        )
        return SocialLinksListResponseDTO(
            success=True,
            status_code=200,
            message="Social links retrieved successfully",
            data=social_links,
            request_id=None,
        )
    except Exception as e:
        logger.error(f"Error getting user social links: {e}")
        return SocialLinksListResponseDTO(
            success=False,
            status_code=500,
            message=f"Internal server error: {str(e)}",
            data=None,
            request_id=None,
        )


@router.get("/stats")
async def get_user_social_link_stats(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SocialLinkStatsResponseDTO:
    """
    Get social link statistics for a user.

    Args:
        current_user: Authenticated user

    Returns:
        SocialLinkStatsResponseDTO with statistics
    """
    logger.info(f"Getting social link stats for user: {current_user.user_id}")

    try:
        stats = await social_link_service.get_user_social_link_stats(
            current_user.user_id
        )
        return SocialLinkStatsResponseDTO(
            success=True,
            status_code=200,
            message="Social link statistics retrieved successfully",
            data=stats,
            request_id=None,
        )
    except Exception as e:
        logger.error(f"Error getting social link stats: {e}")
        return SocialLinkStatsResponseDTO(
            success=False,
            status_code=500,
            message=f"Internal server error: {str(e)}",
            data=None,
            request_id=None,
        )


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint for social link service.

    Returns:
        Dict containing service status
    """
    return {
        "status": "healthy",
        "service": "social_link",
        "functions": [
            "discord_oauth_verification",
            "github_oauth_verification",
            "google_oauth_verification",
            "onchain_confirmation",
            "social_links_management",
        ],
        "supported_platforms": ["discord", "github", "google", "twitter", "telegram"],
    }
