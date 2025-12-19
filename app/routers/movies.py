import math
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db
from app.models import Movie

router = APIRouter(prefix="/movies", tags=["movies"])

@router.get("/ping")
def ping():
    return {"ok": True}

@router.get("")
def list_movies(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    movies = (
        db.query(Movie)
        .order_by(Movie.popularity.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "title": m.title,
            "release_date": m.release_date,
            "overview": m.overview,
            "popularity": m.popularity,
            "vote_average": m.rating,
            "vote_count": m.vote_count,
        }
        for m in movies
    ]

@router.get("/trending")
def trending(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    movies = db.query(Movie).all()
    
    def score(m):
        pop = m.popularity or 0.0
        vc = m.vote_count or 0
        return pop * math.log(vc + 1)
    
    ranked = sorted(movies, key=score, reverse=True)[:limit]
    
    return [
        {
            "id": m.id,
            "title": m.title,
            "popularity": m.popularity,
            "vote_average": m.rating,
            "vote_count": m.vote_count,
            "trending_score": score(m),
        }
        for m in ranked
    ]

@router.get("/{movie_id}")
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Parse genres from JSON field
    genres = []
    if movie.genres:
        # genres is stored as JSON array: [{"id": 28, "name": "Action"}, ...]
        if isinstance(movie.genres, list):
            genres = [{"id": g.get("id"), "name": g.get("name")} for g in movie.genres if g.get("id") and g.get("name")]
    
    return {
        "id": movie.id,
        "title": movie.title,
        "release_date": movie.release_date,
        "overview": movie.overview,
        "popularity": movie.popularity,
        "vote_average": movie.rating,
        "vote_count": movie.vote_count,
        "genres": genres,
    }

