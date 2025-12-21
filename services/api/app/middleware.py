import time
import statistics
from typing import Callable, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from .cache import record_cache_hit, record_cache_miss, get_cache_stats


_latency_data: dict[str, List[float]] = {}


def _increment_request_count(endpoint: str):
    try:
        from .routers.metrics import increment_request_count
        increment_request_count(endpoint)
    except ImportError:
        pass


class PerformanceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable):
        if not request.url.path.startswith("/movies") and \
           not request.url.path.startswith("/analytics") and \
           not request.url.path.startswith("/search"):
            return await call_next(request)
        
        start_time = time.time()
        request.state.cache_hit = False
        response = await call_next(request)
        latency_ms = (time.time() - start_time) * 1000
        
        endpoint = request.url.path.split("?")[0]
        if endpoint not in _latency_data:
            _latency_data[endpoint] = []
        _latency_data[endpoint].append(latency_ms)
        
        _increment_request_count(endpoint)
        
        if len(_latency_data[endpoint]) > 1000:
            _latency_data[endpoint] = _latency_data[endpoint][-1000:]
        
        response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"
        if hasattr(request.state, "cache_hit"):
            response.headers["X-Cache-Status"] = "HIT" if request.state.cache_hit else "MISS"
        
        return response


def get_latency_stats(endpoint: Optional[str] = None) -> dict:
    if endpoint:
        latencies = _latency_data.get(endpoint, [])
    else:
        latencies = []
        for endpoint_latencies in _latency_data.values():
            latencies.extend(endpoint_latencies)
    
    if not latencies:
        return {
            "count": 0,
            "avg": 0,
            "p50": 0,
            "p95": 0,
            "min": 0,
            "max": 0,
        }
    
    sorted_latencies = sorted(latencies)
    count = len(sorted_latencies)
    
    return {
        "count": count,
        "avg": round(statistics.mean(sorted_latencies), 2),
        "p50": round(sorted_latencies[int(count * 0.5)], 2),
        "p95": round(sorted_latencies[int(count * 0.95)], 2),
        "min": round(min(sorted_latencies), 2),
        "max": round(max(sorted_latencies), 2),
    }


def get_all_endpoint_stats() -> dict:
    return {endpoint: get_latency_stats(endpoint) for endpoint in _latency_data.keys()}

