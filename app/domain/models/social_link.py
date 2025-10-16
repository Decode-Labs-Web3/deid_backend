"""
MongoDB models for social account linking.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Union

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator


class SocialPlatform(str, Enum):
    """Supported social platforms."""

    DISCORD = "discord"
    TWITTER = "twitter"
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


class SocialLinkModel(BaseModel):
    """MongoDB model for social account links."""

    # Primary fields
    user_id: str = Field(..., description="User's wallet address or unique identifier")
    platform: SocialPlatform = Field(..., description="Social platform")
    account_id: str = Field(
        ..., description="Social account ID (e.g., Discord user ID)"
    )
    username: str = Field(..., description="Social account username")

    # Optional fields
    email: Optional[str] = Field(None, description="Social account email")
    display_name: Optional[str] = Field(
        None, description="Display name on the platform"
    )
    avatar_url: Optional[str] = Field(None, description="Avatar URL from the platform")

    # Verification data
    signature: str = Field(..., description="EIP-712 signature for verification")
    verification_hash: str = Field(..., description="Hash used for verification")
    status: VerificationStatus = Field(
        default=VerificationStatus.PENDING, description="Verification status"
    )

    # Onchain data
    tx_hash: Optional[str] = Field(
        None, description="Transaction hash from smart contract"
    )
    block_number: Optional[int] = Field(
        None, description="Block number of the transaction"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    # MongoDB specific fields
    id: Optional[str] = Field(None, alias="_id", description="MongoDB document ID")

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid_to_str(cls, v):
        """Convert MongoDB ObjectId to string."""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class SocialLinkCreateModel(BaseModel):
    """Model for creating a new social link."""

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
    status: VerificationStatus = Field(
        default=VerificationStatus.VERIFIED, description="Verification status"
    )


class SocialLinkUpdateModel(BaseModel):
    """Model for updating a social link."""

    username: Optional[str] = Field(None, description="Social account username")
    email: Optional[str] = Field(None, description="Social account email")
    signature: Optional[str] = Field(
        None, description="EIP-712 signature for verification"
    )
    verification_hash: Optional[str] = Field(
        None, description="Hash used for verification"
    )
    status: Optional[VerificationStatus] = Field(
        None, description="Verification status"
    )
    tx_hash: Optional[str] = Field(
        None, description="Transaction hash from smart contract"
    )
    block_number: Optional[int] = Field(
        None, description="Block number of the transaction"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )


class SocialLinkQueryModel(BaseModel):
    """Model for querying social links."""

    user_id: Optional[str] = Field(None, description="Filter by user ID")
    platform: Optional[SocialPlatform] = Field(None, description="Filter by platform")
    status: Optional[VerificationStatus] = Field(None, description="Filter by status")
    limit: int = Field(default=100, description="Maximum number of results")
    skip: int = Field(default=0, description="Number of results to skip")
