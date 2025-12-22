# MovieMetric

**MovieMetric** is a distributed movie analytics backend built with **FastAPI, PostgreSQL, Redis, Celery, and Meilisearch**.  
It ingests raw movie data from external APIs, normalizes it into a relational database, precomputes analytics in background jobs, and serves fast, read-only REST APIs for discovery, analytics, and search.

> Designed to mirror how internal analytics platforms are built in production systems by separating offline batch processing from online serving.

---

## Key Features

- RESTful API for movie discovery and analytics
- Asynchronous data ingestion and batch processing (Celery + Redis)
- Precomputed analytics (trending scores, genre statistics, decade ratings)
- Full-text search powered by Meilisearch
- Redis caching for low-latency reads
- Health check and metrics endpoints
- Automated tests with CI/CD (GitHub Actions)

---

## Problem & Solution

### The Problem

Third-party movie APIs (such as TMDB) are optimized for lookup, not analytics.  
They push computation to the client, lack domain-specific logic (e.g. trending, aggregates), and are inefficient for high-frequency internal queries.

### The Solution

MovieMetric transforms raw movie data into **analytics-ready artifacts** by:

- ingesting and normalizing data into PostgreSQL
- computing analytics offline using batch jobs
- exposing fast, purpose-built APIs for internal consumption

This system is designed as an **internal analytics platform**, not a consumer-facing application.

---

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

> Heavy computation is performed offline; the API layer only serves fast reads.

---

## Technologies Used

- **Backend:** FastAPI, SQLAlchemy  
- **Database:** PostgreSQL  
- **Async & Jobs:** Celery, Redis  
- **Search:** Meilisearch  
- **Infrastructure:** Docker  
- **CI/CD:** GitHub Actions  

---

## Data Flow

This is what actually happens in the system.

### A. Ingestion Flow (Offline)

```
TMDB API
   ↓
Worker (ingestion job)
   ↓
Postgres (raw tables)
```

- Happens asynchronously
- Can be retried safely
- Scales by adding workers

### B. Processing Flow (Offline)

```
Postgres (raw data)
   ↓
Worker (batch compute)
   ↓
Postgres (artifact tables)
```

**Artifacts include:**
- Trending rankings (`movie_trending_daily`)
- Genre statistics (`genre_stats_daily`)
- Decade aggregates (`ratings_by_decade`)
- Recommendations (`movie_recommendations`)

**Key idea:** Analytics are computed once, not on every request.

### C. Serving Flow (Online)

```
Client
   ↓
API
   ↓
Redis (if cached)
   ↓
Postgres / Meilisearch
```

- Fast
- Predictable
- Low latency

## What Makes This a "System" (Not Just an App)

### Before (Simple App)
- One process
- Everything happens on request
- Hard to scale
- Hard to reason about

### Now (MovieMetric)
- Multiple services
- Clear ownership of responsibilities
- Async vs sync separation
- Batch vs online workloads

**You didn't just add features — you changed where work happens. That's system design.**

## Why Precomputed Analytics Matter

### The Problem with On-Demand Computation

**Traditional Approach:**
```
Every time someone asks for trending movies:
  1. Query all movies
  2. Calculate scores
  3. Sort and rank
  4. Return results
```

**Problems:**
- High latency (seconds per request)
- High database load
- Inconsistent performance
- Doesn't scale

### The MovieMetric Approach

**Instead:**
```
Compute trending once (nightly):
  1. Worker calculates all scores
  2. Stores results in artifact table
  3. API reads precomputed data
  4. Returns results in milliseconds
```

**Benefits:**
- ✅ Reduces latency (milliseconds vs seconds)
- ✅ Reduces DB load (simple SELECT vs complex computation)
- ✅ Improves reliability (predictable performance)
- ✅ Mirrors real analytics platforms (Redshift, BigQuery, etc.)

**This is one of the most important design decisions in MovieMetric.**

The system separates:
- **Write operations** (ingestion, computation) → Worker
- **Read operations** (API queries) → Fast, cached responses

This architecture pattern is used by companies like Netflix, Spotify, and Amazon for their analytics platforms.

## Architecture

The application consists of multiple services orchestrated with Docker Compose:

- **API Service**: FastAPI application serving REST endpoints
- **Worker Service**: Celery worker for background tasks (ingestion, computation)
- **Scheduler Service**: Celery Beat for scheduled tasks
- **PostgreSQL**: Primary database for movie data
- **Redis**: Message broker and cache
- **Meilisearch**: Full-text search engine

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

#### How Services Communicate

**API ↔ Worker (via Redis)**
- API enqueues jobs to Redis queue
- Worker picks up jobs from Redis
- Results stored in Redis backend
- API polls Redis for job status

**API ↔ PostgreSQL**
- Direct SQLAlchemy connections
- Connection pooling (10 connections, max 20 overflow)
- Read operations for API responses

**API ↔ Redis (Caching)**
- Cache-aside pattern
- TTL-based expiration (default 1 hour)
- Cache key format: `prefix:arg1:arg2:...`

**API ↔ Meilisearch**
- Direct HTTP client connections
- Search queries bypass PostgreSQL
- Index updates via worker tasks

**Worker ↔ External Services**
- TMDB API: HTTP requests with rate limiting
- PostgreSQL: Write operations for ingestion/computation
- Meilisearch: Bulk document indexing

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

**Scheduled Tasks:**
- **2:00 AM UTC**: Full data ingestion from TMDB
- **3:00 AM UTC**: Compute trending scores
- **3:15 AM UTC**: Compute genre statistics
- **Monday 4:00 AM UTC**: Rebuild search index
- **Monday 5:00 AM UTC**: Recompute recommendations

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

### Why Testing Matters

- **Catch regressions**: Know immediately if changes break existing functionality
- **Documentation**: Tests serve as executable examples of how the system works
- **Confidence**: Deploy with confidence knowing the system works correctly
- **Professional standard**: Demonstrates engineering maturity and respect for maintainability

## CI/CD

**Continuous Integration (CI)** automatically runs tests on every code push, ensuring the system works correctly before changes are merged.

### How CI Works

When you push code to GitHub:

1. GitHub spins up a temporary virtual machine
2. Services are started (PostgreSQL, Redis, Meilisearch) - just like Docker Compose
3. Dependencies are installed
4. All tests run automatically:
   - Unit tests
   - Integration tests
   - Worker tests
5. Results are reported:
   - ✅ Green checkmark if all tests pass
   - ❌ Red X if any test fails

### Benefits

- **Automatic validation**: Every push is tested, not just when you remember
- **Early detection**: Catch bugs before they reach production
- **Team confidence**: Everyone knows the codebase is working
- **Professional standard**: Demonstrates engineering maturity

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

## Database Management

### Export Database

```bash
./scripts/export_db.sh
```

Creates `data/database_dump.sql` with all movie data.

### Import Database

```bash
./scripts/import_db.sh
```

Imports from `data/database_dump.sql`.

## Environment Variables

### Required

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `CELERY_BROKER_URL` - Celery broker URL
- `CELERY_RESULT_BACKEND` - Celery result backend URL
- `MEILI_URL` - Meilisearch URL
- `MEILI_MASTER_KEY` - Meilisearch master key
- `TMDB_API_KEY` - The Movie Database API key

### Local Development

For local development, use `localhost` instead of service names:

```env
DATABASE_URL=postgresql://moviegpt:moviegpt@localhost:5432/moviegpt
REDIS_URL=redis://localhost:6379/0
MEILI_URL=http://localhost:7700
```

## Performance

- **Caching**: Redis cache-aside pattern for hot reads
- **Monitoring**: Request latency tracking and cache hit/miss rates
- **Metrics**: Real-time performance metrics via `/metrics` endpoint

## Development

### Adding New Endpoints

1. Create route handler in `services/api/app/routers/`
2. Add Pydantic schemas in `services/api/app/schemas.py`
3. Register router in `services/api/app/main.py`

### Adding New Tasks

1. Create task function in `services/worker/worker_app/tasks_*.py`
2. Register in `services/worker/worker_app/celery_app.py`
3. Add admin endpoint to trigger task

### Database Migrations

```bash
cd services/api
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Troubleshooting

### Services Not Starting

```bash
cd infra
docker compose logs
docker compose ps
```

### Database Connection Issues

Verify PostgreSQL is running:
```bash
docker compose ps postgres
```

Check connection string in `infra/.env`.

### Worker Not Processing Jobs

Check worker logs:
```bash
docker compose logs worker
```

Verify Redis is accessible:
```bash
docker compose exec redis redis-cli ping
```

## License

MIT
