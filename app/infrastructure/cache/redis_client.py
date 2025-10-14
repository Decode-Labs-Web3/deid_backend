"""
Redis client for caching operations.
Handles connection management, JSON serialization, and error handling.
"""

import json
import redis.asyncio as redis
from typing import Any, Optional, Union
from datetime import timedelta

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client with JSON serialization support."""

    def __init__(self):
        """Initialize Redis client."""
        self._client: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None

    async def connect(self) -> None:
        """Establish connection to Redis server."""
        try:
            # Use Redis URI from configuration
            redis_uri = settings.REDIS_URI

            # Create connection pool
            self._connection_pool = redis.ConnectionPool.from_url(
                redis_uri,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )

            # Create Redis client
            self._client = redis.Redis(connection_pool=self._connection_pool)

            # Test connection
            await self._client.ping()
            logger.info(f"Connected to Redis at {redis_uri}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache.

        Args:
            key (str): Cache key

        Returns:
            Optional[Any]: Deserialized value or None if not found
        """
        if not self._client:
            await self.connect()

        try:
            value = await self._client.get(key)
            if value is None:
                logger.debug(f"Cache miss for key: {key}")
                return None

            # Try to deserialize JSON
            try:
                deserialized_value = json.loads(value)
                logger.debug(f"Cache hit for key: {key}")
                return deserialized_value
            except json.JSONDecodeError:
                # If not JSON, return as string
                logger.debug(f"Cache hit for key: {key} (non-JSON)")
                return value

        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in Redis cache.

        Args:
            key (str): Cache key
            value (Any): Value to cache (will be JSON serialized)
            expire (Optional[Union[int, timedelta]]): Expiration time in seconds or timedelta

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._client:
            await self.connect()

        try:
            # Serialize value to JSON
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, default=str)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                # For other types, convert to string
                serialized_value = json.dumps(str(value))

            # Set in Redis
            result = await self._client.set(key, serialized_value, ex=expire)

            if result:
                logger.debug(f"Cache set for key: {key}")
                return True
            else:
                logger.warning(f"Failed to set cache for key: {key}")
                return False

        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis cache.

        Args:
            key (str): Cache key to delete

        Returns:
            bool: True if key was deleted, False otherwise
        """
        if not self._client:
            await self.connect()

        try:
            result = await self._client.delete(key)
            if result:
                logger.debug(f"Cache deleted for key: {key}")
                return True
            else:
                logger.debug(f"Key not found for deletion: {key}")
                return False

        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis cache.

        Args:
            key (str): Cache key to check

        Returns:
            bool: True if key exists, False otherwise
        """
        if not self._client:
            await self.connect()

        try:
            result = await self._client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking existence of key {key} in Redis: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """
        Get time to live for a key.

        Args:
            key (str): Cache key

        Returns:
            int: TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        if not self._client:
            await self.connect()

        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key} in Redis: {e}")
            return -2


# Global Redis client instance
redis_client = RedisClient()


async def get_redis_client() -> RedisClient:
    """
    Get Redis client instance.

    Returns:
        RedisClient: Redis client instance
    """
    if not redis_client._client:
        await redis_client.connect()
    return redis_client
