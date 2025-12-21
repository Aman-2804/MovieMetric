from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, Text, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from .db import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    overview = Column(Text, nullable=True)
    release_date = Column(Date, nullable=True, index=True)
    genre = Column(String, nullable=True, index=True)  # Can be comma-separated or JSON
    genres = Column(JSON, nullable=True)  # Array of genre objects
    rating = Column(Float, nullable=True, index=True)  # Average rating
    vote_count = Column(Integer, default=0)  # Number of votes
    popularity = Column(Float, nullable=True, index=True)  # For trending
    poster_path = Column(String, nullable=True)
    backdrop_path = Column(String, nullable=True)
    runtime = Column(Integer, nullable=True)  # Duration in minutes
    budget = Column(BigInteger, nullable=True)  # Changed to BigInteger for large values
    revenue = Column(BigInteger, nullable=True)  # Changed to BigInteger for large values
    tagline = Column(String, nullable=True)
    status = Column(String, nullable=True)  # Released, Post Production, etc.
    is_trending = Column(Boolean, default=False, index=True)
    is_underrated = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MovieTrendingDaily(Base):
    """Daily trending movie scores and rankings"""
    __tablename__ = "movie_trending_daily"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    score = Column(Float, nullable=False)  # Computed trending score
    rank = Column(Integer, nullable=False)  # Ranking for that date (1 = most trending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('movie_id', 'date', name='uq_movie_trending_daily'),
    )


class GenreStatsDaily(Base):
    """Daily statistics per genre"""
    __tablename__ = "genre_stats_daily"

    id = Column(Integer, primary_key=True, index=True)
    genre_id = Column(Integer, nullable=False, index=True)  # TMDB genre ID
    genre_name = Column(String, nullable=False)  # Genre name for convenience
    date = Column(Date, nullable=False, index=True)
    avg_rating = Column(Float, nullable=True)  # Average rating of movies in this genre
    volume = Column(Integer, default=0)  # Number of movies in this genre
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('genre_id', 'date', name='uq_genre_stats_daily'),
    )


class RatingsByDecade(Base):
    """Average ratings aggregated by decade"""
    __tablename__ = "ratings_by_decade"

    id = Column(Integer, primary_key=True, index=True)
    decade = Column(Integer, nullable=False, unique=True, index=True)  # e.g., 1990, 2000, 2010
    avg_rating = Column(Float, nullable=True)  # Average rating for movies in this decade
    movie_count = Column(Integer, default=0)  # Number of movies in this decade
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MovieRecommendations(Base):
    """Precomputed movie recommendations"""
    __tablename__ = "movie_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)
    recommendations_json = Column(JSON, nullable=False)  # Array of recommended movie IDs with scores
    generated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

