import math
from datetime import date, datetime, timedelta
from collections import Counter
from typing import List, Dict
from celery import Task
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from .celery_app import celery_app
from services.api.app.db import SessionLocal
from services.api.app.models import (
    Movie,
    MovieTrendingDaily,
    GenreStatsDaily,
    RatingsByDecade,
    MovieRecommendations,
)


@celery_app.task(name="compute.trending", bind=True)
def compute_trending(self: Task, target_date: str = None):
    db = SessionLocal()
    try:
        if target_date:
            compute_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            compute_date = date.today()
        
        movies = db.query(Movie).filter(
            Movie.popularity.isnot(None),
            Movie.rating.isnot(None),
        ).all()
        
        trending_scores = []
        for movie in movies:
            popularity = movie.popularity or 0
            rating = movie.rating or 0
            vote_count = movie.vote_count or 0
            
            # Normalized score calculation
            score = (
                (popularity * 0.4) +
                (rating * 20 * 0.3) +
                (math.log(vote_count + 1) * 10 * 0.3)
            )
            
            trending_scores.append({
                "movie_id": movie.id,
                "score": score,
            })
        
        trending_scores.sort(key=lambda x: x["score"], reverse=True)
        
        db.query(MovieTrendingDaily).filter(
            MovieTrendingDaily.date == compute_date
        ).delete()
        
        count = 0
        for rank, item in enumerate(trending_scores, start=1):
            trending_record = MovieTrendingDaily(
                movie_id=item["movie_id"],
                date=compute_date,
                score=item["score"],
                rank=rank,
            )
            db.add(trending_record)
            count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "date": str(compute_date),
            "movies_processed": count,
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="compute.genre_stats", bind=True)
def compute_genre_stats(self: Task, target_date: str = None):
    db = SessionLocal()
    try:
        if target_date:
            compute_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            compute_date = date.today()
        
        movies = db.query(Movie).all()
        genre_data = {}
        
        for movie in movies:
            if movie.genres and isinstance(movie.genres, list):
                for genre in movie.genres:
                    if isinstance(genre, dict):
                        genre_id = genre.get("id")
                        genre_name = genre.get("name")
                        
                        if genre_id and genre_name:
                            if genre_id not in genre_data:
                                genre_data[genre_id] = {
                                    "name": genre_name,
                                    "ratings": [],
                                    "count": 0,
                                }
                            
                            if movie.rating is not None:
                                genre_data[genre_id]["ratings"].append(movie.rating)
                            genre_data[genre_id]["count"] += 1
        
        db.query(GenreStatsDaily).filter(
            GenreStatsDaily.date == compute_date
        ).delete()
        
        count = 0
        for genre_id, data in genre_data.items():
            avg_rating = (
                sum(data["ratings"]) / len(data["ratings"])
                if data["ratings"] else None
            )
            
            genre_stat = GenreStatsDaily(
                genre_id=genre_id,
                genre_name=data["name"],
                date=compute_date,
                avg_rating=avg_rating,
                volume=data["count"],
            )
            db.add(genre_stat)
            count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "date": str(compute_date),
            "genres_processed": count,
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="compute.ratings_by_decade", bind=True)
def compute_ratings_by_decade(self: Task):
    db = SessionLocal()
    try:
        rows = (
            db.query(
                (func.floor(extract("year", Movie.release_date) / 10) * 10).label("decade"),
                func.avg(Movie.rating).label("avg_rating"),
                func.count(Movie.id).label("movie_count"),
            )
            .filter(Movie.release_date.isnot(None))
            .filter(Movie.rating.isnot(None))
            .group_by("decade")
            .all()
        )
        
        db.query(RatingsByDecade).delete()
        count = 0
        for row in rows:
            decade_record = RatingsByDecade(
                decade=int(row.decade),
                avg_rating=float(row.avg_rating) if row.avg_rating else None,
                movie_count=row.movie_count,
            )
            db.add(decade_record)
            count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "decades_processed": count,
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="compute.recommendations", bind=True)
def compute_recommendations(self: Task, movie_id: int = None):
    db = SessionLocal()
    try:
        if movie_id:
            movies_to_process = db.query(Movie).filter(Movie.id == movie_id).all()
        else:
            movies_to_process = db.query(Movie).filter(
                Movie.genres.isnot(None),
                Movie.rating.isnot(None),
            ).all()
        
        count = 0
        generated_at = datetime.now()
        
        for movie in movies_to_process:
            if not movie.genres or not isinstance(movie.genres, list):
                continue
            
            movie_genre_ids = {
                g.get("id") for g in movie.genres
                if isinstance(g, dict) and g.get("id")
            }
            
            if not movie_genre_ids:
                continue
            
            recommendations = []
            
            all_movies = db.query(Movie).filter(
                Movie.id != movie.id,
                Movie.genres.isnot(None),
                Movie.rating.isnot(None),
            ).all()
            
            for other_movie in all_movies:
                if not other_movie.genres or not isinstance(other_movie.genres, list):
                    continue
                
                other_genre_ids = {
                    g.get("id") for g in other_movie.genres
                    if isinstance(g, dict) and g.get("id")
                }
                
                if not other_genre_ids:
                    continue
                
                overlap = len(movie_genre_ids & other_genre_ids)
                total_genres = len(movie_genre_ids | other_genre_ids)
                genre_score = overlap / total_genres if total_genres > 0 else 0
                
                rating_diff = abs((movie.rating or 0) - (other_movie.rating or 0))
                rating_score = max(0, 1 - (rating_diff / 10))
                
                combined_score = (genre_score * 0.5) + (rating_score * 0.5)
                
                if combined_score > 0.3:
                    recommendations.append({
                        "movie_id": other_movie.id,
                        "title": other_movie.title,
                        "score": round(combined_score, 4),
                        "rating": other_movie.rating,
                    })
            
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            recommendations = recommendations[:10]
            
            if recommendations:
                db.query(MovieRecommendations).filter(
                    MovieRecommendations.movie_id == movie.id
                ).delete()
                
                # Insert new recommendations
                rec_record = MovieRecommendations(
                    movie_id=movie.id,
                    recommendations_json=recommendations,
                    generated_at=generated_at,
                )
                db.add(rec_record)
                count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "recommendations_generated": count,
            "generated_at": generated_at.isoformat(),
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="compute.update_trending")
def update_trending_movies():
    return compute_trending.delay()


@celery_app.task(name="compute.update_underrated")
def update_underrated_movies():
    db = SessionLocal()
    try:
        movies = db.query(Movie).filter(
            Movie.rating >= 7.5,
            Movie.popularity < 30.0,
            Movie.vote_count >= 100,
        ).all()
        
        count = 0
        for movie in movies:
            if not movie.is_underrated:
                movie.is_underrated = True
                count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "movies_updated": count,
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="compute.calculate_analytics")
def calculate_analytics():
    trending_result = compute_trending.delay()
    genre_result = compute_genre_stats.delay()
    decade_result = compute_ratings_by_decade.delay()
    
    return {
        "status": "success",
        "tasks_enqueued": [
            trending_result.id,
            genre_result.id,
            decade_result.id,
        ],
    }

