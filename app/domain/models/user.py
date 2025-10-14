"""
Simple user models for DEID Backend.
Focused on syncing user data from Decode to blockchain profile.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DecodeUserProfile(BaseModel):
    """User profile data from Decode Portal."""
    id: str = Field(..., description="Decode user ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_ipfs_hash: Optional[str] = Field(None, description="Avatar IPFS hash")
    created_at: Optional[datetime] = Field(None, description="Created at")
    updated_at: Optional[datetime] = Field(None, description="Updated at")
