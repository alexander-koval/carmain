#!/bin/bash

# Database backup script for Carmain PostgreSQL database

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

# Create backup with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="carmain_dump_${TIMESTAMP}.sql"

echo "Creating database backup: ${BACKUP_FILE}"
PGPASSWORD=${POSTGRES_PASSWORD} pg_dump -h localhost -U ${POSTGRES_USER} -d ${DB_NAME} > ${BACKUP_FILE}

if [ $? -eq 0 ]; then
    echo "Backup created successfully: ${BACKUP_FILE}"
else
    echo "Backup failed!"
    exit 1
fi
