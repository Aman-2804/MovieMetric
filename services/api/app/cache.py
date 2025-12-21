import os
import json
import redis
from typing import Optional, Any, Callable
from functools import wraps
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()

# Redis connection pool
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def cache_key(prefix: str, *args, **kwargs) -> str:
    parts = [prefix]
    for arg in args:
        if arg is not None:
            if isinstance(arg, date):
                parts.append(str(arg))
            elif isinstance(arg, datetime):
                parts.append(arg.isoformat())
            else:
                parts.append(str(arg))
    
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        kw_parts = [f"{k}:{v}" for k, v in sorted_kwargs if v is not None]
        if kw_parts:
            parts.extend(kw_parts)
    
    return ":".join(parts)


def get_from_cache(key: str) -> Optional[Any]:
    try:
        client = get_redis_client()
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception:
        pass
    return None


def set_in_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    try:
        client = get_redis_client()
        serialized = json.dumps(value)
        return client.setex(key, ttl, serialized)
    except Exception:
        return False


def delete_from_cache(key: str) -> bool:
    """Delete key from cache"""
    try:
        client = get_redis_client()
        return bool(client.delete(key))
    except Exception:
        return False


def cached(ttl: int = 3600, key_prefix: Optional[str] = None):
    def decorator(func: Callable):
        prefix = key_prefix or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = cache_key(prefix, *args, **kwargs)
            cached_value = get_from_cache(key)
            if cached_value is not None:
                return cached_value
            result = func(*args, **kwargs)
            set_in_cache(key, result, ttl)
            return result
        
        return wrapper
    return decorator


_cache_stats = {"hits": 0, "misses": 0}


def record_cache_hit():
    _cache_stats["hits"] += 1


def record_cache_miss():
    _cache_stats["misses"] += 1


def get_cache_stats() -> dict:
    total = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = (_cache_stats["hits"] / total * 100) if total > 0 else 0
    
    return {
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "total": total,
        "hit_rate": round(hit_rate, 2),
    }


def reset_cache_stats():
    _cache_stats["hits"] = 0
    _cache_stats["misses"] = 0

