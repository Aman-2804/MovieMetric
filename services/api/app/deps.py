from typing import Generator
from sqlalchemy.orm import Session
from .db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.
    
    Yields a database session and ensures it's properly closed after use.
    This should be used as a FastAPI dependency in route handlers.
    
    Usage:
        @router.get("/endpoint")
        def my_endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        >>> from fastapi import Depends
        >>> @router.get("/movies")
        >>> def list_movies(db: Session = Depends(get_db)):
        >>>     return db.query(Movie).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

