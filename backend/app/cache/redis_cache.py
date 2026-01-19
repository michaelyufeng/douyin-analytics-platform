"""
Redis cache implementation.
"""
from typing import Optional, Any
import json
from loguru import logger

from app.config import settings

# Redis client (lazy initialization)
_redis_client = None


async def get_redis():
    """Get Redis client instance."""
    global _redis_client
    if not settings.redis_enabled:
        return None

    if _redis_client is None:
        try:
            import redis.asyncio as redis
            _redis_client = redis.from_url(settings.redis_url)
            await _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None

    return _redis_client


class RedisCache:
    """Redis cache operations."""

    def __init__(self, prefix: str = "douyin"):
        self.prefix = prefix
        self.default_ttl = 3600  # 1 hour

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = await get_redis()
        if not client:
            return None

        try:
            data = await client.get(self._make_key(key))
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache."""
        client = await get_redis()
        if not client:
            return False

        try:
            await client.set(
                self._make_key(key),
                json.dumps(value, default=str),
                ex=ttl or self.default_ttl
            )
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        client = await get_redis()
        if not client:
            return False

        try:
            await client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await get_redis()
        if not client:
            return False

        try:
            return await client.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False


# Global cache instance
cache = RedisCache()
