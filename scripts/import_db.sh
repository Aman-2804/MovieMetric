#!/bin/bash
# Import database from SQL file

# Load environment variables
source .env 2>/dev/null || true

# Default values
DB_USER=${POSTGRES_USER:-moviegpt}
DB_PASSWORD=${POSTGRES_PASSWORD:-moviegpt}
DB_NAME=${POSTGRES_DB:-moviegpt}
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5433}

DUMP_FILE=${1:-data/database_dump.sql}

if [ ! -f "$DUMP_FILE" ]; then
    echo "Error: Database dump file not found: $DUMP_FILE"
    exit 1
fi

echo "Importing database from $DUMP_FILE..."
docker compose exec -T db psql -U $DB_USER -d $DB_NAME < $DUMP_FILE

if [ $? -eq 0 ]; then
    echo "Database imported successfully!"
else
    echo "Error: Failed to import database"
    exit 1
fi

