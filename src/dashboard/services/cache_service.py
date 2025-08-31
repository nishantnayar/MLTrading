"""
Caching service for dashboard data optimization.
Implements in-memory caching with TTL for frequently accessed data.
"""

import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from .base_service import BaseDashboardService


class CacheService(BaseDashboardService):
    """Service to handle caching of frequently accessed dashboard data."""


    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        super().__init__()
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl


    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if time.time() - entry['timestamp'] > entry['ttl']:
            # Cache expired, remove entry
            del self.cache[key]
            return None

        self.logger.debug(f"Cache hit for key: {key}")
        return entry['data']


    def set(self, key: str, data: Any, ttl: int = None) -> None:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl

        self.cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'ttl': ttl
        }
        self.logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")


    def invalidate(self, pattern: str = None) -> None:
        """Invalidate cache entries matching pattern."""
        if pattern is None:
            # Clear all cache
            self.cache.clear()
            self.logger.info("All cache entries cleared")
        else:
            # Clear entries matching pattern
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
            self.logger.info(f"Cleared {len(keys_to_remove)} cache entries matching pattern: {pattern}")


    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_count = 0

        current_time = time.time()
        for entry in self.cache.values():
            if current_time - entry['timestamp'] > entry['ttl']:
                expired_count += 1

        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_count,
            'expired_entries': expired_count
        }


def cached(ttl: int = 300, key_func: Callable = None):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key from arguments
    """


    def decorator(func):
        @wraps(func)


        def wrapper(self, *args, **kwargs):
            # Initialize cache service if not present
            if not hasattr(self, '_cache_service'):
                self._cache_service = CacheService()

            # Generate cache key
            if key_func:
                cache_key = key_func(self, *args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            # Try to get from cache
            cached_result = self._cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Call original function and cache result
            result = func(self, *args, **kwargs)
            self._cache_service.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


# Global cache instance for dashboard
_dashboard_cache = CacheService()


def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    return _dashboard_cache

