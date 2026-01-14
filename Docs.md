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
