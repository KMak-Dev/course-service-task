#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting API on http://0.0.0.0:8000"
echo "Open http://localhost:8000/docs for interactive API docs"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
