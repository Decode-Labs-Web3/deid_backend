"""
MongoDB repository for social account links.
"""

from datetime import datetime, timezone
from typing import List, Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from app.core.config import get_mongodb_database_name, get_mongodb_url
from app.core.logging import get_logger
from app.domain.models.social_link import (
    SocialLinkCreateModel,
    SocialLinkModel,
    SocialLinkQueryModel,
    SocialLinkUpdateModel,
    SocialPlatform,
    VerificationStatus,
)

logger = get_logger(__name__)


class SocialLinkRepository:
    """Repository for social account links in MongoDB."""

    def __init__(self):
        """Initialize the repository."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.collection: Optional[AsyncIOMotorCollection] = None
        self._initialized = False

    async def initialize(self):
        """Initialize MongoDB connection and collection."""
        if self._initialized:
            return

        try:
            # Connect to MongoDB
            mongodb_url = get_mongodb_url()
            database_name = get_mongodb_database_name()

            self.client = AsyncIOMotorClient(mongodb_url)
            self.database = self.client[database_name]
            self.collection = self.database["social_links"]

            # Create indexes
            await self._create_indexes()

            self._initialized = True
            logger.info(
                f"SocialLinkRepository initialized with database: {database_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize SocialLinkRepository: {e}")
            raise

    async def _create_indexes(self):
        """Create database indexes for optimal performance."""
        try:
            # Drop old unique index if it exists (allows migration to new constraint)
            try:
                await self.collection.drop_index("user_platform_unique")
                logger.info("Dropped old user_platform_unique index")
            except Exception:
                pass  # Index doesn't exist, which is fine

            # Compound unique index for user_id, platform, and account_id
            # This prevents the same social account from being linked twice to the same user
            # BUT allows multiple different accounts per platform per user
            await self.collection.create_index(
                [
                    ("user_id", ASCENDING),
                    ("platform", ASCENDING),
                    ("account_id", ASCENDING),
                ],
                unique=True,
                name="user_platform_account_unique",
            )

            # Index for user_id queries
            await self.collection.create_index(
                [("user_id", ASCENDING)], name="user_id_index"
            )

            # Index for platform queries
            await self.collection.create_index(
                [("platform", ASCENDING)], name="platform_index"
            )

            # Index for status queries
            await self.collection.create_index(
                [("status", ASCENDING)], name="status_index"
            )

            # Index for created_at queries
            await self.collection.create_index(
                [("created_at", DESCENDING)], name="created_at_index"
            )

            logger.info("Social link indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            # Don't raise here as the app can still work without indexes

    async def create_social_link(
        self, social_link: SocialLinkCreateModel
    ) -> Optional[SocialLinkModel]:
        """
        Create a new social link.

        Args:
            social_link: Social link data to create

        Returns:
            Created social link model or None if failed
        """
        await self.initialize()

        try:
            # Convert to dict and add timestamps
            link_data = social_link.dict()
            link_data["created_at"] = datetime.now(timezone.utc)
            link_data["updated_at"] = datetime.now(timezone.utc)

            # Insert document
            result = await self.collection.insert_one(link_data)

            if result.inserted_id:
                # Fetch the created document
                created_doc = await self.collection.find_one(
                    {"_id": result.inserted_id}
                )
                if created_doc:
                    created_doc["id"] = str(created_doc["_id"])
                    return SocialLinkModel(**created_doc)

            return None

        except DuplicateKeyError:
            logger.warning(
                f"Social link already exists for user {social_link.user_id} and platform {social_link.platform}"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to create social link: {e}")
            return None

    async def get_social_link(
        self, user_id: str, platform: SocialPlatform
    ) -> Optional[SocialLinkModel]:
        """
        Get a social link by user ID and platform.
        Note: If multiple accounts exist for the same platform, returns the first one.

        Args:
            user_id: User's wallet address or unique identifier
            platform: Social platform

        Returns:
            Social link model or None if not found
        """
        await self.initialize()

        try:
            doc = await self.collection.find_one(
                {"user_id": user_id, "platform": platform.value}
            )

            if doc:
                doc["id"] = str(doc["_id"])
                return SocialLinkModel(**doc)

            return None

        except Exception as e:
            logger.error(f"Failed to get social link: {e}")
            return None

    async def get_social_link_by_account(
        self, user_id: str, platform: SocialPlatform, account_id: str
    ) -> Optional[SocialLinkModel]:
        """
        Get a social link by user ID, platform, and account ID.

        Args:
            user_id: User's wallet address or unique identifier
            platform: Social platform
            account_id: Social account ID

        Returns:
            Social link model or None if not found
        """
        await self.initialize()

        try:
            doc = await self.collection.find_one(
                {
                    "user_id": user_id,
                    "platform": platform.value,
                    "account_id": account_id,
                }
            )

            if doc:
                doc["id"] = str(doc["_id"])
                return SocialLinkModel(**doc)

            return None

        except Exception as e:
            logger.error(f"Failed to get social link by account: {e}")
            return None

    async def get_user_social_links(
        self, user_id: str, status: Optional[VerificationStatus] = None
    ) -> List[SocialLinkModel]:
        """
        Get all social links for a user.

        Args:
            user_id: User's wallet address or unique identifier
            status: Optional status filter

        Returns:
            List of social link models
        """
        await self.initialize()

        try:
            query = {"user_id": user_id}
            if status:
                query["status"] = status.value

            cursor = self.collection.find(query).sort("created_at", DESCENDING)
            docs = await cursor.to_list(length=None)

            social_links = []
            for doc in docs:
                doc["id"] = str(doc["_id"])
                social_links.append(SocialLinkModel(**doc))

            return social_links

        except Exception as e:
            logger.error(f"Failed to get user social links: {e}")
            return []

    async def update_social_link(
        self, user_id: str, platform: SocialPlatform, update_data: SocialLinkUpdateModel
    ) -> Optional[SocialLinkModel]:
        """
        Update a social link.

        Args:
            user_id: User's wallet address or unique identifier
            platform: Social platform
            update_data: Update data

        Returns:
            Updated social link model or None if not found
        """
        await self.initialize()

        try:
            # Prepare update document
            update_doc = update_data.dict(exclude_unset=True)
            update_doc["updated_at"] = datetime.now(timezone.utc)

            # Update document
            result = await self.collection.update_one(
                {"user_id": user_id, "platform": platform.value}, {"$set": update_doc}
            )

            if result.modified_count > 0:
                # Fetch updated document
                updated_doc = await self.collection.find_one(
                    {"user_id": user_id, "platform": platform.value}
                )
                if updated_doc:
                    updated_doc["id"] = str(updated_doc["_id"])
                    return SocialLinkModel(**updated_doc)

            return None

        except Exception as e:
            logger.error(f"Failed to update social link: {e}")
            return None

    async def delete_social_link(self, user_id: str, platform: SocialPlatform) -> bool:
        """
        Delete all social links for a platform.
        Note: This deletes all accounts linked for this platform.

        Args:
            user_id: User's wallet address or unique identifier
            platform: Social platform

        Returns:
            True if deleted, False otherwise
        """
        await self.initialize()

        try:
            result = await self.collection.delete_many(
                {"user_id": user_id, "platform": platform.value}
            )

            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Failed to delete social link: {e}")
            return False

    async def delete_social_link_by_account(
        self, user_id: str, platform: SocialPlatform, account_id: str
    ) -> bool:
        """
        Delete a specific social account link.

        Args:
            user_id: User's wallet address or unique identifier
            platform: Social platform
            account_id: Social account ID

        Returns:
            True if deleted, False otherwise
        """
        await self.initialize()

        try:
            result = await self.collection.delete_one(
                {
                    "user_id": user_id,
                    "platform": platform.value,
                    "account_id": account_id,
                }
            )

            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Failed to delete social link by account: {e}")
            return False

    async def query_social_links(
        self, query_model: SocialLinkQueryModel
    ) -> List[SocialLinkModel]:
        """
        Query social links with filters.

        Args:
            query_model: Query parameters

        Returns:
            List of social link models
        """
        await self.initialize()

        try:
            # Build query
            query = {}
            if query_model.user_id:
                query["user_id"] = query_model.user_id
            if query_model.platform:
                query["platform"] = query_model.platform.value
            if query_model.status:
                query["status"] = query_model.status.value

            # Execute query
            cursor = self.collection.find(query).sort("created_at", DESCENDING)
            cursor = cursor.skip(query_model.skip).limit(query_model.limit)
            docs = await cursor.to_list(length=None)

            social_links = []
            for doc in docs:
                doc["id"] = str(doc["_id"])
                social_links.append(SocialLinkModel(**doc))

            return social_links

        except Exception as e:
            logger.error(f"Failed to query social links: {e}")
            return []

    async def get_social_link_stats(self, user_id: str) -> dict:
        """
        Get social link statistics for a user.

        Args:
            user_id: User's wallet address or unique identifier

        Returns:
            Dictionary with statistics
        """
        await self.initialize()

        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            ]

            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)

            stats = {"total": 0, "verified": 0, "onchain": 0, "pending": 0, "failed": 0}

            for result in results:
                status = result["_id"]
                count = result["count"]
                stats["total"] += count
                stats[status] = count

            return stats

        except Exception as e:
            logger.error(f"Failed to get social link stats: {e}")
            return {"total": 0, "verified": 0, "onchain": 0, "pending": 0, "failed": 0}

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._initialized = False
            logger.info("SocialLinkRepository connection closed")


# Global repository instance
social_link_repository = SocialLinkRepository()
