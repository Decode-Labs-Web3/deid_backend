"""
MongoDB models for badges.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator


class ValidationType(str, Enum):
    """Validation type for badges."""

    ERC20_BALANCE_CHECK = "erc20_balance_check"
    ERC721_BALANCE_CHECK = "erc721_balance_check"


class BlockchainNetwork(str, Enum):
    """Blockchain network for badges."""

    ETHEREUM = "ethereum"
    BINANCE_SMART_CHAIN = "bsc"
    BASE = "base"


# Task and Badge Models


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


class TaskModel(BaseModel):
    """Task model."""

    task_title: str = Field(..., description="Task title")
    task_description: str = Field(..., description="Task description")
    validation_type: ValidationType = Field(..., description="Validation type")
    blockchain_network: BlockchainNetwork = Field(..., description="Blockchain network")
    token_contract_address: str = Field(..., description="Token contract address")
    minimum_balance: int = Field(..., description="Minimum balance")
    badge_details: dict = Field(..., description="Badge details")
