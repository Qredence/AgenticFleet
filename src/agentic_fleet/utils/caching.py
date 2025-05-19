"""
Caching utilities for AgenticFleet.

This module provides caching mechanisms to improve performance of expensive operations.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Cache:
    """
    Simple in-memory cache with TTL support.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize cache with maximum size.
        
        Args:
            max_size: Maximum number of items to store in the cache
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache if it exists and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: The cached value or None if not found or expired
        """
        if key not in self._cache:
            return None
            
        entry = self._cache[key]
        now = time.time()
        
        if entry["expires"] <= now:
            # Remove expired entry
            del self._cache[key]
            return None
            
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """
        Set a value in the cache with expiration time.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        # Ensure we don't exceed max size by removing oldest entries
        if len(self._cache) >= self._max_size:
            # Sort keys by expiration time and remove oldest
            oldest_keys = sorted(
                self._cache.keys(), 
                key=lambda k: self._cache[k]["expires"]
            )[:max(1, len(self._cache) - self._max_size + 1)]
            
            for old_key in oldest_keys:
                del self._cache[old_key]
        
        # Add new entry
        self._cache[key] = {
            "value": value,
            "expires": time.time() + ttl_seconds,
            "created": time.time()
        }
    
    def invalidate(self, key: str) -> None:
        """
        Remove a specific key from the cache.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()
    
    def size(self) -> int:
        """
        Get the current size of the cache.
        
        Returns:
            int: Number of items in the cache
        """
        return len(self._cache)


# Global cache instance
_global_cache = Cache()


def cached(ttl_seconds: int = 300, key_prefix: str = "", cache_instance: Optional[Cache] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl_seconds: Time to live in seconds
        key_prefix: Optional prefix for cache keys
        cache_instance: Custom cache instance or None to use global cache
        
    Returns:
        Callable: Decorator function
    """
    cache = cache_instance or _global_cache
    
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key from function name, args, and kwargs
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key
            for arg in args:
                key_parts.append(str(arg))
                
            # Add sorted kwargs to key
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}:{v}")
                
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
                
            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result
            
        return wrapper
    
    return decorator


def async_cached(ttl_seconds: int = 300, key_prefix: str = "", cache_instance: Optional[Cache] = None):
    """
    Decorator for caching async function results.
    
    Args:
        ttl_seconds: Time to live in seconds
        key_prefix: Optional prefix for cache keys
        cache_instance: Custom cache instance or None to use global cache
        
    Returns:
        Callable: Decorator function for async functions
    """
    cache = cache_instance or _global_cache
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key from function name, args, and kwargs
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key
            for arg in args:
                key_parts.append(str(arg))
                
            # Add sorted kwargs to key
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}:{v}")
                
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
                
            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result
            
        return wrapper
    
    return decorator


def get_global_cache() -> Cache:
    """
    Get the global cache instance.
    
    Returns:
        Cache: Global cache instance
    """
    return _global_cache 