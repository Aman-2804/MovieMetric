import os
import requests
import time
from datetime import datetime
from celery import Task
from .celery_app import celery_app
from services.api.app.db import SessionLocal
from services.api.app.models import Movie


BASE = "https://api.themoviedb.org/3"


def tmdb_get(path, params=None, retries=3):
    api_key = os.getenv("TMDB_API_KEY")
    params = params or {}
    params["api_key"] = api_key
    
    for attempt in range(retries):
        try:
            r = requests.get(f"{BASE}{path}", params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2
                time.sleep(wait_time)
            else:
                return None
    return None


def parse_date(s):
    """Parse date string to date object"""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def calculate_is_trending(movie_data, threshold=50.0):
    """Determine if movie is trending based on popularity"""
    popularity = movie_data.get("popularity", 0)
    return popularity >= threshold


def calculate_is_underrated(movie_data):
    """Determine if movie is underrated (high rating but low vote count)"""
    rating = movie_data.get("vote_average", 0)
    vote_count = movie_data.get("vote_count", 0)
    return rating >= 7.5 and vote_count < 1000


def process_movie(movie_data, db, fetch_details=True):
    """Process and save a movie to the database"""
    movie_id = movie_data.get("id")
    if not movie_id:
        return None
    
    # Check if movie exists
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    
    if not movie:
        movie = Movie(id=movie_id)
        db.add(movie)
    
    # Update basic fields from list data
    movie.title = movie_data.get("title") or movie_data.get("original_title") or ""
    movie.release_date = parse_date(movie_data.get("release_date"))
    movie.overview = movie_data.get("overview")
    movie.popularity = movie_data.get("popularity")
    movie.rating = movie_data.get("vote_average")
    movie.vote_count = movie_data.get("vote_count")
    movie.poster_path = movie_data.get("poster_path")
    movie.backdrop_path = movie_data.get("backdrop_path")
    
    # Handle genres - store as JSON array
    genre_ids = movie_data.get("genre_ids", [])
    if genre_ids:
        genres_list = [{"id": gid} for gid in genre_ids]
        movie.genres = genres_list
    
    movie.is_trending = calculate_is_trending(movie_data)
    movie.is_underrated = calculate_is_underrated(movie_data)
    
    if fetch_details:
        details, credits = get_movie_details(movie_id)
        if details:
            movie.runtime = details.get("runtime")
            movie.budget = details.get("budget")
            movie.revenue = details.get("revenue")
            movie.tagline = details.get("tagline")
            movie.status = details.get("status")
            
            if details.get("genres"):
                movie.genres = [{"id": g.get("id"), "name": g.get("name")} for g in details.get("genres", [])]
                genre_names = [g.get("name", "") for g in details.get("genres", [])]
                movie.genre = ", ".join(genre_names) if genre_names else None
            
            # Recalculate flags with full data
            movie.is_trending = calculate_is_trending(details)
            movie.is_underrated = calculate_is_underrated(details)
    
    return movie


def get_movie_details(movie_id):
    """Fetch full movie details from TMDB"""
    data = tmdb_get(f"/movie/{movie_id}", {"language": "en-US"})
    if not data:
        return None, None
    
    credits = tmdb_get(f"/movie/{movie_id}/credits", {"language": "en-US"})
    return data, credits


@celery_app.task(name="ingest.genres", bind=True)
def ingest_genres(self: Task):
    try:
        db = SessionLocal()
        gdata = tmdb_get("/genre/movie/list", {"language": "en-US"})
        
        if not gdata or "genres" not in gdata:
            db.close()
            return {"status": "error", "message": "Failed to fetch genres"}
        
        genre_count = len(gdata["genres"])
        db.close()
        return {
            "status": "success",
            "genres_fetched": genre_count,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task(name="ingest.popular", bind=True)
def ingest_popular(self: Task, pages: int = 10):
    return ingest_endpoint("popular", pages)


@celery_app.task(name="ingest.top_rated", bind=True)
def ingest_top_rated(self: Task, pages: int = 10):
    return ingest_endpoint("top_rated", pages)


@celery_app.task(name="ingest.now_playing", bind=True)
def ingest_now_playing(self: Task, pages: int = 5):
    return ingest_endpoint("now_playing", pages)


@celery_app.task(name="ingest.upcoming", bind=True)
def ingest_upcoming(self: Task, pages: int = 5):
    return ingest_endpoint("upcoming", pages)


@celery_app.task(name="ingest.trending", bind=True)
def ingest_trending(self: Task, pages: int = 5):
    db = SessionLocal()
    total = 0
    
    try:
        for page in range(1, pages + 1):
            data = tmdb_get("/trending/movie/week", {"page": page, "language": "en-US"})
            
            if not data or "results" not in data:
                break
            
            for movie_data in data["results"]:
                try:
                    movie = process_movie(movie_data, db, fetch_details=True)
                    if movie:
                        movie.is_trending = True
                        total += 1
                except Exception as e:
                    continue
            
            db.commit()
            time.sleep(0.5)
        
        db.close()
        return {
            "status": "success",
            "movies_fetched": total,
        }
    except Exception as e:
        db.rollback()
        db.close()
        return {"status": "error", "message": str(e)}


@celery_app.task(name="ingest.discover", bind=True)
def ingest_discover(self: Task, sort_by: str = "popularity.desc", pages: int = 5):
    db = SessionLocal()
    total_movies = 0
    
    try:
        for page in range(1, pages + 1):
            data = tmdb_get("/discover/movie", {
                "page": page,
                "language": "en-US",
                "sort_by": sort_by,
                "vote_count.gte": 50
            })
            
            if not data or "results" not in data:
                break
            
            for movie_data in data["results"]:
                try:
                    process_movie(movie_data, db, fetch_details=True)
                    total_movies += 1
                except Exception:
                    continue
            
            db.commit()
            time.sleep(0.5)
        
        db.close()
        return {
            "status": "success",
            "movies_fetched": total_movies,
            "sort_by": sort_by,
        }
    except Exception as e:
        db.rollback()
        db.close()
        return {"status": "error", "message": str(e)}


def ingest_endpoint(endpoint: str, pages: int, fetch_details: bool = True):
    """Helper function to fetch movies from a TMDB endpoint"""
    db = SessionLocal()
    total_movies = 0
    
    try:
        for page in range(1, pages + 1):
            data = tmdb_get(f"/movie/{endpoint}", {"page": page, "language": "en-US"})
            
            if not data or "results" not in data:
                break
            
            for movie_data in data["results"]:
                try:
                    process_movie(movie_data, db, fetch_details=fetch_details)
                    total_movies += 1
                except Exception:
                    continue
            
            db.commit()
            time.sleep(0.5)
        
        db.close()
        return {
            "status": "success",
            "endpoint": endpoint,
            "movies_fetched": total_movies,
        }
    except Exception as e:
        db.rollback()
        db.close()
        return {"status": "error", "message": str(e)}


@celery_app.task(name="ingest.run_full", bind=True)
def ingest_run_full(self: Task):
    try:
        ingest_popular.delay(pages=30)
        ingest_top_rated.delay(pages=30)
        ingest_now_playing.delay(pages=10)
        ingest_upcoming.delay(pages=10)
        ingest_trending.delay(pages=5)
        ingest_discover.delay(sort_by="popularity.desc", pages=10)
        ingest_discover.delay(sort_by="vote_average.desc", pages=10)
        
        return {
            "status": "success",
            "message": "Full ingestion started",
            "tasks_enqueued": 8,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
