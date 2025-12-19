# MovieGPT

A FastAPI-based movie database application with analytics capabilities, powered by The Movie Database (TMDB) API.

## Project Overview

This project provides a REST API for querying movie data with advanced analytics features including genre analysis, ratings by decade, and trending/underrated movie discovery.

## What's Been Completed

### 1. **Database Setup**
- PostgreSQL database configured with Docker Compose
- SQLAlchemy models defined (`services/api/app/models.py`)
- Database connection and session management (`services/api/app/db.py`)
- Movie model with all necessary fields for endpoints

### 2. **Data Ingestion & Database Management**
- TMDB API integration (`ingest/fetch_tmdb.py`)
- Fetches movies from multiple endpoints:
  - Popular movies (30 pages)
  - Top rated movies (30 pages)
  - Now playing (10 pages)
  - Upcoming releases (10 pages)
  - Trending movies
  - Discover endpoint with multiple filters
- Automatically calculates `is_trending` and `is_underrated` flags
- Handles 1000+ movies per run
- Updates existing movies (no duplicates)
- Database export/import scripts (`scripts/export_db.sh`, `scripts/import_db.sh`)
  - Share database dumps via git
  - Quick setup for team members

### 3. **Project Structure**
```
MovieGPT/
├── services/
│   └── api/
│       └── app/
│           ├── __init__.py
│           ├── main.py              # FastAPI app
│           ├── db.py               # Database connection & session
│           ├── models.py           # SQLAlchemy Movie model
│           ├── schemas.py          # Pydantic schemas
│           ├── deps.py             # Dependencies
│           ├── create_tables.py    # Table creation script
│           └── routers/
│               ├── movies.py       # Movie endpoints
│               └── analytics.py    # Analytics endpoints
├── ingest/
│   └── fetch_tmdb.py       # TMDB data ingestion script
├── scripts/
│   ├── export_db.sh        # Export database to SQL dump
│   └── import_db.sh        # Import database from SQL dump
├── data/
│   └── database_dump.sql   # Database dump file (committed to git)
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
python services/api/app/create_tables.py
```

Expected output: `Tables created!!`

### Step 5: Populate Database with Movie Data

You have **two options** to get movie data:

#### Option 1: Import Pre-populated Database (Recommended - Fastest)

If a database dump is available in the repository, import it:

```bash
# Import the database dump
./scripts/import_db.sh
```

This will load all movies from the shared database dump (takes seconds).

#### Option 2: Fetch Movies from TMDB API

Alternatively, fetch your own data from TMDB:

```bash
# Fetch movies from TMDB API
python ingest/fetch_tmdb.py
```

This will:
- Fetch 1000+ movies from TMDB
- Populate the database with movie data
- Calculate trending and underrated flags
- Take 15-20 minutes to complete (due to API rate limiting)

**Expected output:**
```
Starting TMDB data ingestion...
Fetching from popular...
   Processed page 1
   ...
Ingestion Complete!
   Total movies: 1200
   Trending: 45
   Underrated: 120
```

**Note:** Choose Option 1 if you want the same data as the team. Choose Option 2 if you want fresh data or more movies.

### Step 6: Run the Application

```bash
# Activate venv
source .venv/bin/activate

# Run with python -m to ensure correct interpreter
python -m uvicorn services.api.app.main:app --reload
```

The API will be available at:
- API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs