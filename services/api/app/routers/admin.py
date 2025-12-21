import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from celery import Celery
from celery.result import AsyncResult
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "moviemetric_api",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)

router = APIRouter(prefix="/admin", tags=["admin"])


class IngestResponse(BaseModel):
    status: str
    task_id: str
    message: str


class JobStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post("/ingest/run", response_model=IngestResponse)
def trigger_ingestion():
    try:
        task = celery_app.send_task("ingest.run_full")
        
        return IngestResponse(
            status="enqueued",
            task_id=task.id,
            message="Ingestion job enqueued. Use task_id to check status."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue ingestion job: {str(e)}"
        )


@router.get("/jobs/{task_id}", response_model=JobStatusResponse)
def get_job_status(task_id: str):
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = JobStatusResponse(
            task_id=task_id,
            status=task_result.state,
        )
        
        if task_result.ready():
            if task_result.successful():
                response.result = task_result.result
            else:
                response.error = str(task_result.info)
        else:
            # Task is still pending or in progress
            response.result = {"info": task_result.info}
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.post("/compute/trending", response_model=IngestResponse)
def trigger_compute_trending(target_date: str = None):
    try:
        task = celery_app.send_task("compute.trending", args=[target_date] if target_date else [])
        
        return IngestResponse(
            status="enqueued",
            task_id=task.id,
            message=f"Trending computation job enqueued for date: {target_date or 'today'}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue trending computation: {str(e)}"
        )


@router.post("/compute/genre-stats", response_model=IngestResponse)
def trigger_compute_genre_stats(target_date: str = None):
    try:
        task = celery_app.send_task("compute.genre_stats", args=[target_date] if target_date else [])
        
        return IngestResponse(
            status="enqueued",
            task_id=task.id,
            message=f"Genre stats computation job enqueued for date: {target_date or 'today'}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue genre stats computation: {str(e)}"
        )


@router.post("/compute/ratings-by-decade", response_model=IngestResponse)
def trigger_compute_ratings_by_decade():
    try:
        task = celery_app.send_task("compute.ratings_by_decade")
        
        return IngestResponse(
            status="enqueued",
            task_id=task.id,
            message="Ratings by decade computation job enqueued"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue ratings by decade computation: {str(e)}"
        )


@router.post("/compute/recommendations", response_model=IngestResponse)
def trigger_compute_recommendations(movie_id: int = None):
    try:
        task = celery_app.send_task("compute.recommendations", args=[movie_id] if movie_id else [])
        
        return IngestResponse(
            status="enqueued",
            task_id=task.id,
            message=f"Recommendations computation job enqueued for movie: {movie_id or 'all movies'}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue recommendations computation: {str(e)}"
        )


@router.post("/compute/all", response_model=IngestResponse)
def trigger_compute_all():
    try:
        task = celery_app.send_task("compute.calculate_analytics")
        
        return IngestResponse(
            status="enqueued",
            task_id=task.id,
            message="All analytics computation jobs enqueued"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue analytics computation: {str(e)}"
        )


@router.post("/search/build-index", response_model=IngestResponse)
def trigger_build_search_index():
    try:
        task = celery_app.send_task("search.build_index")
        
        return IngestResponse(
            status="enqueued",
            task_id=task.id,
            message="Search index build job enqueued. This will read all movies from Postgres and index them in Meilisearch."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue search index build: {str(e)}"
        )

