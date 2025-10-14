"""
DTOs (Data Transfer Objects) for Social Link endpoints.
Contains request and response models for social account verification.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SocialPlatform(str, Enum):
    """Supported social platforms."""
    DISCORD = "discord"
    TWITTER = "twitter"
    GITHUB = "github"
    TELEGRAM = "telegram"


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


class SocialLinkDataDTO(BaseModel):
    """DTO for social link data."""
    id: Optional[str] = Field(None, description="MongoDB document ID")
    user_id: str = Field(..., description="User's wallet address or unique identifier")
    platform: SocialPlatform = Field(..., description="Social platform")
    account_id: str = Field(..., description="Social account ID")
    username: str = Field(..., description="Social account username")
    email: Optional[str] = Field(None, description="Social account email")
    display_name: Optional[str] = Field(None, description="Display name on the platform")
    avatar_url: Optional[str] = Field(None, description="Avatar URL from the platform")
    signature: str = Field(..., description="EIP-712 signature for verification")
    verification_hash: str = Field(..., description="Hash used for verification")
    status: VerificationStatus = Field(..., description="Verification status")
    tx_hash: Optional[str] = Field(None, description="Transaction hash from smart contract")
    block_number: Optional[int] = Field(None, description="Block number of the transaction")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SocialVerificationResponseDTO(BaseModel):
    """Response DTO for social verification."""
    success: bool = Field(..., description="Verification success status")
    status_code: int = Field(..., alias="statusCode", description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Verification data")
    request_id: Optional[str] = Field(None, alias="requestId", description="Request ID for tracing")

    class Config:
        populate_by_name = True


class SocialLinkResponseDTO(BaseModel):
    """Response DTO for social link operations."""
    success: bool = Field(..., description="Operation success status")
    status_code: int = Field(..., alias="statusCode", description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[SocialLinkDataDTO] = Field(None, description="Social link data")
    request_id: Optional[str] = Field(None, alias="requestId", description="Request ID for tracing")

    class Config:
        populate_by_name = True


class SocialLinksListResponseDTO(BaseModel):
    """Response DTO for listing social links."""
    success: bool = Field(..., description="Operation success status")
    status_code: int = Field(..., alias="statusCode", description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[List[SocialLinkDataDTO]] = Field(None, description="List of social links")
    request_id: Optional[str] = Field(None, alias="requestId", description="Request ID for tracing")

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
    data: Optional[SocialLinkStatsDTO] = Field(None, description="Social link statistics")
    request_id: Optional[str] = Field(None, alias="requestId", description="Request ID for tracing")

    class Config:
        populate_by_name = True
