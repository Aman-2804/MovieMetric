from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.db import Base


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

