#!/bin/sh
set -e

ADMIN_URL="${ADMIN_DATABASE_URL:-postgresql+psycopg://course:course@db:5432/course_service}"
APP_URL="${DATABASE_URL:-postgresql+psycopg://course_app:course@db:5432/course_service}"

echo "Running database migrations..."
ADMIN_DATABASE_URL="$ADMIN_URL" alembic upgrade head

echo "Ensuring application database role..."
python -m database.bootstrap "$ADMIN_URL"

echo "Starting API on http://0.0.0.0:8000"
echo "Open http://localhost:8000/docs for interactive API docs"
export DATABASE_URL="$APP_URL"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
