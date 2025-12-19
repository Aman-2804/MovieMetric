from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


# Genre Schema
class GenreOut(BaseModel):
    """Genre information"""
    id: int
    name: str

    class Config:
        from_attributes = True


# Movie Schemas
class MovieOut(BaseModel):
    """Basic movie information"""
    id: int
    title: str
    release_date: Optional[date] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None
    vote_average: Optional[float] = Field(None, description="Average rating")
    vote_count: int = 0
    is_trending: bool = False
    is_underrated: bool = False

    class Config:
        from_attributes = True


class MovieDetailOut(BaseModel):
    """Detailed movie information with genres"""
    id: int
    title: str
    release_date: Optional[date] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None
    vote_average: Optional[float] = Field(None, description="Average rating")
    vote_count: int = 0
    genres: List[GenreOut] = []
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    runtime: Optional[int] = None
    budget: Optional[int] = None
    revenue: Optional[int] = None
    tagline: Optional[str] = None
    status: Optional[str] = None
    is_trending: bool = False
    is_underrated: bool = False

    class Config:
        from_attributes = True


class TrendingMovieOut(BaseModel):
    """Movie information with trending score"""
    id: int
    title: str
    popularity: Optional[float] = None
    vote_average: Optional[float] = Field(None, description="Average rating")
    vote_count: int = 0
    trending_score: float = Field(..., description="Calculated trending score")

    class Config:
        from_attributes = True


# Analytics Schemas
class TopGenreOut(BaseModel):
    """Top genre analytics output"""
    id: int
    name: str
    movie_count: int = Field(..., description="Number of movies in this genre")

    class Config:
        from_attributes = True


class RatingsByDecadeOut(BaseModel):
    """Ratings analytics grouped by decade"""
    decade: int = Field(..., description="Decade (e.g., 1990, 2000)")
    avg_rating: float = Field(..., description="Average rating for movies in this decade")
    movie_count: int = Field(..., description="Number of movies released in this decade")

    class Config:
        from_attributes = True


# Response wrapper schemas
class MessageResponse(BaseModel):
    """Simple message response"""
    ok: bool

