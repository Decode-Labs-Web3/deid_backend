"""
Task Router for DEID Backend.
Handles task/badge management endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps.decode_guard import (
    AuthenticatedUser,
    get_admin_user,
    get_current_user,
)
from app.api.dto.task_dto import (
    OriginTaskCreateRequestDTO,
    OriginTaskValidateRequestDTO,
    TaskCreateResponseDTO,
    TaskListResponseDTO,
    TaskResponseDTO,
    TaskValidationResponseDTO,
)
from app.api.services.task_service import task_service
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter()


@router.post("/create", response_model=TaskCreateResponseDTO)
async def create_task(
    request: OriginTaskCreateRequestDTO,
    current_user: AuthenticatedUser = Depends(get_admin_user),
) -> TaskCreateResponseDTO:
    """
    Create a new task/badge. (Admin Only)

    This endpoint:
    1. Uploads badge metadata to IPFS
    2. Creates task in MongoDB
    3. Creates badge on smart contract
    4. Returns the created task data

    **Access**: Admin role required

    Args:
        request: Task creation request data
        current_user: Authenticated admin user

    Returns:
        TaskCreateResponseDTO with creation result
    """
    logger.info(f"Creating task: {request.task_title} by admin {current_user.user_id}")

    try:
        success, message, task_data = await task_service.create_task(request)

        if success:
            return TaskCreateResponseDTO(
                success=True,
                message=message,
                data=TaskResponseDTO(**task_data) if task_data else None,
            )
        else:
            # Task creation failed
            return TaskCreateResponseDTO(
                success=False,
                message=message,
                data=TaskResponseDTO(**task_data) if task_data else None,
            )

    except Exception as e:
        logger.error(f"Error creating task: {e}", exc_info=True)
        return TaskCreateResponseDTO(
            success=False, message=f"Internal server error: {str(e)}", data=None
        )


@router.get("/list", response_model=TaskListResponseDTO)
async def get_tasks(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    type: Optional[List[str]] = Query(
        None,
        description="Filter by task types (can select multiple): 'token' (ERC20), 'nft' (ERC721)",
    ),
    network: Optional[List[str]] = Query(
        None,
        description="Filter by blockchain networks (can select multiple): 'ethereum', 'bsc', 'base'",
    ),
) -> TaskListResponseDTO:
    """
    Get paginated list of tasks with optional filters.

    Args:
        page: Page number (1-indexed, default: 1)
        page_size: Number of items per page (default: 10, max: 100)
        type: Optional filter by task types (can pass multiple: type=token&type=nft)
        network: Optional filter by blockchain networks (can pass multiple: network=ethereum&network=bsc)

    Returns:
        TaskListResponseDTO with paginated task list

    Examples:
        - All tasks: /api/v1/task/list
        - Token tasks only: /api/v1/task/list?type=token
        - Both types: /api/v1/task/list?type=token&type=nft
        - Ethereum and BSC: /api/v1/task/list?network=ethereum&network=bsc
        - Token tasks on Ethereum and Base: /api/v1/task/list?type=token&network=ethereum&network=base
    """
    # Map user-friendly type filters to validation_types
    validation_types = None
    if type:
        type_mapping = {
            "token": "erc20_balance_check",
            "nft": "erc721_balance_check",
        }
        validation_types = []
        for t in type:
            mapped_type = type_mapping.get(t.lower())
            if not mapped_type:
                return TaskListResponseDTO(
                    success=False,
                    message=f"Invalid type filter '{t}'. Allowed values: 'token', 'nft'",
                    data=[],
                    pagination={
                        "page": page,
                        "page_size": page_size,
                        "total_count": 0,
                        "total_pages": 0,
                    },
                )
            validation_types.append(mapped_type)

    # Validate network filters
    blockchain_networks = None
    if network:
        allowed_networks = ["ethereum", "bsc", "base"]
        blockchain_networks = []
        for net in network:
            if net.lower() not in allowed_networks:
                return TaskListResponseDTO(
                    success=False,
                    message=f"Invalid network filter '{net}'. Allowed values: {', '.join(allowed_networks)}",
                    data=[],
                    pagination={
                        "page": page,
                        "page_size": page_size,
                        "total_count": 0,
                        "total_pages": 0,
                    },
                )
            blockchain_networks.append(net.lower())

    logger.info(
        f"Getting tasks: page={page}, page_size={page_size}, types={type}, networks={network}"
    )

    try:
        tasks, total_count, total_pages = await task_service.get_tasks_paginated(
            page=page,
            page_size=page_size,
            validation_types=validation_types,
            blockchain_networks=blockchain_networks,
        )

        # Convert tasks to response DTOs
        task_responses = [TaskResponseDTO(**task) for task in tasks]

        return TaskListResponseDTO(
            success=True,
            message="Tasks retrieved successfully",
            data=task_responses,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
            },
        )

    except Exception as e:
        logger.error(f"Error getting tasks: {e}", exc_info=True)
        return TaskListResponseDTO(
            success=False,
            message=f"Internal server error: {str(e)}",
            data=[],
            pagination={
                "page": page,
                "page_size": page_size,
                "total_count": 0,
                "total_pages": 0,
            },
        )


@router.get("/{task_id}", response_model=TaskCreateResponseDTO)
async def get_task_by_id(task_id: str) -> TaskCreateResponseDTO:
    """
    Get task by ID.

    Args:
        task_id: Task ID (MongoDB ObjectId)

    Returns:
        TaskCreateResponseDTO with task data
    """
    logger.info(f"Getting task by ID: {task_id}")

    try:
        task_data = await task_service.get_task_by_id(task_id)

        if task_data:
            return TaskCreateResponseDTO(
                success=True,
                message="Task retrieved successfully",
                data=TaskResponseDTO(**task_data),
            )
        else:
            return TaskCreateResponseDTO(
                success=False, message="Task not found", data=None
            )

    except Exception as e:
        logger.error(f"Error getting task: {e}", exc_info=True)
        return TaskCreateResponseDTO(
            success=False, message=f"Internal server error: {str(e)}", data=None
        )


@router.post("/{task_id}/validate", response_model=TaskValidationResponseDTO)
async def validate_task(
    task_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> TaskValidationResponseDTO:
    """
    Validate if user meets task requirements and get signature for badge minting.

    This endpoint:
    1. Fetches user profile from Decode using session
    2. Gets user's primary wallet address
    3. Checks if wallet meets task requirements (minimum token/NFT balance)
    4. Signs task_id with backend private key if validation succeeds
    5. Returns signature for frontend to use in badge minting

    **Access**: Authenticated users only (requires deid_session_id cookie)

    Args:
        task_id: Task ID to validate
        current_user: Authenticated user from session

    Returns:
        TaskValidationResponseDTO with validation result and signature
    """
    logger.info(f"Validating task {task_id} for user {current_user.user_id}")

    try:
        validation_result = await task_service.validate_task_for_user(
            task_id=task_id, user_id=current_user.user_id
        )

        return validation_result

    except Exception as e:
        logger.error(f"Error validating task: {e}", exc_info=True)
        return TaskValidationResponseDTO(
            success=False, message=f"Internal server error: {str(e)}", data=None
        )


@router.get("/health", include_in_schema=False)
async def health_check() -> dict:
    """
    Health check endpoint for task service.

    Returns:
        Dict containing service status
    """
    return {
        "status": "healthy",
        "service": "task_management",
        "functions": [
            "create_task_with_badge",
            "list_tasks_paginated",
            "get_task_by_id",
            "validate_task_for_user",
        ],
        "supported_validation_types": [
            "erc20_balance_check",
            "erc721_balance_check",
        ],
    }
