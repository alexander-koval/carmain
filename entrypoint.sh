#!/bin/bash

# Exit on error
set -e

# Create logs directory
mkdir -p /app/logs

# Run database migrations (if using alembic)
echo "Running database migrations..."
alembic upgrade head

# Start gunicorn with logging to both stderr and file
echo "Starting Carmain application..."
exec gunicorn carmain.main:carmain -c gunicorn.conf.py 2>&1 | tee /app/logs/error.log