import os
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from meilisearch import Client
from meilisearch.errors import MeilisearchError
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/search", tags=["search"])


def get_meilisearch_client() -> Client:
    meili_url = os.getenv("MEILI_URL", "http://localhost:7700")
    meili_key = os.getenv("MEILI_MASTER_KEY", "dev_master_key")
    return Client(meili_url, meili_key)


class SearchResult(BaseModel):
    id: int
    title: str
    overview: Optional[str] = None
    release_year: Optional[int] = None
    genres: List[str] = []
    vote_average: Optional[float] = None
    vote_count: int = 0
    popularity: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    hits: List[SearchResult]
    total: int
    limit: int
    offset: int


@router.get("", response_model=SearchResponse)
def search_movies(
    q: str = Query(..., description="Search query string"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum rating filter"),
    year: Optional[int] = Query(None, description="Filter by release year"),
    genre: Optional[str] = Query(None, description="Filter by genre name"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    client = get_meilisearch_client()
    index_name = "movies"
    
    try:
        index = client.get_index(index_name)
    except MeilisearchError:
        raise HTTPException(
            status_code=503,
            detail="Search index not available. Please build the index first using /admin/search/build-index"
        )
    
    # Build filter string
    filters = []
    
    if min_rating is not None:
        filters.append(f"vote_average >= {min_rating}")
    
    if year is not None:
        filters.append(f"release_year = {year}")
    
    if genre is not None:
        # Genre filter - Meilisearch array filter syntax
        filters.append(f'genres = "{genre}"')
    
    filter_string = " AND ".join(filters) if filters else None
    
    # Perform search
    try:
        search_results = index.search(
            q,
            {
                "limit": limit,
                "offset": offset,
                "filter": filter_string,
            }
        )
        
        # Convert hits to SearchResult models
        hits = [
            SearchResult(
                id=hit["id"],
                title=hit.get("title", ""),
                overview=hit.get("overview"),
                release_year=hit.get("release_year"),
                genres=hit.get("genres", []),
                vote_average=hit.get("vote_average"),
                vote_count=hit.get("vote_count", 0),
                popularity=hit.get("popularity"),
            )
            for hit in search_results["hits"]
        ]
        
        return SearchResponse(
            query=q,
            hits=hits,
            total=search_results["estimatedTotalHits"],
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

