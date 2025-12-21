"""
Unit tests for recommendation score calculation
"""
import pytest


def calculate_recommendation_score(
    movie_genre_ids: set,
    other_genre_ids: set,
    movie_rating: float,
    other_rating: float
) -> float:
    """
    Calculate recommendation score using the same formula as the worker
    
    Score = (genre_overlap_ratio * 0.5) + (rating_similarity * 0.5)
    """
    # Calculate genre overlap
    overlap = len(movie_genre_ids & other_genre_ids)
    total_genres = len(movie_genre_ids | other_genre_ids)
    genre_score = overlap / total_genres if total_genres > 0 else 0
    
    # Calculate rating similarity (normalized difference)
    rating_diff = abs(movie_rating - other_rating)
    rating_score = max(0, 1 - (rating_diff / 10))  # Normalize to 0-1
    
    # Combined score
    combined_score = (genre_score * 0.5) + (rating_score * 0.5)
    
    return combined_score


class TestRecommendationScoring:
    """Test recommendation score calculation"""
    
    def test_perfect_match(self):
        """Test perfect genre and rating match"""
        score = calculate_recommendation_score(
            movie_genre_ids={1, 2, 3},
            other_genre_ids={1, 2, 3},
            movie_rating=8.0,
            other_rating=8.0
        )
        assert score == 1.0  # Perfect match
    
    def test_no_genre_overlap(self):
        """Test movies with no genre overlap"""
        score = calculate_recommendation_score(
            movie_genre_ids={1, 2},
            other_genre_ids={3, 4},
            movie_rating=8.0,
            other_rating=8.0
        )
        # Should only have rating similarity component
        assert 0 < score < 0.6
    
    def test_partial_genre_overlap(self):
        """Test movies with partial genre overlap"""
        score = calculate_recommendation_score(
            movie_genre_ids={1, 2, 3},
            other_genre_ids={2, 3, 4},
            movie_rating=8.0,
            other_rating=8.0
        )
        # 2 out of 4 genres overlap = 0.5 genre score
        # Same rating = 1.0 rating score
        # Expected: (0.5 * 0.5) + (1.0 * 0.5) = 0.75
        assert abs(score - 0.75) < 0.01
    
    def test_rating_difference_impact(self):
        """Test that larger rating differences reduce score"""
        score1 = calculate_recommendation_score(
            movie_genre_ids={1, 2},
            other_genre_ids={1, 2},
            movie_rating=8.0,
            other_rating=8.0
        )
        score2 = calculate_recommendation_score(
            movie_genre_ids={1, 2},
            other_genre_ids={1, 2},
            movie_rating=8.0,
            other_rating=3.0
        )
        assert score1 > score2
    
    def test_genre_overlap_impact(self):
        """Test that more genre overlap increases score"""
        score1 = calculate_recommendation_score(
            movie_genre_ids={1, 2, 3, 4},
            other_genre_ids={1},
            movie_rating=8.0,
            other_rating=8.0
        )
        score2 = calculate_recommendation_score(
            movie_genre_ids={1, 2, 3, 4},
            other_genre_ids={1, 2, 3},
            movie_rating=8.0,
            other_rating=8.0
        )
        assert score2 > score1
    
    def test_score_range(self):
        """Test that scores are in valid range [0, 1]"""
        scores = [
            calculate_recommendation_score(
                {1, 2}, {3, 4}, 1.0, 10.0
            ),  # No overlap, large rating diff
            calculate_recommendation_score(
                {1, 2}, {1, 2}, 8.0, 8.0
            ),  # Perfect match
        ]
        
        for score in scores:
            assert 0 <= score <= 1
    
    def test_empty_genres(self):
        """Test handling of empty genre sets"""
        score = calculate_recommendation_score(
            movie_genre_ids=set(),
            other_genre_ids={1, 2},
            movie_rating=8.0,
            other_rating=8.0
        )
        # Should only have rating similarity
        assert 0 < score < 0.6

