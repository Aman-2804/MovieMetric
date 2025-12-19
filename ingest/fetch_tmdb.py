import os
import sys
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db import SessionLocal, Base, engine
from app.models import Movie

load_dotenv()

API_KEY = os.getenv("API_KEY")  # Using API_KEY from .env
BASE = "https://api.themoviedb.org/3"


def tmdb_get(path, params=None, retries=3):
    """Make a request to TMDB API with error handling, rate limiting, and retries"""
    params = params or {}
    params["api_key"] = API_KEY
    
    for attempt in range(retries):
        try:
            r = requests.get(f"{BASE}{path}", params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"   Retry {attempt + 1}/{retries} for {path} after {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"   Error fetching {path} after {retries} attempts: {e}")
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


def get_movie_details(movie_id):
    """Fetch full movie details from TMDB"""
    data = tmdb_get(f"/movie/{movie_id}", {"language": "en-US"})
    if not data:
        return None, None
    
    # Also get credits for additional data (optional, don't fail if it errors)
    credits = tmdb_get(f"/movie/{movie_id}/credits", {"language": "en-US"})
    
    return data, credits


def calculate_is_trending(movie_data, threshold=50.0):
    """Determine if movie is trending based on popularity"""
    popularity = movie_data.get("popularity", 0)
    return popularity >= threshold


def calculate_is_underrated(movie_data):
    """Determine if movie is underrated (high rating but low vote count)"""
    rating = movie_data.get("vote_average", 0)
    vote_count = movie_data.get("vote_count", 0)
    # Underrated: rating >= 7.5 but vote_count < 1000
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
        # Fetch genre names if we have genre_ids
        genres_list = []
        for gid in genre_ids:
            # We'll get genre names from the full movie details
            genres_list.append({"id": gid})
        movie.genres = genres_list
    
    # Calculate flags
    movie.is_trending = calculate_is_trending(movie_data)
    movie.is_underrated = calculate_is_underrated(movie_data)
    
    # If fetch_details is True, get full movie details
    if fetch_details:
        details, credits = get_movie_details(movie_id)
        if details:
            # Update with full details
            movie.runtime = details.get("runtime")
            movie.budget = details.get("budget")
            movie.revenue = details.get("revenue")
            movie.tagline = details.get("tagline")
            movie.status = details.get("status")
            
            # Update genres with full names
            if details.get("genres"):
                movie.genres = [{"id": g.get("id"), "name": g.get("name")} for g in details.get("genres", [])]
                # Also store as comma-separated string for easy querying
                genre_names = [g.get("name", "") for g in details.get("genres", [])]
                movie.genre = ", ".join(genre_names) if genre_names else None
            
            # Recalculate flags with full data
            movie.is_trending = calculate_is_trending(details)
            movie.is_underrated = calculate_is_underrated(details)
    
    return movie


def fetch_movies_from_endpoint(endpoint, pages=5, fetch_details=True):
    """Fetch movies from a TMDB endpoint (popular, top_rated, etc.)"""
    db = SessionLocal()
    total_movies = 0
    
    try:
        print(f"\nFetching from {endpoint}...")
        
        for page in range(1, pages + 1):
            data = tmdb_get(f"/movie/{endpoint}", {"page": page, "language": "en-US"})
            
            if not data or "results" not in data:
                print(f"   No data for page {page}")
                break
            
            movies = data["results"]
            print(f"   Processing page {page} ({len(movies)} movies)...")
            
            for movie_data in movies:
                try:
                    process_movie(movie_data, db, fetch_details=fetch_details)
                    total_movies += 1
                except Exception as e:
                    print(f"   Error processing movie {movie_data.get('id')}: {e}")
                    continue
            
            # Commit after each page
            db.commit()
            
            # Rate limiting - be nice to TMDB API (TMDB allows 40 requests per 10 seconds)
            time.sleep(0.5)
            
            print(f"   Processed page {page}")
        
        print(f"Total movies processed from {endpoint}: {total_movies}")
        
    except Exception as e:
        print(f"Error in fetch_movies_from_endpoint: {e}")
        db.rollback()
    finally:
        db.close()


def fetch_trending_movies():
    """Fetch currently trending movies"""
    db = SessionLocal()
    total = 0
    
    try:
        print("\nFetching trending movies...")
        
        # TMDB has a trending endpoint
        for page in range(1, 6):  # Increased pages for trending
            data = tmdb_get("/trending/movie/week", {"page": page, "language": "en-US"})
            
            if not data or "results" not in data:
                break
            
            for movie_data in data["results"]:
                try:
                    movie = process_movie(movie_data, db, fetch_details=True)
                    if movie:
                        movie.is_trending = True  # Force trending flag
                        total += 1
                except Exception as e:
                    print(f"   Error processing trending movie: {e}")
                    continue
            
            db.commit()
            time.sleep(0.5)
            print(f"   Processed trending page {page}")
        
        print(f"Total trending movies: {total}")
        
    except Exception as e:
        print(f"Error fetching trending: {e}")
        db.rollback()
    finally:
        db.close()


def fetch_discover_movies(sort_by="popularity.desc", pages=5, fetch_details=True):
    """Fetch movies from TMDB discover endpoint with custom sorting"""
    db = SessionLocal()
    total_movies = 0
    
    try:
        print(f"\nFetching from discover (sort: {sort_by})...")
        
        for page in range(1, pages + 1):
            data = tmdb_get("/discover/movie", {
                "page": page,
                "language": "en-US",
                "sort_by": sort_by,
                "vote_count.gte": 50  # Only movies with at least 50 votes for quality
            })
            
            if not data or "results" not in data:
                print(f"   No data for page {page}")
                break
            
            movies = data["results"]
            print(f"   Processing page {page} ({len(movies)} movies)...")
            
            for movie_data in movies:
                try:
                    process_movie(movie_data, db, fetch_details=fetch_details)
                    total_movies += 1
                except Exception as e:
                    print(f"   Error processing movie {movie_data.get('id')}: {e}")
                    continue
            
            db.commit()
            time.sleep(0.5)
            print(f"   Processed page {page}")
        
        print(f"Total movies processed from discover ({sort_by}): {total_movies}")
        
    except Exception as e:
        print(f"Error in fetch_discover_movies: {e}")
        db.rollback()
    finally:
        db.close()


def update_underrated_flag():
    """Update is_underrated flag for all movies based on current data"""
    db = SessionLocal()
    
    try:
        print("\nUpdating underrated flags...")
        movies = db.query(Movie).all()
        updated = 0
        
        for movie in movies:
            was_underrated = movie.is_underrated
            movie.is_underrated = calculate_is_underrated({
                "vote_average": movie.rating or 0,
                "vote_count": movie.vote_count or 0
            })
            if was_underrated != movie.is_underrated:
                updated += 1
        
        db.commit()
        print(f"Updated {updated} underrated flags")
        
    except Exception as e:
        print(f"Error updating underrated flags: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main ingestion function"""
    if not API_KEY:
        raise RuntimeError("API_KEY missing in .env")
    
    print("Starting TMDB data ingestion...")
    print(f"Using API key: {API_KEY[:10]}...")
    
    # Fetch from multiple endpoints for comprehensive data
    # Increased pages to get 1000+ movies total
    endpoints = [
        ("popular", 30),      # Popular movies - increased for more data
        ("top_rated", 30),    # Top rated movies - increased for more data
        ("now_playing", 10),   # Currently playing
        ("upcoming", 10),      # Upcoming releases
    ]
    
    for endpoint, pages in endpoints:
        fetch_movies_from_endpoint(endpoint, pages=pages, fetch_details=True)
    
    # Fetch trending movies separately
    fetch_trending_movies()
    
    # Also fetch from discover endpoint with different filters for variety
    print("\nFetching additional movies from discover endpoint...")
    discover_filters = [
        {"sort_by": "popularity.desc", "pages": 10},
        {"sort_by": "vote_average.desc", "pages": 10},
        {"sort_by": "release_date.desc", "pages": 5},
    ]
    
    for filter_config in discover_filters:
        fetch_discover_movies(
            sort_by=filter_config["sort_by"],
            pages=filter_config["pages"],
            fetch_details=True
        )
    
    # Update underrated flags based on all collected data
    update_underrated_flag()
    
    # Final stats
    db = SessionLocal()
    total_movies = db.query(Movie).count()
    trending_count = db.query(Movie).filter(Movie.is_trending == True).count()
    underrated_count = db.query(Movie).filter(Movie.is_underrated == True).count()
    db.close()
    
    print("\n" + "="*50)
    print("Ingestion Complete!")
    print(f"   Total movies: {total_movies}")
    print(f"   Trending: {trending_count}")
    print(f"   Underrated: {underrated_count}")
    print("="*50)


if __name__ == "__main__":
    main()

