import math
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..deps import get_db
from ..models import Movie
from ..schemas import MovieOut, MovieDetailOut, TrendingMovieOut, MessageResponse, GenreOut

router = APIRouter(prefix="/movies", tags=["movies"])

@router.get("/ping", response_model=MessageResponse)
def ping():
    return {"ok": True}

@router.get("", response_model=List[MovieOut])
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
        MovieOut(
            id=m.id,
            title=m.title,
            release_date=m.release_date,
            overview=m.overview,
            popularity=m.popularity,
            vote_average=m.rating,
            vote_count=m.vote_count,
            is_trending=m.is_trending,
            is_underrated=m.is_underrated,
        )
        for m in movies
    ]

@router.get("/trending", response_model=List[TrendingMovieOut])
def trending(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    movies = db.query(Movie).all()
    
    def score(m):
        pop = m.popularity or 0.0
        vc = m.vote_count or 0
        return pop * math.log(vc + 1)
    
    ranked = sorted(movies, key=score, reverse=True)[:limit]
    
    return [
        TrendingMovieOut(
            id=m.id,
            title=m.title,
            popularity=m.popularity,
            vote_average=m.rating,
            vote_count=m.vote_count,
            trending_score=score(m),
        )
        for m in ranked
    ]

@router.get("/{movie_id}", response_model=MovieDetailOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Parse genres from JSON field
    genres = []
    if movie.genres:
        # genres is stored as JSON array: [{"id": 28, "name": "Action"}, ...]
        if isinstance(movie.genres, list):
            genres = [
                GenreOut(id=g.get("id"), name=g.get("name"))
                for g in movie.genres
                if g.get("id") and g.get("name")
            ]
    
    return MovieDetailOut(
        id=movie.id,
        title=movie.title,
        release_date=movie.release_date,
        overview=movie.overview,
        popularity=movie.popularity,
        vote_average=movie.rating,
        vote_count=movie.vote_count,
        genres=genres,
        poster_path=movie.poster_path,
        backdrop_path=movie.backdrop_path,
        runtime=movie.runtime,
        budget=movie.budget,
        revenue=movie.revenue,
        tagline=movie.tagline,
        status=movie.status,
        is_trending=movie.is_trending,
        is_underrated=movie.is_underrated,
    )

