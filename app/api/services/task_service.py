"""
Task Service Layer.
Contains business logic for task management and smart contract integration.
"""

import json
from typing import Dict, List, Optional, Tuple

from app.api.dto.task_dto import BadgeDetail, OriginTaskCreateRequestDTO
from app.core.config import settings
from app.core.logging import get_logger
from app.domain.models.task import TaskModel
from app.domain.repositories.task_repository import task_repository
from app.infrastructure.blockchain.contract_client import ContractClient
from app.infrastructure.ipfs.ipfs_service import ipfs_service

logger = get_logger(__name__)


class TaskService:
    """Service class for task management."""

    def __init__(self):
        """Initialize task service."""
        self.contract_client = None

    async def _get_contract_client(self) -> ContractClient:
        """Get or create contract client instance."""
        if not self.contract_client:
            # Load BadgeSystem ABI
            with open(
                "app/contracts/verification/BadgeSystem.sol/BadgeSystem.json", "r"
            ) as f:
                badge_system_abi = json.load(f)["abi"]

            if not settings.PROXY_ADDRESS:
                raise ValueError("PROXY_ADDRESS not configured in environment")

            self.contract_client = ContractClient(
                contract_address=settings.PROXY_ADDRESS, abi=badge_system_abi
            )

        return self.contract_client

    async def create_task(
        self, task_request: OriginTaskCreateRequestDTO
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new task and badge on smart contract.

        Steps:
        1. Upload badge metadata to IPFS
        2. Save task to MongoDB
        3. Create badge on smart contract
        4. Update task with transaction info

        Args:
            task_request: Task creation request data

        Returns:
            Tuple of (success, message, task_data)
        """
        try:
            # Step 1: Prepare badge metadata for IPFS
            badge_metadata = self._prepare_badge_metadata(task_request.badge_details)

            # Upload to IPFS
            ipfs_hash = await ipfs_service.upload_badge_metadata(badge_metadata)
            if not ipfs_hash:
                return False, "Failed to upload badge metadata to IPFS", None

            metadata_uri = ipfs_service.get_ipfs_url(ipfs_hash)
            logger.info(f"Badge metadata uploaded to IPFS: {ipfs_hash}")

            # Step 2: Save task to MongoDB
            task_model = TaskModel(
                task_title=task_request.task_title,
                task_description=task_request.task_description,
                validation_type=task_request.validation_type,
                blockchain_network=task_request.blockchain_network,
                token_contract_address=task_request.token_contract_address,
                minimum_balance=task_request.minimum_balance,
                badge_details=task_request.badge_details,
            )

            created_task = await task_repository.create_task(task_model)
            task_id = str(created_task["_id"])
            logger.info(f"Task created in MongoDB with ID: {task_id}")

            # Step 3: Create badge on smart contract
            try:
                contract_client = await self._get_contract_client()

                # Call createBadge function
                tx_receipt = await contract_client.send_transaction(
                    function_name="createBadge",
                    args=[task_id, metadata_uri],
                    from_address=None,  # Will use default from contract_client
                )

                if tx_receipt and tx_receipt.get("status") == 1:
                    tx_hash = tx_receipt["transactionHash"].hex()
                    block_number = tx_receipt["blockNumber"]

                    # Step 4: Update task with transaction info
                    await task_repository.update_task_contract_data(
                        task_id, tx_hash, block_number
                    )

                    logger.info(
                        f"Badge created on-chain: tx_hash={tx_hash}, block={block_number}"
                    )

                    # Retrieve updated task
                    updated_task = await task_repository.get_task_by_id(task_id)

                    return (
                        True,
                        "Task and badge created successfully",
                        self._serialize_task(updated_task),
                    )
                else:
                    logger.error("Smart contract transaction failed")
                    return (
                        False,
                        "Failed to create badge on smart contract",
                        self._serialize_task(created_task),
                    )

            except Exception as contract_error:
                logger.error(f"Smart contract error: {contract_error}")
                # Task is created in DB but contract failed
                return (
                    False,
                    f"Task created but contract deployment failed: {str(contract_error)}",
                    self._serialize_task(created_task),
                )

        except Exception as e:
            logger.error(f"Error creating task: {e}", exc_info=True)
            return False, f"Failed to create task: {str(e)}", None

    async def get_tasks_paginated(
        self, page: int = 1, page_size: int = 10, validation_type: Optional[str] = None
    ) -> Tuple[List[Dict], int, int]:
        """
        Get paginated list of tasks.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            validation_type: Optional filter by validation type

        Returns:
            Tuple of (tasks list, total count, total pages)
        """
        try:
            # Calculate skip
            skip = (page - 1) * page_size

            # Get tasks and total count
            tasks, total_count = await task_repository.get_tasks_paginated(
                skip=skip, limit=page_size, validation_type=validation_type
            )

            # Calculate total pages
            total_pages = (total_count + page_size - 1) // page_size

            # Serialize tasks
            serialized_tasks = [self._serialize_task(task) for task in tasks]

            return serialized_tasks, total_count, total_pages

        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return [], 0, 0

    async def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task data or None if not found
        """
        try:
            task = await task_repository.get_task_by_id(task_id)
            if task:
                return self._serialize_task(task)
            return None
        except Exception as e:
            logger.error(f"Error getting task by ID: {e}")
            return None

    def _prepare_badge_metadata(self, badge_details: BadgeDetail) -> Dict:
        """
        Prepare badge metadata for IPFS upload.

        Args:
            badge_details: Badge details from request

        Returns:
            Badge metadata dictionary
        """
        return {
            "name": badge_details.badge_name,
            "description": badge_details.badge_description,
            "image": f"ipfs://{badge_details.badge_image}",
            "attributes": [
                {"trait_type": attr.trait_type, "value": attr.value}
                for attr in badge_details.attributes
            ],
        }

    def _serialize_task(self, task: Dict) -> Dict:
        """
        Serialize task document for API response.

        Args:
            task: Task document from MongoDB

        Returns:
            Serialized task data
        """
        if not task:
            return None

        # Convert ObjectId to string
        task_data = {
            "id": str(task["_id"]),
            "task_title": task.get("task_title"),
            "task_description": task.get("task_description"),
            "validation_type": task.get("validation_type"),
            "blockchain_network": task.get("blockchain_network"),
            "token_contract_address": task.get("token_contract_address"),
            "minimum_balance": task.get("minimum_balance"),
            "badge_details": task.get("badge_details"),
            "tx_hash": task.get("tx_hash"),
            "block_number": task.get("block_number"),
            "created_at": (
                task.get("created_at").isoformat() if task.get("created_at") else None
            ),
            "updated_at": (
                task.get("updated_at").isoformat() if task.get("updated_at") else None
            ),
        }

        return task_data


# Global service instance
task_service = TaskService()
