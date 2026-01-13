# MovieMetric

**MovieMetric** is a distributed movie analytics backend built with **FastAPI, PostgreSQL, Redis, Celery, and Meilisearch**.  
Instead of querying third-party APIs directly every time, It ingests raw movie data from external APIs, normalizes it into a relational database, precomputes analytics in background jobs, and serves fast, read-only REST APIs for discovery, analytics, and search.



## Key Features

- RESTful API for movie discovery and analytics
- Asynchronous data ingestion and batch processing (Celery + Redis)
- Precomputed analytics (trending scores, genre statistics, decade ratings)
- Full-text search powered by Meilisearch
- Redis caching for low-latency reads
- Health check and metrics endpoints
- Automated tests with CI/CD (GitHub Actions)

## Why Movie Metric

Most movie APIs (like TMDB) are great for lookups, but bad for analytics:

- they push computation to the client
- they don’t support domain-specific metrics (trending, aggregates, time-based stats)
- repeated queries are slow and inefficient

MovieMetric is built to explore how production systems solve this problem:

- ingest once
- compute offline
- serve fast

This mirrors how internal platforms at companies separate batch processing from online serving.

## Architecture Overview

MovieMetric is implemented as a **distributed backend system** with clear separation of responsibilities:

- **API (FastAPI)**  
  Stateless, read-only service that serves precomputed data via REST endpoints.

- **Worker (Celery)**  
  Executes background jobs for ingestion, analytics computation, search indexing, and recommendations.

- **Scheduler (Celery Beat)**  
  Automates periodic ingestion and recomputation of analytics.

- **PostgreSQL**  
  Source of truth for raw data, normalized relations, and precomputed analytics artifacts.

- **Redis**  
  Used as a task queue for background jobs and as a cache for hot API endpoints.

- **Meilisearch**  
  Dedicated full-text search engine for fast, filtered movie search.


---

## Technologies Used

- **Backend:** FastAPI, SQLAlchemy  
- **Database:** PostgreSQL  
- **Async & Jobs:** Celery, Redis  
- **Search:** Meilisearch  
- **Infrastructure:** Docker  
- **CI/CD:** GitHub Actions  

---

### System Architecture & Data Pipeline

#### Service Interaction Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────────────────────────────┐
│           API Service (FastAPI)                 │
│  ┌──────────────────────────────────────────┐  │
│  │  Middleware: Performance Monitoring      │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  Cache Check (Redis)                      │
│  │  ├─ Cache Hit → Return Cached Data      │  │
│  │  └─ Cache Miss → Query Database          │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  Routers: /movies, /analytics, /search   │  │
│  └──────────────────────────────────────────┘  │
└──────┬──────────────────────────────────────┬──┘
       │                                       │
       │ Query                                 │ Enqueue Job
       ▼                                       ▼
┌──────────────┐                    ┌──────────────────┐
│ PostgreSQL   │                    │   Redis Queue    │
│              │                    │  (Celery Broker) │
│ - movies     │                    └────────┬─────────┘
│ - artifacts  │                             │
└──────────────┘                             │ Task Message
                                             ▼
                                    ┌──────────────────┐
                                    │ Worker Service   │
                                    │  (Celery Worker) │
                                    └────────┬─────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
            ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
            │   TMDB API   │        │  PostgreSQL  │        │ Meilisearch  │
            │  (Ingestion) │        │ (Computation)│        │ (Index Build) │
            └──────────────┘        └──────────────┘        └──────────────┘
```

#### Data Pipeline Stages

**1. Data Ingestion Pipeline**
```
TMDB API → Worker Task → PostgreSQL (movies table)
         ↓
    Redis Queue (job tracking)
         ↓
    API Endpoint (/admin/jobs/{id}) for status
```

**2. Analytics Computation Pipeline**
```
PostgreSQL (movies) → Worker Task → PostgreSQL (artifact tables)
                    ↓
              - movie_trending_daily
              - genre_stats_daily
              - ratings_by_decade
              - movie_recommendations
```

**3. Search Index Pipeline**
```
PostgreSQL (movies) → Worker Task → Meilisearch Index
                    ↓
              Full-text search documents
```

**4. API Request Pipeline (with Caching)**
```
Client Request
    ↓
API Middleware (latency tracking)
    ↓
Cache Check (Redis)
    ├─ Hit → Return cached response (fast)
    └─ Miss → Query PostgreSQL
              ↓
         Store in cache
              ↓
         Return response
```

#### Scheduled Task Flow

```
Celery Beat (Scheduler)
    ↓
Scheduled Time Trigger
    ↓
Redis Queue (task message)
    ↓
Worker Picks Up Task
    ↓
Execute Task Logic
    ↓
Update Database/Index
    ↓
Task Complete (status in Redis)
```

## Project Structure

```
MovieGPT/
├── services/
│   ├── api/                    # FastAPI application
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI app entry point
│   │   │   ├── db.py          # Database connection
│   │   │   ├── models.py      # SQLAlchemy models
│   │   │   ├── schemas.py     # Pydantic schemas
│   │   │   ├── cache.py       # Redis caching utilities
│   │   │   ├── middleware.py  # Performance monitoring
│   │   │   └── routers/       # API route handlers
│   │   ├── alembic/           # Database migrations
│   │   └── Dockerfile
│   ├── worker/                 # Celery worker
│   │   ├── worker_app/
│   │   │   ├── celery_app.py  # Celery configuration
│   │   │   ├── tasks_ingest.py
│   │   │   ├── tasks_compute.py
│   │   │   └── tasks_search.py
│   │   └── Dockerfile
│   └── scheduler/              # Celery Beat scheduler
│       └── Dockerfile
├── infra/
│   ├── docker-compose.yml     # Service orchestration
│   └── .env                    # Environment variables
├── tests/                      # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── worker/                # Worker tests
├── scripts/
│   ├── export_db.sh           # Database export
│   └── import_db.sh           # Database import
├── data/
│   └── database_dump.sql      # Pre-populated database
└── requirements.txt           # Python dependencies
```

## Prerequisites

- Python 3.9+
- Docker Desktop
- Git

## Setup

### 1. Clone Repository

```bash
git clone git@github.com:Aman-2804/MovieGPT.git
cd MovieGPT
```

### 2. Environment Variables

Create `infra/.env` with the following:

```env
DATABASE_URL=postgresql+psycopg2://moviegpt:moviegpt@postgres:5432/moviegpt
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
MEILI_URL=http://meilisearch:7700
MEILI_MASTER_KEY=dev_master_key
TMDB_API_KEY=your_tmdb_api_key
```

### 3. Start Services

```bash
cd infra
docker compose up -d
```

This starts all services: PostgreSQL, Redis, Meilisearch, API, Worker, and Scheduler.

### 4. Database Migration

```bash
cd services/api
alembic upgrade head
```

### 5. Populate Database

**Option 1: Import Pre-populated Database (Fastest)**

```bash
./scripts/import_db.sh
```

**Option 2: Trigger Ingestion via API**

```bash
curl -X POST http://localhost:8000/admin/ingest/run
```

Check job status:
```bash
curl http://localhost:8000/admin/jobs/{task_id}
```

### 6. Build Search Index

```bash
curl -X POST http://localhost:8000/admin/search/build-index
```

## Running Locally (Development)

### API Service

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r services/api/requirements.txt

export DATABASE_URL=postgresql://moviegpt:moviegpt@localhost:5432/moviegpt
export REDIS_URL=redis://localhost:6379/0
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_RESULT_BACKEND=redis://localhost:6379/1
export MEILI_URL=http://localhost:7700
export MEILI_MASTER_KEY=dev_master_key
export TMDB_API_KEY=your_api_key

python -m uvicorn services.api.app.main:app --reload
```

### Worker Service

```bash
pip install -r services/worker/requirements.txt

celery -A services.worker.worker_app.celery_app worker --loglevel=info
```

### Scheduler Service

```bash
celery -A services.worker.worker_app.celery_app beat --loglevel=info
```

## API Endpoints

### Movies

- `GET /movies` - List movies with pagination
- `GET /movies/{id}` - Get movie by ID
- `GET /movies/trending` - Get trending movies

### Analytics

- `GET /analytics/top-genres` - Top genres by volume
- `GET /analytics/ratings-by-decade` - Average ratings by decade

### Search

- `GET /search?q={query}` - Full-text search with filters
  - Query params: `min_rating`, `year`, `genre`, `limit`, `offset`

### Admin

- `POST /admin/ingest/run` - Trigger data ingestion
- `POST /admin/compute/trending` - Compute trending scores
- `POST /admin/compute/genre-stats` - Compute genre statistics
- `POST /admin/compute/ratings-by-decade` - Compute ratings by decade
- `POST /admin/compute/recommendations` - Generate recommendations
- `POST /admin/compute/all` - Run all compute tasks
- `POST /admin/search/build-index` - Build Meilisearch index
- `GET /admin/jobs/{task_id}` - Get job status

### Health & Metrics

- `GET /health` - Service health checks
- `GET /metrics` - System metrics and performance data

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Testing ensures your system works correctly and catches regressions when code changes. This project includes three types of tests that verify different aspects of the system.

### Test Types

**A. Unit Tests** (Fast, Pure Logic)
- Test mathematical formulas and business rules without databases
- Examples: trending score calculation, recommendation similarity scoring
- Run in milliseconds, no external dependencies
- Location: `tests/unit/`

**B. Integration Tests** (API + Database)
- Test real API endpoints with actual database connections
- Verify routes are wired correctly, queries work, and JSON contracts are maintained
- Use a test database with known data
- Location: `tests/integration/`

**C. Worker Tests** (Background Jobs)
- Verify Celery tasks actually perform their work
- Test that ingestion tasks write to database, compute tasks populate artifact tables
- Critical because workers can fail silently in production
- Location: `tests/worker/`

### Run Tests

```bash
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
pytest tests/worker/

# With coverage
pytest --cov=services --cov-report=html
```

## CI/CD

**Continuous Integration (CI)** automatically runs tests on every code push, ensuring the system works correctly before changes are merged.

### CI Configuration

See `.github/workflows/ci.yml` for the complete workflow configuration.

The CI pipeline:
- Runs on every push/PR to `main` and `develop` branches
- Sets up PostgreSQL, Redis, and Meilisearch as services
- Runs all test suites
- Generates coverage reports

## Scheduled Tasks

Celery Beat runs the following scheduled tasks:

- **Nightly (2:00 AM UTC)**: Full data ingestion
- **Nightly (3:00 AM UTC)**: Trending computation
- **Nightly (3:15 AM UTC)**: Genre stats computation
- **Weekly (Monday 4:00 AM UTC)**: Search index rebuild
- **Weekly (Monday 5:00 AM UTC)**: Recommendations recomputation

## License

MIT
