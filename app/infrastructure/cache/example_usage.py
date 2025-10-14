"""
Example usage of the Redis cache infrastructure.
This file demonstrates how to use the cache service in your application.
"""

import asyncio
from datetime import timedelta
from app.infrastructure.cache import get_cache_service


async def example_usage():
    """Example of how to use the cache service."""

    # Get cache service instance
    cache = await get_cache_service()

    # Example 1: Simple get/set
    print("=== Example 1: Simple get/set ===")

    # Set a value
    await cache.set("user:123", {"name": "John Doe", "email": "john@example.com"})

    # Get the value
    user_data = await cache.get("user:123")
    print(f"User data: {user_data}")

    # Example 2: Set with expiration
    print("\n=== Example 2: Set with expiration ===")

    # Set with 60 seconds expiration
    await cache.set("session:abc123", {"user_id": 123, "role": "admin"}, expire=60)

    # Check if key exists
    exists = await cache.exists("session:abc123")
    print(f"Session exists: {exists}")

    # Example 3: Generate cache key
    print("\n=== Example 3: Generate cache key ===")

    # Generate a complex cache key
    cache_key = cache.generate_key(
        "user_profile",
        user_id=123,
        include_wallets=True,
        filters={"active": True, "verified": True}
    )
    print(f"Generated cache key: {cache_key}")

    # Example 4: Get or set pattern
    print("\n=== Example 4: Get or set pattern ===")

    async def fetch_user_profile(user_id: int):
        """Simulate fetching user profile from database."""
        print(f"Fetching user profile for user {user_id} from database...")
        return {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }

    # This will fetch from database first time, then from cache
    profile1 = await cache.get_or_set(
        "user_profile:456",
        lambda: fetch_user_profile(456),
        expire=300  # 5 minutes
    )
    print(f"Profile 1: {profile1}")

    # This will get from cache
    profile2 = await cache.get_or_set(
        "user_profile:456",
        lambda: fetch_user_profile(456),
        expire=300
    )
    print(f"Profile 2 (from cache): {profile2}")

    # Example 5: Multiple operations
    print("\n=== Example 5: Multiple operations ===")

    # Set multiple values
    await cache.set_many({
        "config:theme": "dark",
        "config:language": "en",
        "config:notifications": True
    }, expire=3600)  # 1 hour

    # Get multiple values
    configs = await cache.get_many(["config:theme", "config:language", "config:notifications"])
    print(f"Configs: {configs}")

    # Example 6: Delete operations
    print("\n=== Example 6: Delete operations ===")

    # Delete single key
    deleted = await cache.delete("user:123")
    print(f"Deleted user:123: {deleted}")

    # Check if deleted
    exists = await cache.exists("user:123")
    print(f"User:123 still exists: {exists}")


if __name__ == "__main__":
    asyncio.run(example_usage())
