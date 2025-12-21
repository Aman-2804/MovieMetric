import os
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, Any
from sqlalchemy import text
from ..db import engine
from ..cache import get_redis_client
from meilisearch import Client
from meilisearch.errors import MeilisearchError
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    status: str
    postgres: Dict[str, Any]
    redis: Dict[str, Any]
    meilisearch: Dict[str, Any]


def check_postgres() -> Dict[str, Any]:
    try:
        start_time = time.time()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def check_redis() -> Dict[str, Any]:
    try:
        start_time = time.time()
        client = get_redis_client()
        client.ping()
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def check_meilisearch() -> Dict[str, Any]:
    try:
        start_time = time.time()
        meili_url = os.getenv("MEILI_URL", "http://localhost:7700")
        meili_key = os.getenv("MEILI_MASTER_KEY", "dev_master_key")
        client = Client(meili_url, meili_key)
        client.health()
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("", response_model=HealthStatus)
def health_check():
    postgres_status = check_postgres()
    redis_status = check_redis()
    meilisearch_status = check_meilisearch()
    
    overall_status = "healthy"
    if (postgres_status["status"] != "healthy" or 
        redis_status["status"] != "healthy" or 
        meilisearch_status["status"] != "healthy"):
        overall_status = "degraded"
    
    return HealthStatus(
        status=overall_status,
        postgres=postgres_status,
        redis=redis_status,
        meilisearch=meilisearch_status,
    )

