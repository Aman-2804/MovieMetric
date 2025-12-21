FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy API requirements
COPY services/api/requirements.txt ./services/api/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r services/api/requirements.txt

# Copy services directory
COPY services ./services

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "services.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

