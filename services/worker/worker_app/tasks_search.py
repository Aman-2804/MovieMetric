import os
from typing import List, Dict, Any
from celery import Task
from meilisearch import Client
from meilisearch.errors import MeilisearchError
from .celery_app import celery_app
from services.api.app.db import SessionLocal
from services.api.app.models import Movie


def get_meilisearch_client() -> Client:
    meili_url = os.getenv("MEILI_URL", "http://meilisearch:7700")
    meili_key = os.getenv("MEILI_MASTER_KEY", "dev_master_key")
    return Client(meili_url, meili_key)


def movie_to_search_document(movie: Movie) -> Dict[str, Any]:
    release_year = None
    if movie.release_date:
        release_year = movie.release_date.year
    
    genre_names = []
    if movie.genres and isinstance(movie.genres, list):
        for genre in movie.genres:
            if isinstance(genre, dict) and "name" in genre:
                genre_names.append(genre["name"])
    
    return {
        "id": movie.id,
        "title": movie.title or "",
        "overview": movie.overview or "",
        "release_year": release_year,
        "genres": genre_names,
        "vote_average": movie.rating,
        "vote_count": movie.vote_count or 0,
        "popularity": movie.popularity,
    }


@celery_app.task(name="search.build_index", bind=True)
def build_search_index(self: Task):
    db = SessionLocal()
    client = get_meilisearch_client()
    index_name = "movies"
    
    try:
        movies = db.query(Movie).all()
        
        if not movies:
            return {
                "status": "error",
                "message": "No movies found in database",
                "movies_indexed": 0,
            }
        
        documents = [movie_to_search_document(movie) for movie in movies]
        
        try:
            index = client.get_index(index_name)
        except MeilisearchError:
            index = client.create_index(index_name, {"primaryKey": "id"})
            index.update_searchable_attributes(["title", "overview", "genres"])
            index.update_filterable_attributes([
                "release_year",
                "genres",
                "vote_average",
                "vote_count",
                "popularity",
            ])
            index.update_sortable_attributes([
                "release_year",
                "vote_average",
                "vote_count",
                "popularity",
            ])
        
        task_info = index.add_documents(documents)
        
        db.close()
        
        return {
            "status": "success",
            "movies_indexed": len(documents),
            "task_uid": task_info.task_uid,
        }
    except Exception as e:
        db.close()
        return {
            "status": "error",
            "message": str(e),
            "movies_indexed": 0,
        }


@celery_app.task(name="search.index_movie", bind=True)
def index_movie_in_meilisearch(self: Task, movie_id: int):
    db = SessionLocal()
    client = get_meilisearch_client()
    index_name = "movies"
    
    try:
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        
        if not movie:
            db.close()
            return {
                "status": "error",
                "message": f"Movie {movie_id} not found",
                "movie_id": movie_id,
            }
        
        document = movie_to_search_document(movie)
        
        try:
            index = client.get_index(index_name)
        except MeilisearchError:
            index = client.create_index(index_name, {"primaryKey": "id"})
            index.update_searchable_attributes(["title", "overview", "genres"])
            index.update_filterable_attributes(["release_year", "genres", "vote_average", "vote_count", "popularity"])
            index.update_sortable_attributes(["release_year", "vote_average", "vote_count", "popularity"])
        
        task_info = index.add_documents([document])
        
        db.close()
        
        return {
            "status": "success",
            "movie_id": movie_id,
            "task_uid": task_info.task_uid,
        }
    except Exception as e:
        db.close()
        return {
            "status": "error",
            "message": str(e),
            "movie_id": movie_id,
        }


@celery_app.task(name="search.bulk_index", bind=True)
def bulk_index_movies(self: Task, movie_ids: List[int]):
    db = SessionLocal()
    client = get_meilisearch_client()
    index_name = "movies"
    
    try:
        movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        
        if not movies:
            db.close()
            return {
                "status": "error",
                "message": "No movies found",
                "movies_indexed": 0,
            }
        
        documents = [movie_to_search_document(movie) for movie in movies]
        
        try:
            index = client.get_index(index_name)
        except MeilisearchError:
            index = client.create_index(index_name, {"primaryKey": "id"})
            index.update_searchable_attributes(["title", "overview", "genres"])
            index.update_filterable_attributes(["release_year", "genres", "vote_average", "vote_count", "popularity"])
            index.update_sortable_attributes(["release_year", "vote_average", "vote_count", "popularity"])
        
        task_info = index.add_documents(documents)
        
        db.close()
        
        return {
            "status": "success",
            "movies_indexed": len(documents),
            "task_uid": task_info.task_uid,
        }
    except Exception as e:
        db.close()
        return {
            "status": "error",
            "message": str(e),
            "movies_indexed": 0,
        }


@celery_app.task(name="search.update_index", bind=True)
def update_search_index(self: Task):
    return build_search_index()

