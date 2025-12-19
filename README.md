# MovieGPT

A FastAPI-based movie database application with analytics capabilities, powered by The Movie Database (TMDB) API.

## Project Overview

This project provides a REST API for querying movie data with advanced analytics features including genre analysis, ratings by decade, and trending/underrated movie discovery.

## What's Been Completed

### 1. **Database Setup**
- PostgreSQL database configured with Docker Compose
- SQLAlchemy models defined (`app/models.py`)
- Database connection and session management (`app/db.py`)
- Movie model with all necessary fields for endpoints

### 2. **Data Ingestion**
- TMDB API integration (`ingest/fetch_tmdb.py`)
- Fetches movies from multiple endpoints:
  - Popular movies (10 pages)
  - Top rated movies (10 pages)
  - Now playing (5 pages)
  - Upcoming releases (5 pages)
  - Trending movies
- Automatically calculates `is_trending` and `is_underrated` flags
- Handles ~600-700 movies per run
- Updates existing movies (no duplicates)

### 3. **Project Structure**
```
MovieGPT/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app (needs implementation)
│   ├── db.py               # Database connection & session
│   ├── models.py           # SQLAlchemy Movie model
│   ├── schemas.py          # Pydantic schemas (needs implementation)
│   ├── deps.py             # Dependencies (needs implementation)
│   ├── create_tables.py    # Table creation script
│   └── routers/
│       ├── movies.py       # Movie endpoints (needs implementation)
│       └── analytics.py    # Analytics endpoints (needs implementation)
├── ingest/
│   └── fetch_tmdb.py       # TMDB data ingestion script
├── docker-compose.yml      # PostgreSQL setup
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API_KEY, DATABASE_URL)
└── README.md               # This file
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- Docker Desktop (for PostgreSQL)
- Git

### Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone git@github.com:Aman-2804/MovieGPT.git
cd MovieGPT

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

The `.env` file should already contain:
```env
API_KEY=fe64f3566cf67db20224033bb11f4d4b
DATABASE_URL=postgresql://moviegpt:moviegpt@localhost:5432/moviegpt
```

**Note:** `.env` is in `.gitignore` for security. If missing, create it with the above values.

### Step 3: Start PostgreSQL Database

```bash
before this open docker and run it
# Start PostgreSQL container
docker compose up -d

# Verify it's running
docker ps
```

You should see a `postgres` container running on port 5432.

### Step 4: Create Database Tables

```bash
# Run from project root
python app/create_tables.py
```

Expected output: `Tables created!!`

### Step 5: Ingest Movie Data from TMDB

```bash
# Fetch movies from TMDB API
python ingest/fetch_tmdb.py
```

This will:
- Fetch ~600-700 movies from TMDB
- Populate the database with movie data
- Calculate trending and underrated flags
- Take a few minutes to complete (due to API rate limiting)

**Expected output:**
```
Starting TMDB data ingestion...
Fetching from popular...
   Processed page 1
   ...
Ingestion Complete!
   Total movies: 650
   Trending: 45
   Underrated: 120
```

