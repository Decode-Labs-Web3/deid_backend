"""
Task Repository for MongoDB operations.
Handles CRUD operations for tasks in MongoDB.
"""

from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.logging import get_logger
from app.domain.models.task import TaskModel, TaskValidationModel

logger = get_logger(__name__)


class TaskRepository:
    """Repository for task operations."""

    def __init__(self):
        """Initialize task repository."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None
        self.validations_collection = None

    async def connect(self):
        """Connect to MongoDB."""
        if not self.client:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.MONGO_DB_NAME]
            self.collection = self.db["tasks"]
            self.validations_collection = self.db["task_validations"]
            logger.info("Connected to MongoDB tasks collection")

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def create_task(self, task_data: TaskModel) -> dict:
        """
        Create a new task in MongoDB.

        Args:
            task_data: Task data to create

        Returns:
            Created task document with _id
        """
        await self.connect()

        task_dict = task_data.model_dump()
        task_dict["created_at"] = datetime.now(timezone.utc)
        task_dict["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.insert_one(task_dict)

        # Retrieve the created document
        created_task = await self.collection.find_one({"_id": result.inserted_id})

        logger.info(f"Created task with ID: {result.inserted_id}")
        return created_task

    async def get_task_by_id(self, task_id: str) -> Optional[dict]:
        """
        Get task by ID.

        Args:
            task_id: Task ID (MongoDB ObjectId as string)

        Returns:
            Task document or None if not found
        """
        await self.connect()

        try:
            object_id = ObjectId(task_id)
            task = await self.collection.find_one({"_id": object_id})
            return task
        except Exception as e:
            logger.error(f"Error getting task by ID {task_id}: {e}")
            return None

    async def get_tasks_paginated(
        self,
        skip: int = 0,
        limit: int = 10,
        validation_types: Optional[List[str]] = None,
        blockchain_networks: Optional[List[str]] = None,
    ) -> tuple[List[dict], int]:
        """
        Get paginated list of tasks.

        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            validation_types: Optional filter by validation types (list of erc20_balance_check, erc721_balance_check)
            blockchain_networks: Optional filter by blockchain networks (list of ethereum, bsc, base)

        Returns:
            Tuple of (list of tasks, total count)
        """
        await self.connect()

        # Build query filter
        query = {}
        if validation_types and len(validation_types) > 0:
            query["validation_type"] = {"$in": validation_types}
        if blockchain_networks and len(blockchain_networks) > 0:
            query["blockchain_network"] = {"$in": blockchain_networks}

        # Get total count
        total_count = await self.collection.count_documents(query)

        # Get paginated results
        cursor = (
            self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        )
        tasks = await cursor.to_list(length=limit)

        logger.info(
            f"Retrieved {len(tasks)} tasks (skip={skip}, limit={limit}, "
            f"validation_types={validation_types}, blockchain_networks={blockchain_networks})"
        )
        return tasks, total_count

    async def update_task_contract_data(
        self, task_id: str, tx_hash: str, block_number: int
    ) -> bool:
        """
        Update task with smart contract transaction data.

        Args:
            task_id: Task ID
            tx_hash: Transaction hash
            block_number: Block number

        Returns:
            True if updated successfully
        """
        await self.connect()

        try:
            object_id = ObjectId(task_id)
            result = await self.collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "tx_hash": tx_hash,
                        "block_number": block_number,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False

    async def create_task_validation(
        self, validation_data: TaskValidationModel
    ) -> Optional[dict]:
        """
        Create a new task validation record.

        Args:
            validation_data: Task validation data

        Returns:
            Created validation document with _id
        """
        await self.connect()

        validation_dict = validation_data.model_dump()
        validation_dict["created_at"] = datetime.now(timezone.utc)

        result = await self.validations_collection.insert_one(validation_dict)

        # Retrieve the created document
        created_validation = await self.validations_collection.find_one(
            {"_id": result.inserted_id}
        )

        logger.info(
            f"Created task validation for user {validation_data.user_id}, task {validation_data.task_id}"
        )
        return created_validation

    async def get_user_task_validation(
        self, user_id: str, task_id: str
    ) -> Optional[dict]:
        """
        Get task validation for a user and task.

        Args:
            user_id: User ID
            task_id: Task ID

        Returns:
            Validation document or None if not found
        """
        await self.connect()

        try:
            validation = await self.validations_collection.find_one(
                {"user_id": user_id, "task_id": task_id}
            )
            return validation
        except Exception as e:
            logger.error(f"Error getting task validation: {e}")
            return None


# Global repository instance
task_repository = TaskRepository()
