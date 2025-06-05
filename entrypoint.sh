#!/bin/bash

# Exit on error
set -e

# Create logs directory
mkdir -p /app/logs

# Wait for database to be ready
echo "Waiting for database..."
python -c "
import os
import time
import socket
from urllib.parse import urlparse

# Get DATABASE_URL from environment (set in Portainer)
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print('DATABASE_URL environment variable is not set')
    exit(1)

parsed = urlparse(db_url)
host = parsed.hostname
port = parsed.port or 5432

max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print('Database is ready!')
            break
        else:
            raise ConnectionError('Connection failed')
    except Exception as e:
        attempt += 1
        print(f'Database not ready (attempt {attempt}/{max_attempts})')
        time.sleep(2)
else:
    print('Failed to connect to database after maximum attempts')
    exit(1)
"

# Run database migrations
echo "Running database migrations..."
python -c "
from alembic.config import Config
from alembic import command

# Configure alembic
alembic_cfg = Config('alembic.ini')

print('Applying database migrations...')
command.upgrade(alembic_cfg, 'head')
print('Database migrations applied successfully!')
"

# Start gunicorn with logging to both stderr and file
echo "Starting Carmain application..."
exec gunicorn carmain.main:carmain -c gunicorn.conf.py 2>&1 | tee /app/logs/error.log