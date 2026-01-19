"""
Local in-memory cache implementation.
Fallback when Redis is not available.
"""
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading


@dataclass
class CacheEntry:
    """Cache entry with expiration."""
    value: Any
    expires_at: datetime


class LocalCache:
    """Thread-safe local memory cache."""

    def __init__(self, prefix: str = "douyin", max_size: int = 10000):
        self.prefix = prefix
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self.default_ttl = 3600  # 1 hour

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}:{key}"

    def _cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in self._cache.items()
            if v.expires_at < now
        ]
        for key in expired_keys:
            del self._cache[key]

    def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        if len(self._cache) >= self.max_size:
            # Remove oldest 10% of entries
            to_remove = int(self.max_size * 0.1)
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k].expires_at
            )
            for key in sorted_keys[:to_remove]:
                del self._cache[key]

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        full_key = self._make_key(key)
        with self._lock:
            entry = self._cache.get(full_key)
            if entry is None:
                return None
            if entry.expires_at < datetime.utcnow():
                del self._cache[full_key]
                return None
            return entry.value

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache."""
        full_key = self._make_key(key)
        expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)

        with self._lock:
            self._cleanup_expired()
            self._evict_if_needed()
            self._cache[full_key] = CacheEntry(value=value, expires_at=expires_at)
            return True

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        full_key = self._make_key(key)
        with self._lock:
            if full_key in self._cache:
                del self._cache[full_key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()


# Global local cache instance
local_cache = LocalCache()
