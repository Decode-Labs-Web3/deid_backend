"""
DTOs (Data Transfer Objects) for Social Link endpoints.
Contains request and response models for social account verification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SocialPlatform(str, Enum):
    """Supported social platforms."""

    DISCORD = "discord"
    TWITTER = "twitter"  # X (formerly Twitter)
    GITHUB = "github"
    TELEGRAM = "telegram"
    GOOGLE = "google"
    FACEBOOK = "facebook"


class VerificationStatus(str, Enum):
    """Verification status for social accounts."""

    PENDING = "pending"
    VERIFIED = "verified"
    ONCHAIN = "onchain"
    FAILED = "failed"
    ALREADY_LINKED = "already_linked"


# Request DTOs
class DiscordOAuthCallbackRequestDTO(BaseModel):
    """Request DTO for Discord OAuth callback."""

    code: str = Field(..., description="Authorization code from Discord")
    state: str = Field(..., description="State parameter for CSRF protection")


class OnchainConfirmRequestDTO(BaseModel):
    """Request DTO for onchain confirmation."""

    tx_hash: str = Field(..., description="Transaction hash from smart contract")
    platform: SocialPlatform = Field(..., description="Social platform")
    account_id: str = Field(..., description="Social account ID")


# Response DTOs
class DiscordUserInfoDTO(BaseModel):
    """DTO for Discord user information."""

    id: str = Field(..., description="Discord user ID")
    username: str = Field(..., description="Discord username")
    discriminator: str = Field(..., description="Discord discriminator")
    email: Optional[str] = Field(None, description="Discord email")
    verified: bool = Field(..., description="Is Discord account verified")
    avatar: Optional[str] = Field(None, description="Discord avatar hash")


class GitHubUserInfoDTO(BaseModel):
    """DTO for GitHub user information."""

    id: int = Field(..., description="GitHub user ID")
    login: str = Field(..., description="GitHub username")
    name: Optional[str] = Field(None, description="GitHub display name")
    email: Optional[str] = Field(None, description="GitHub email")
    avatar_url: Optional[str] = Field(None, description="GitHub avatar URL")
    bio: Optional[str] = Field(None, description="GitHub bio")
    blog: Optional[str] = Field(None, description="GitHub blog URL")
    location: Optional[str] = Field(None, description="GitHub location")
    public_repos: int = Field(..., description="Number of public repositories")
    public_gists: int = Field(..., description="Number of public gists")
    followers: int = Field(..., description="Number of followers")
    following: int = Field(..., description="Number of following")
    created_at: str = Field(..., description="Account creation date")
    updated_at: str = Field(..., description="Last update date")


class GoogleUserInfoDTO(BaseModel):
    """DTO for Google user information."""

    id: str = Field(..., description="Google user ID")
    email: str = Field(..., description="Google email")
    verified_email: bool = Field(..., description="Is email verified")
    name: Optional[str] = Field(None, description="Full name")
    given_name: Optional[str] = Field(None, description="First name")
    family_name: Optional[str] = Field(None, description="Last name")
    picture: Optional[str] = Field(None, description="Profile picture URL")
    locale: Optional[str] = Field(None, description="User locale")


class FacebookUserInfoDTO(BaseModel):
    """DTO for Facebook user information."""

    id: str = Field(..., description="Facebook user ID")
    name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Facebook email")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    picture: Optional[Dict[str, Any]] = Field(None, description="Profile picture data")
    locale: Optional[str] = Field(None, description="User locale")


class XUserInfoDTO(BaseModel):
    """DTO for X (Twitter) user information."""

    id: str = Field(..., description="X user ID")
    name: Optional[str] = Field(None, description="Display name")
    username: str = Field(..., description="X username (handle)")
    description: Optional[str] = Field(None, description="User bio")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    verified: Optional[bool] = Field(None, description="Is verified user")
    created_at: Optional[str] = Field(None, description="Account creation date")


class SocialLinkDataDTO(BaseModel):
    """DTO for social link data."""

    id: Optional[str] = Field(None, description="MongoDB document ID")
    user_id: str = Field(..., description="User's wallet address or unique identifier")
    platform: SocialPlatform = Field(..., description="Social platform")
    account_id: str = Field(..., description="Social account ID")
    username: str = Field(..., description="Social account username")
    email: Optional[str] = Field(None, description="Social account email")
    display_name: Optional[str] = Field(
        None, description="Display name on the platform"
    )
    avatar_url: Optional[str] = Field(None, description="Avatar URL from the platform")
    signature: str = Field(..., description="EIP-712 signature for verification")
    verification_hash: str = Field(..., description="Hash used for verification")
    status: VerificationStatus = Field(..., description="Verification status")
    tx_hash: Optional[str] = Field(
        None, description="Transaction hash from smart contract"
    )
    block_number: Optional[int] = Field(
        None, description="Block number of the transaction"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SocialVerificationResponseDTO(BaseModel):
    """Response DTO for social verification."""

    success: bool = Field(..., description="Verification success status")
    status_code: int = Field(..., alias="statusCode", description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Verification data")
    request_id: Optional[str] = Field(
        None, alias="requestId", description="Request ID for tracing"
    )

    class Config:
        populate_by_name = True


class SocialLinkResponseDTO(BaseModel):
    """Response DTO for social link operations."""

    success: bool = Field(..., description="Operation success status")
    status_code: int = Field(..., alias="statusCode", description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[SocialLinkDataDTO] = Field(None, description="Social link data")
    request_id: Optional[str] = Field(
        None, alias="requestId", description="Request ID for tracing"
    )

    class Config:
        populate_by_name = True


class SocialLinksListResponseDTO(BaseModel):
    """Response DTO for listing social links."""

    success: bool = Field(..., description="Operation success status")
    status_code: int = Field(..., alias="statusCode", description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[List[SocialLinkDataDTO]] = Field(
        None, description="List of social links"
    )
    request_id: Optional[str] = Field(
        None, alias="requestId", description="Request ID for tracing"
    )

    class Config:
        populate_by_name = True


class SocialLinkStatsDTO(BaseModel):
    """DTO for social link statistics."""

    total: int = Field(..., description="Total number of social links")
    verified: int = Field(..., description="Number of verified links")
    onchain: int = Field(..., description="Number of onchain links")
    pending: int = Field(..., description="Number of pending links")
    failed: int = Field(..., description="Number of failed links")


class SocialLinkStatsResponseDTO(BaseModel):
    """Response DTO for social link statistics."""

    success: bool = Field(..., description="Operation success status")
    status_code: int = Field(..., alias="statusCode", description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[SocialLinkStatsDTO] = Field(
        None, description="Social link statistics"
    )
    request_id: Optional[str] = Field(
        None, alias="requestId", description="Request ID for tracing"
    )

    class Config:
        populate_by_name = True
