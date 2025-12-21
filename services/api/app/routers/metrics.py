import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
from datetime import datetime
from celery.result import AsyncResult
from celery import Celery
from dotenv import load_dotenv
from ..middleware import get_latency_stats, get_all_endpoint_stats
from ..cache import get_cache_stats

load_dotenv()

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Celery app for querying job information
celery_app = Celery(
    "moviemetric_api",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)


class MetricsResponse(BaseModel):
    requests: Dict[str, Any]
    latency: Dict[str, Any]
    cache: Dict[str, Any]
    jobs: Dict[str, Any]


_request_counts: Dict[str, int] = {}


def increment_request_count(endpoint: str):
    _request_counts[endpoint] = _request_counts.get(endpoint, 0) + 1


def get_request_counts() -> Dict[str, int]:
    return _request_counts.copy()


def get_total_request_count() -> int:
    return sum(_request_counts.values())


def get_job_metrics() -> Dict[str, Any]:
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active() or {}
        scheduled_tasks = inspect.scheduled() or {}
        reserved_tasks = inspect.reserved() or {}
        
        task_counts = {
            "active": sum(len(tasks) for tasks in active_tasks.values()),
            "scheduled": sum(len(tasks) for tasks in scheduled_tasks.values()),
            "reserved": sum(len(tasks) for tasks in reserved_tasks.values()),
        }
        
        job_info = {
            "task_counts": task_counts,
            "workers_connected": len(active_tasks),
        }
        
        return job_info
    except Exception as e:
        return {
            "error": str(e),
            "task_counts": {"active": 0, "scheduled": 0, "reserved": 0},
            "workers_connected": 0,
        }


@router.get("", response_model=MetricsResponse)
def get_metrics():
    overall_latency = get_latency_stats()
    endpoint_latencies = get_all_endpoint_stats()
    cache_stats = get_cache_stats()
    request_counts = get_request_counts()
    total_requests = get_total_request_count()
    job_metrics = get_job_metrics()
    
    return MetricsResponse(
        requests={
            "total": total_requests,
            "by_endpoint": request_counts,
        },
        latency={
            "overall": overall_latency,
            "by_endpoint": endpoint_latencies,
        },
        cache=cache_stats,
        jobs=job_metrics,
    )

