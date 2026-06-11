# Course Service

Multi-tenant online course backend (FastAPI + PostgreSQL + RLS).

## Quick start (Docker)

```bash
docker compose up --build
```

When the API is ready:

- Health: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs
- Postgres: `localhost:5432` (user `course`, password `course`, db `course_service`)

The `api` service runs Alembic migrations on startup, then serves the app on port **8000**.

Stop with `Ctrl+C`, or run detached:

```bash
docker compose up --build -d
docker compose down      # stop
docker compose down -v   # stop and wipe database volume
```

## Manual API test (curl)

Create a provider:

```bash
curl -s -X POST http://localhost:8000/providers \
  -H "Content-Type: application/json" \
  -d '{"name": "Provider A"}' | jq
```

Save the returned `id`, then:

```bash
export PROVIDER_ID="<paste-id-here>"

# List all providers
curl -s http://localhost:8000/providers | jq

# Get one provider
curl -s http://localhost:8000/providers/$PROVIDER_ID | jq

# Update
curl -s -X PATCH http://localhost:8000/providers/$PROVIDER_ID \
  -H "Content-Type: application/json" \
  -d '{"name": "Provider A (updated)"}' | jq

# Delete
curl -s -X DELETE http://localhost:8000/providers/$PROVIDER_ID -w "\nHTTP %{http_code}\n"
```

Interactive testing is easiest via **http://localhost:8000/docs**.

## Local development (without Docker for the API)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
docker compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
```

## Stack

- **FastAPI** — HTTP API
- **SQLAlchemy 2.0 (async)** — ORM + statement-based CRUD layer
- **Alembic** — migrations
- **PostgreSQL 16** — database with row-level security (RLS)

## Architecture

```
routes/   → HTTP handlers (Pydantic in/out)
crud/     → database access (select / insert / update / delete)
models/   → SQLAlchemy ORM models
schemas/  → Pydantic request/response models
```

Tenant isolation uses `provider_id` on all tenant-owned tables and PostgreSQL RLS policies keyed on session variable `app.current_provider_id`.

## Tests

Integration tests use [Testcontainers](https://testcontainers.com/) to start a temporary PostgreSQL 16 instance, run Alembic migrations, and exercise the API in-process via `httpx` (no separate server). **Docker must be running.**

```bash
pip install -e ".[dev]"
pytest -v
```

## Assumptions / out of scope

- No authentication — `provider_id` in the URL stands in for future auth
- No video upload, streaming, search, or frontend
- Provider list (`GET /providers`) is open; other provider mutations require tenant context via RLS
