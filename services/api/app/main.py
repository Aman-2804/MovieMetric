from fastapi import FastAPI

from .routers import movies, analytics, admin, search, health, metrics
from .middleware import PerformanceMiddleware

app = FastAPI(
    title="MovieMetric",
    description="A FastAPI-based movie database application with analytics capabilities, powered by The Movie Database (TMDB) API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add performance monitoring middleware
app.add_middleware(PerformanceMiddleware)

# Include routers (prefixes and tags are already defined in router definitions)
app.include_router(movies.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(search.router)
app.include_router(health.router)
app.include_router(metrics.router)

