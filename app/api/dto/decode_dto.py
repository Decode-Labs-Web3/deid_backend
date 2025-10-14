"""
DTOs (Data Transfer Objects) for SSO endpoints.
Contains request and response models for API communication.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# Request DTOs
class SSOValidateRequestDTO(BaseModel):
    """Request DTO for fetching user data from Decode."""
    sso_token: str = Field(..., description="SSO token from frontend")

class GetMyProfileRequestDTO(BaseModel):
    """Request DTO for getting my profile from Decode."""
    user_id: str = Field(..., description="User ID extracted from redis cache")

# Response DTOs

class SSOValidateResponseDataDTO(BaseModel):
    """DTO for the 'data' field in SSO validate response."""
    id: str = Field(..., alias="_id", description="Session unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    device_fingerprint_id: str = Field(..., description="Device fingerprint ID")
    session_token: str = Field(..., description="Session token (JWT)")
    app: str = Field(..., description="App name")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    is_active: bool = Field(..., description="Is the session active?")
    last_used_at: datetime = Field(..., description="Last used timestamp")
    created_at: datetime = Field(..., alias="createdAt", description="Creation timestamp")
    updated_at: datetime = Field(..., alias="updatedAt", description="Last update timestamp")
    version: int = Field(..., alias="__v", description="Document version")
    access_token: str = Field(..., description="Access token (JWT)")

    class Config:
        allow_population_by_field_name = True

class SSOValidateResponseDTO(BaseModel):
    """Response DTO for SSO token validation."""
    success: bool = Field(..., description="Validation success status")
    status_code: int = Field(..., alias="statusCode", description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[SSOValidateResponseDataDTO] = Field(None, description="Session data")
    request_id: Optional[str] = Field(None, alias="requestId", description="Request ID for tracing")

    class Config:
        allow_population_by_field_name = True


class DecodeWalletDataDTO(BaseModel):
    """DTO for wallet data from Decode Portal."""
    id: str = Field(..., alias="_id", description="Wallet unique identifier")
    address: str = Field(..., description="Wallet address")
    user_id: str = Field(..., description="Associated user ID")
    name_service: Optional[str] = Field(None, description="Name service (if any)")
    is_primary: bool = Field(..., description="Is this the primary wallet?")
    created_at: datetime = Field(..., alias="createdAt", description="Creation timestamp")
    updated_at: datetime = Field(..., alias="updatedAt", description="Last update timestamp")
    version: int = Field(..., alias="__v", description="Document version")

    class Config:
        allow_population_by_field_name = True

class DecodeUserDataDTO(BaseModel):
    """DTO for user data from Decode Portal."""
    id: str = Field(..., alias="_id", description="Decode user ID")
    email: Optional[str] = Field(None, description="User email")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    bio: Optional[str] = Field(None, description="User bio")
    avatar_ipfs_hash: Optional[str] = Field(None, description="Avatar IPFS hash")
    role: Optional[str] = Field(None, description="User role")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    is_active: Optional[bool] = Field(None, description="Is user active")
    primary_wallet: Optional[DecodeWalletDataDTO] = Field(None, description="Primary wallet")
    wallets: Optional[List[DecodeWalletDataDTO]] = Field(None, description="Wallets")
    following_number: Optional[int] = Field(None, description="Number of following")
    followers_number: Optional[int] = Field(None, description="Number of followers")
    is_following: Optional[bool] = Field(None, description="Is following this user")
    is_follower: Optional[bool] = Field(None, description="Is follower of this user")
    is_blocked: Optional[bool] = Field(None, description="Is blocked by this user")
    is_blocked_by: Optional[bool] = Field(None, description="Is blocked by this user")
    mutual_followers_number: Optional[int] = Field(None, description="Number of mutual followers")
    mutual_followers_list: Optional[List[str]] = Field(None, description="List of mutual followers")
    version: Optional[int] = Field(None, alias="__v", description="Version number")

    class Config:
        allow_population_by_field_name = True


class FetchUserDataResponseDTO(BaseModel):
    """Response DTO for fetching user data from Decode."""
    success: bool = Field(..., description="Fetch success status")
    statusCode: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[DecodeUserDataDTO] = Field(None, description="User data from Decode")
    requestId: Optional[str] = Field(None, description="Request ID for tracing")

    class Config:
        allow_population_by_field_name = True

class ProfileMetadataDTO(BaseModel):
    """DTO for profile metadata from IPFS."""
    username: str = Field(..., description="Username")
    display_name: str = Field(..., description="Display name")
    bio: str = Field(..., description="User bio")
    avatar_ipfs_hash: str = Field(..., description="Avatar IPFS hash")
    primary_wallet: DecodeWalletDataDTO = Field(..., description="Primary wallet")
    wallets: List[DecodeWalletDataDTO] = Field(..., description="List of wallets")
    decode_user_id: str = Field(..., description="Decode user ID")

class ProfileMetadataResponseDTO(BaseModel):
    """Response DTO for profile metadata endpoint."""
    success: bool = Field(..., description="Fetch success status")
    statusCode: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Response message")
    data: Optional[ProfileMetadataDTO] = Field(None, description="Profile metadata from IPFS")
    requestId: Optional[str] = Field(None, description="Request ID for tracing")

    class Config:
        allow_population_by_field_name = True

class HealthCheckResponseDTO(BaseModel):
    """Response DTO for health check endpoint."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    functions: list[str] = Field(..., description="Available functions")
