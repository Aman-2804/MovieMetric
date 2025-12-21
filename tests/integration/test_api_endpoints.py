"""
Integration tests for API endpoints
"""
import os
import pytest
from fastapi.testclient import TestClient
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.api.app.main import app
from services.api.app.models import Movie
from services.api.app.db import Base

# Use test database
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://moviegpt:moviegpt@localhost:5432/moviegpt_test")
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def sample_movie(test_db_session):
    """Create a sample movie in test database"""
    movie = Movie(
        id=1,
        title="Test Movie",
        overview="A test movie",
        release_date=date(2020, 1, 1),
        rating=8.5,
        vote_count=1000,
        popularity=50.0,
        genres=[{"id": 28, "name": "Action"}],
    )
    test_db_session.add(movie)
    test_db_session.commit()
    return movie


class TestMoviesEndpoints:
    """Test movies endpoints"""
    
    def test_list_movies(self, client, sample_movie):
        """Test GET /movies"""
        response = client.get("/movies?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_movie_by_id(self, client, sample_movie):
        """Test GET /movies/{id}"""
        response = client.get(f"/movies/{sample_movie.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_movie.id
        assert data["title"] == sample_movie.title
    
    def test_get_movie_not_found(self, client):
        """Test GET /movies/{id} with non-existent ID"""
        response = client.get("/movies/99999")
        assert response.status_code == 404
    
    def test_trending_movies(self, client, sample_movie):
        """Test GET /movies/trending"""
        response = client.get("/movies/trending?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_top_genres(self, client, sample_movie):
        """Test GET /analytics/top-genres"""
        response = client.get("/analytics/top-genres")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_ratings_by_decade(self, client, sample_movie):
        """Test GET /analytics/ratings-by-decade"""
        response = client.get("/analytics/ratings-by-decade")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Each item should have decade, avg_rating, movie_count
        if len(data) > 0:
            assert "decade" in data[0]
            assert "avg_rating" in data[0]
            assert "movie_count" in data[0]


class TestHealthEndpoints:
    """Test health endpoints"""
    
    def test_health_check(self, client):
        """Test GET /health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "postgres" in data
        assert "redis" in data
        assert "meilisearch" in data


class TestMetricsEndpoints:
    """Test metrics endpoints"""
    
    def test_metrics(self, client):
        """Test GET /metrics"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "requests" in data
        assert "latency" in data
        assert "cache" in data
        assert "jobs" in data

