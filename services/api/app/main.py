from fastapi import FastAPI

from .routers import movies, analytics

app = FastAPI(
    title="MovieMetric",
    description="A FastAPI-based movie database application with analytics capabilities, powered by The Movie Database (TMDB) API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers (prefixes and tags are already defined in router definitions)
app.include_router(movies.router)
app.include_router(analytics.router)

