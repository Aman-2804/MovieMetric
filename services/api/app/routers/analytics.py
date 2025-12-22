from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session
from ..deps import get_db
from ..models import Movie, GenreStatsDaily, RatingsByDecade
from ..schemas import TopGenreOut, RatingsByDecadeOut, MessageResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/ping", response_model=MessageResponse)
def ping():
    return {"ok": True}

@router.get("/top-genres", response_model=List[TopGenreOut])
def top_genres(
    db: Session = Depends(get_db),
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format. Defaults to latest available.")
):
    if target_date:
        try:
            query_date = date.fromisoformat(target_date)
        except ValueError:
            query_date = None
    else:
        query_date = None
    
    if query_date:
        # Get stats for specific date
        stats = db.query(GenreStatsDaily).filter(
            GenreStatsDaily.date == query_date
        ).order_by(desc(GenreStatsDaily.volume)).limit(20).all()
    else:
        # Get latest date's stats
        latest_date = db.query(GenreStatsDaily.date).order_by(
            desc(GenreStatsDaily.date)
        ).first()
        
        if latest_date:
            stats = db.query(GenreStatsDaily).filter(
                GenreStatsDaily.date == latest_date[0]
            ).order_by(desc(GenreStatsDaily.volume)).limit(20).all()
        else:
            # Fallback: compute on the fly if no precomputed data
            from collections import Counter
            movies = db.query(Movie).all()
            genre_counter = Counter()
            genre_map = {}
            
            for movie in movies:
                if movie.genres and isinstance(movie.genres, list):
                    for genre in movie.genres:
                        if isinstance(genre, dict):
                            genre_id = genre.get("id")
                            genre_name = genre.get("name")
                            if genre_id and genre_name:
                                genre_counter[genre_id] += 1
                                genre_map[genre_id] = genre_name
            
            top_genres = genre_counter.most_common(20)
            return [
                TopGenreOut(
                    id=genre_id,
                    name=genre_map.get(genre_id, f"Genre {genre_id}"),
                    movie_count=count
                )
                for genre_id, count in top_genres
            ]
    
    return [
        TopGenreOut(
            id=stat.genre_id,
            name=stat.genre_name,
            movie_count=stat.volume
        )
        for stat in stats
    ]

@router.get("/ratings-by-decade", response_model=List[RatingsByDecadeOut])
def ratings_by_decade(db: Session = Depends(get_db)):
    rows = db.query(RatingsByDecade).order_by(RatingsByDecade.decade).all()
    
    if not rows:
        # Fallback: compute on the fly if no precomputed data
        from sqlalchemy import extract, func
        from ..models import Movie
        
        computed_rows = (
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
            RatingsByDecadeOut(
                decade=int(r.decade),
                avg_rating=float(r.avg_rating or 0),
                movie_count=r.movie_count
            )
            for r in computed_rows
        ]
    
    return [
        RatingsByDecadeOut(
            decade=row.decade,
            avg_rating=float(row.avg_rating or 0),
            movie_count=row.movie_count
        )
        for row in rows
    ]

