"""
Pytest configuration and fixtures
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test database URL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://moviegpt:moviegpt@localhost:5432/moviegpt_test")

from services.api.app.db import Base
from services.api.app.models import Movie


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session"""
    # Create test engine with in-memory SQLite for faster tests
    # Or use a test Postgres database
    engine = create_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
    )
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_movie_data():
    """Sample movie data for testing"""
    return {
        "id": 1,
        "title": "Test Movie",
        "overview": "A test movie overview",
        "release_date": "2020-01-01",
        "rating": 8.5,
        "vote_count": 1000,
        "popularity": 50.0,
        "genres": [{"id": 28, "name": "Action"}],
    }

