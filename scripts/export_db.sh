#!/bin/bash
# Export database to SQL file

# Load environment variables
source .env 2>/dev/null || true

# Default values
DB_USER=${POSTGRES_USER:-moviegpt}
DB_PASSWORD=${POSTGRES_PASSWORD:-moviegpt}
DB_NAME=${POSTGRES_DB:-moviegpt}
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5433}

# Export database
echo "Exporting database to data/database_dump.sql..."
docker compose exec -T db pg_dump -U $DB_USER $DB_NAME > data/database_dump.sql

if [ $? -eq 0 ]; then
    echo "Database exported successfully!"
    echo "File size: $(du -h data/database_dump.sql | cut -f1)"
else
    echo "Error: Failed to export database"
    exit 1
fi

