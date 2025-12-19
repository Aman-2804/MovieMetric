from fastapi import FastAPI

from app.routers import movies, analytics

app = FastAPI(title="MovieGPT")

app.include_router(movies.router)
app.include_router(analytics.router)

