from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ValidationType(str, Enum):

    ERC20_BALANCE_CHECK = "erc20_balance_check"
    ERC721_BALANCE_CHECK = "erc721_balance_check"


class BlockchainNetwork(str, Enum):

    ETHEREUM = "ethereum"
    BINANCE_SMART_CHAIN = "bsc"
    BASE = "base"


# Badge Detail DTO
class BadgeAttributes(BaseModel):
    """Badge attributes."""

    trait_type: str = Field(..., description="Trait type")
    value: str = Field(..., description="Value")


class BadgeDetail(BaseModel):
    """Badge detail."""

    badge_name: str = Field(..., description="Badge name")
    badge_description: str = Field(..., description="Badge description")
    badge_image: str = Field(..., description="Badge image IPFS hash")
    attributes: List[BadgeAttributes] = Field(..., description="Badge attributes")


# Request DTOs
class OriginTaskCreateRequestDTO(BaseModel):
    """Request DTO for creating an origin task."""

    task_title: str = Field(..., description="Task title")
    task_description: str = Field(..., description="Task description")
    validation_type: ValidationType = Field(..., description="Validation type")
    blockchain_network: BlockchainNetwork = Field(..., description="Blockchain network")
    token_contract_address: str = Field(..., description="Token contract address")
    minimum_balance: int = Field(..., description="Minimum balance")
    badge_details: BadgeDetail = Field(..., description="Badge details")


class OriginTaskValidateRequestDTO(BaseModel):
    """Request DTO for validating a task"""

    task_id: str = Field(..., description="Task ID")


# Response DTOs
class TaskResponseDTO(BaseModel):
    """Response DTO for task data."""

    id: str = Field(..., description="Task ID")
    task_title: str = Field(..., description="Task title")
    task_description: str = Field(..., description="Task description")
    validation_type: ValidationType = Field(..., description="Validation type")
    blockchain_network: BlockchainNetwork = Field(..., description="Blockchain network")
    token_contract_address: str = Field(..., description="Token contract address")
    minimum_balance: int = Field(..., description="Minimum balance")
    badge_details: BadgeDetail = Field(..., description="Badge details")
    tx_hash: Optional[str] = Field(None, description="Transaction hash")
    block_number: Optional[int] = Field(None, description="Block number")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class TaskCreateResponseDTO(BaseModel):
    """Response DTO for task creation."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[TaskResponseDTO] = Field(None, description="Created task data")


class TaskListResponseDTO(BaseModel):
    """Response DTO for paginated task list."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: List[TaskResponseDTO] = Field(..., description="List of tasks")
    pagination: Dict[str, int] = Field(
        ...,
        description="Pagination metadata (page, page_size, total_count, total_pages)",
    )


# Task Validation DTOs
class TaskValidationDataDTO(BaseModel):
    """Data DTO for task validation response."""

    task_id: str = Field(..., description="Task ID")
    user_wallet: str = Field(..., description="User's primary wallet address")
    actual_balance: str = Field(
        ...,
        description="Actual balance at validation time (as string to handle large numbers)",
    )
    required_balance: str = Field(
        ..., description="Required minimum balance (as string to handle large numbers)"
    )
    signature: str = Field(..., description="Validation signature for badge minting")
    verification_hash: str = Field(..., description="Verification hash")
    task_details: Dict[str, Any] = Field(..., description="Task details")


class TaskValidationResponseDTO(BaseModel):
    """Response DTO for task validation."""

    success: bool = Field(..., description="Validation success status")
    message: str = Field(..., description="Response message")
    data: Optional[TaskValidationDataDTO] = Field(
        None, description="Validation data with signature"
    )
