"""
@module Cache
@description In-memory TTL cache for API response caching.
             Prevents redundant calls to Google APIs.
"""
from cachetools import TTLCache

_CACHE_MAX_SIZE = 512
_DEFAULT_TTL = 300
_store: TTLCache = TTLCache(maxsize=_CACHE_MAX_SIZE, ttl=_DEFAULT_TTL)

def cache_get(key: str):
    """
    @description Retrieves a value from the TTL cache.
    @param key: str - Cache key
    @returns Any - Cached value or None if missing/expired
    """
    return _store.get(key)

def cache_set(key: str, value, ttl: int = _DEFAULT_TTL) -> None:
    """
    @description Stores a value in the TTL cache.
    @param key: str - Cache key
    @param value: Any - Value to store
    @param ttl: int - Time to live in seconds
    @returns None
    """
    _store[key] = value

def cache_delete(key: str) -> None:
    """
    @description Removes a key from the cache.
    @param key: str - Cache key
    @returns None
    """
    _store.pop(key, None)
