#!/bin/bash

# Database restore script for Carmain PostgreSQL database

# Load environment variables from .env file
if [ -f .env ]; then
    while IFS= read -r line; do
        if [[ $line =~ ^[^#]*= ]]; then
            # Remove spaces around equals sign
            line=$(echo "$line" | sed 's/ *= */=/g')
            export "$line"
        fi
    done < .env
fi

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.sql>"
    echo "Example: $0 carmain_dump_20250602_125000.sql"
    exit 1
fi

BACKUP_FILE=$1

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found!"
    exit 1
fi

echo "Restoring database from: ${BACKUP_FILE}"
echo "Warning: This will drop and recreate the database!"
read -p "Are you sure? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if Docker container is running
    CONTAINER_NAME="carmain-postgres-1"
    if ! docker ps --format "table {{.Names}}" | grep -q "${CONTAINER_NAME}"; then
        echo "Error: PostgreSQL Docker container '${CONTAINER_NAME}' is not running!"
        echo "Please start it with: docker-compose up -d postgres"
        exit 1
    fi
    
    # Terminate active connections to database
    echo "Terminating active connections..."
    docker exec ${CONTAINER_NAME} psql -U ${POSTGRES_USER} -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" 2>/dev/null || true
    
    # Drop and recreate database
    echo "Dropping database..."
    docker exec ${CONTAINER_NAME} dropdb -U ${POSTGRES_USER} ${DB_NAME} 2>/dev/null || true
    
    echo "Creating database..."
    docker exec ${CONTAINER_NAME} createdb -U ${POSTGRES_USER} ${DB_NAME}
    
    echo "Restoring from backup..."
    docker exec -i ${CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${DB_NAME} < ${BACKUP_FILE}
    
    if [ $? -eq 0 ]; then
        echo "Database restored successfully from: ${BACKUP_FILE}"
    else
        echo "Restore failed!"
        exit 1
    fi
else
    echo "Restore cancelled."
fi