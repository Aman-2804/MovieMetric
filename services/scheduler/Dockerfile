FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy worker requirements (scheduler uses same dependencies as worker)
COPY services/worker/requirements.txt ./services/worker/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r services/worker/requirements.txt

# Copy services directory
COPY services ./services

# Set working directory
WORKDIR /app

# Run Celery Beat scheduler
CMD ["celery", "-A", "services.worker.worker_app.celery_app", "beat", "--loglevel=info"]

