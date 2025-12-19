from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy import extract
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.deps import get_db
from app.models import Movie

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/ping")
def ping():
    return {"ok": True}

@router.get("/top-genres")
def top_genres(db: Session = Depends(get_db)):
    # Get all movies
    movies = db.query(Movie).all()
    
    # Count genres from JSON field
    genre_counter = Counter()
    genre_map = {}  # Store genre id -> name mapping
    
    for movie in movies:
        if movie.genres and isinstance(movie.genres, list):
            for genre in movie.genres:
                if isinstance(genre, dict):
                    genre_id = genre.get("id")
                    genre_name = genre.get("name")
                    if genre_id and genre_name:
                        genre_counter[genre_id] += 1
                        genre_map[genre_id] = genre_name
    
    # Get top 20 genres sorted by count
    top_genres = genre_counter.most_common(20)
    
    return [
        {
            "id": genre_id,
            "name": genre_map.get(genre_id, f"Genre {genre_id}"),
            "movie_count": count
        }
        for genre_id, count in top_genres
    ]

@router.get("/ratings-by-decade")
def ratings_by_decade(db: Session = Depends(get_db)):
    rows = (
        db.query(
            (func.floor(extract("year", Movie.release_date) / 10) * 10).label("decade"),
            func.avg(Movie.rating).label("avg_rating"),
            func.count(Movie.id).label("movie_count"),
        )
        .filter(Movie.release_date.isnot(None))
        .group_by("decade")
        .order_by("decade")
        .all()
    )
    
    return [
        {"decade": int(r.decade), "avg_rating": float(r.avg_rating or 0), "movie_count": r.movie_count}
        for r in rows
    ]

