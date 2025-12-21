"""
Unit tests for trending score calculation
"""
import math
import pytest


def calculate_trending_score(popularity: float, rating: float, vote_count: int) -> float:
    """
    Calculate trending score using the same formula as the worker
    
    Formula: (popularity * 0.4) + (rating * 20 * 0.3) + (log(vote_count + 1) * 10 * 0.3)
    """
    return (
        (popularity * 0.4) +
        (rating * 20 * 0.3) +
        (math.log(vote_count + 1) * 10 * 0.3)
    )


class TestTrendingScoring:
    """Test trending score calculation"""
    
    def test_basic_scoring(self):
        """Test basic score calculation"""
        score = calculate_trending_score(
            popularity=50.0,
            rating=8.5,
            vote_count=1000
        )
        assert score > 0
        assert isinstance(score, float)
    
    def test_higher_popularity_higher_score(self):
        """Test that higher popularity results in higher score"""
        score1 = calculate_trending_score(30.0, 8.0, 500)
        score2 = calculate_trending_score(60.0, 8.0, 500)
        assert score2 > score1
    
    def test_higher_rating_higher_score(self):
        """Test that higher rating results in higher score"""
        score1 = calculate_trending_score(50.0, 7.0, 500)
        score2 = calculate_trending_score(50.0, 9.0, 500)
        assert score2 > score1
    
    def test_higher_vote_count_higher_score(self):
        """Test that higher vote count results in higher score"""
        score1 = calculate_trending_score(50.0, 8.0, 100)
        score2 = calculate_trending_score(50.0, 8.0, 1000)
        assert score2 > score1
    
    def test_zero_values(self):
        """Test handling of zero values"""
        score = calculate_trending_score(0.0, 0.0, 0)
        assert score == 0.0
    
    def test_very_high_vote_count(self):
        """Test handling of very high vote counts"""
        score = calculate_trending_score(50.0, 8.0, 1000000)
        assert score > 0
        # Should not be infinite
        assert math.isfinite(score)
    
    def test_ranking_order(self):
        """Test that scores rank movies correctly"""
        movies = [
            {"popularity": 100.0, "rating": 9.0, "vote_count": 5000, "name": "Top Movie"},
            {"popularity": 50.0, "rating": 8.0, "vote_count": 2000, "name": "Mid Movie"},
            {"popularity": 10.0, "rating": 6.0, "vote_count": 100, "name": "Low Movie"},
        ]
        
        scored = [
            {
                **movie,
                "score": calculate_trending_score(
                    movie["popularity"],
                    movie["rating"],
                    movie["vote_count"]
                )
            }
            for movie in movies
        ]
        
        sorted_movies = sorted(scored, key=lambda x: x["score"], reverse=True)
        
        # Top movie should have highest score
        assert sorted_movies[0]["name"] == "Top Movie"
        assert sorted_movies[0]["score"] > sorted_movies[1]["score"]
        assert sorted_movies[1]["score"] > sorted_movies[2]["score"]

