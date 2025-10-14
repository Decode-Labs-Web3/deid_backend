"""
Cache service for high-level caching operations.
Provides convenient methods for common caching patterns.
"""

from typing import Any, Optional, Union, Callable, Awaitable
from datetime import timedelta
import hashlib
import json

from app.infrastructure.cache.redis_client import get_redis_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """High-level cache service with common caching patterns."""

    def __init__(self):
        """Initialize cache service."""
        self._redis_client = None

    async def _get_client(self):
        """Get Redis client instance."""
        if not self._redis_client:
            self._redis_client = await get_redis_client()
        return self._redis_client

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key (str): Cache key

        Returns:
            Optional[Any]: Cached value or None
        """
        client = await self._get_client()
        return await client.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key (str): Cache key
            value (Any): Value to cache
            expire (Optional[Union[int, timedelta]]): Expiration time

        Returns:
            bool: True if successful
        """
        client = await self._get_client()
        return await client.set(key, value, expire)

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key (str): Cache key to delete

        Returns:
            bool: True if deleted
        """
        client = await self._get_client()
        return await client.delete(key)

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key (str): Cache key

        Returns:
            bool: True if exists
        """
        client = await self._get_client()
        return await client.exists(key)

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from prefix and arguments.

        Args:
            prefix (str): Key prefix
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            str: Generated cache key
        """
        # Combine all arguments into a string
        key_parts = [prefix]

        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))

        # Add keyword arguments
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (dict, list)):
                key_parts.append(f"{key}:{json.dumps(value, sort_keys=True)}")
            else:
                key_parts.append(f"{key}:{value}")

        # Join and hash if too long
        key_string = ":".join(key_parts)
        if len(key_string) > 250:  # Redis key length limit
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:{key_hash}"

        return key_string

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        expire: Optional[Union[int, timedelta]] = None
    ) -> Any:
        """
        Get value from cache or set it using factory function.

        Args:
            key (str): Cache key
            factory (Callable): Async function to generate value if not cached
            expire (Optional[Union[int, timedelta]]): Expiration time

        Returns:
            Any: Cached or generated value
        """
        # Try to get from cache
        cached_value = await self.get(key)
        if cached_value is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached_value

        # Generate new value
        logger.debug(f"Cache miss for key: {key}, generating new value")
        new_value = await factory()

        # Cache the new value
        await self.set(key, new_value, expire)

        return new_value

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern (str): Redis key pattern (supports * wildcards)

        Returns:
            int: Number of keys deleted
        """
        client = await self._get_client()
        try:
            # Get all keys matching pattern
            keys = await client._client.keys(pattern)
            if keys:
                # Delete all matching keys
                deleted_count = await client._client.delete(*keys)
                logger.info(f"Invalidated {deleted_count} keys matching pattern: {pattern}")
                return deleted_count
            return 0
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys (list[str]): List of cache keys

        Returns:
            dict[str, Any]: Dictionary of key-value pairs
        """
        client = await self._get_client()
        try:
            values = await client._client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Error getting multiple keys: {e}")
            return {}

    async def set_many(
        self,
        mapping: dict[str, Any],
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set multiple values in cache.

        Args:
            mapping (dict[str, Any]): Dictionary of key-value pairs
            expire (Optional[Union[int, timedelta]]): Expiration time

        Returns:
            bool: True if successful
        """
        client = await self._get_client()
        try:
            # Serialize values
            serialized_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list, tuple)):
                    serialized_mapping[key] = json.dumps(value, default=str)
                elif isinstance(value, (str, int, float, bool)):
                    serialized_mapping[key] = json.dumps(value)
                else:
                    serialized_mapping[key] = json.dumps(str(value))

            # Set all values
            result = await client._client.mset(serialized_mapping)

            # Set expiration if provided
            if expire and result:
                for key in mapping.keys():
                    await client._client.expire(key, expire)

            return result
        except Exception as e:
            logger.error(f"Error setting multiple keys: {e}")
            return False


# Global cache service instance
cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """
    Get cache service instance.

    Returns:
        CacheService: Cache service instance
    """
    return cache_service
