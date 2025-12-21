"""
Worker task tests
"""
import os
import pytest
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.api.app.db import Base
from services.api.app.models import Movie, MovieTrendingDaily, GenreStatsDaily, RatingsByDecade
from services.worker.worker_app.tasks_compute import (
    compute_trending,
    compute_genre_stats,
    compute_ratings_by_decade,
)

# Use test database
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://moviegpt:moviegpt@localhost:5432/moviegpt_test")
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    """Create test database session"""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def sample_movies(test_db):
    """Create sample movies for testing"""
    movies = [
        Movie(
            id=1,
            title="Movie 1",
            rating=8.5,
            vote_count=1000,
            popularity=50.0,
            release_date=date(2020, 1, 1),
            genres=[{"id": 28, "name": "Action"}],
        ),
        Movie(
            id=2,
            title="Movie 2",
            rating=7.5,
            vote_count=500,
            popularity=30.0,
            release_date=date(2010, 1, 1),
            genres=[{"id": 35, "name": "Comedy"}],
        ),
    ]
    for movie in movies:
        test_db.add(movie)
    test_db.commit()
    return movies


class TestIngestionTasks:
    """Test ingestion tasks write to database"""
    
    def test_movie_creation(self, test_db, sample_movies):
        """Test that movies are created in database"""
        movies = test_db.query(Movie).all()
        assert len(movies) >= 2
        assert any(m.title == "Movie 1" for m in movies)
        assert any(m.title == "Movie 2" for m in movies)


class TestComputeTasks:
    """Test compute tasks populate artifacts"""
    
    def test_compute_trending_populates_artifacts(self, test_db, sample_movies):
        """Test that compute_trending creates MovieTrendingDaily records"""
        # Run compute task
        result = compute_trending(target_date="2024-01-01")
        
        assert result["status"] == "success"
        
        # Check that records were created
        trending_records = test_db.query(MovieTrendingDaily).all()
        assert len(trending_records) > 0
        
        # Check that records have required fields
        for record in trending_records:
            assert record.movie_id is not None
            assert record.date is not None
            assert record.score is not None
            assert record.rank is not None
    
    def test_compute_genre_stats_populates_artifacts(self, test_db, sample_movies):
        """Test that compute_genre_stats creates GenreStatsDaily records"""
        # Run compute task
        result = compute_genre_stats(target_date="2024-01-01")
        
        assert result["status"] == "success"
        
        # Check that records were created
        genre_stats = test_db.query(GenreStatsDaily).all()
        assert len(genre_stats) > 0
        
        # Check that records have required fields
        for stat in genre_stats:
            assert stat.genre_id is not None
            assert stat.date is not None
            assert stat.volume is not None
    
    def test_compute_ratings_by_decade_populates_artifacts(self, test_db, sample_movies):
        """Test that compute_ratings_by_decade creates RatingsByDecade records"""
        # Run compute task
        result = compute_ratings_by_decade()
        
        assert result["status"] == "success"
        
        # Check that records were created
        decade_stats = test_db.query(RatingsByDecade).all()
        assert len(decade_stats) > 0
        
        # Check that records have required fields
        for stat in decade_stats:
            assert stat.decade is not None
            assert stat.movie_count is not None

