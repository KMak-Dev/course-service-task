# Course Service

> [Deutsche Version](README.md)

Backend foundation for a **multi-tenant online course platform**: providers manage their own courses, nested chapters, lessons, and per-lesson video metadata. Built with **FastAPI**, **PostgreSQL 16**, and **Row Level Security (RLS)**.

## Technology choices

| Choice | Why |
|--------|-----|
| **Python + FastAPI** | Async-first HTTP API with automatic OpenAPI docs; Pydantic gives request/response validation out of the box. |
| **SQLAlchemy 2.0 (async)** | Mature ORM with explicit statement-based CRUD; fits layered architecture without heavy magic. |
| **PostgreSQL 16** | Native RLS for database-enforced tenant isolation; `TEXT` columns support future full-text search on subtitles. |
| **Alembic** | Versioned schema migrations including RLS policies. |
| **Testcontainers** | Integration tests against real PostgreSQL with the same RLS behavior as Docker/local runtime. |

## Architecture

```
app/routes/    → HTTP handlers (Pydantic in/out, Depends for DB sessions)
app/crud/      → database access (select / insert / update / delete)
app/models/    → SQLAlchemy ORM models
app/schemas/   → Pydantic request/response models
app/database/  → engine, session dependencies, app-role bootstrap
```

**Request flow:** route → CRUD → PostgreSQL. Tenant-scoped routes inject a DB session that sets `app.current_provider_id`; RLS policies filter rows automatically.

**API shape:** nested REST resources under `/providers/{provider_id}/…` so provider scoping is explicit in every URL. No authentication layer — `provider_id` in the path stands in for a future auth token.

**Tenant keys:** every tenant table has `provider_id` with a **foreign key to `providers`** (migration `003`). The column is also denormalized on child rows so RLS policies stay simple; there is no additional constraint ensuring e.g. `chapters.provider_id` matches the parent course's `provider_id`.

## Domain model

| Entity | Relationships | Notes |
|--------|---------------|-------|
| **Provider** | owns many courses | Tenant root |
| **Course** | belongs to provider; has many chapters | `title`, `description` |
| **Chapter** | belongs to course; **nestable** via `parent_id` | `title`, `description`, `sort_order`; cycle prevention on update |
| **Lesson** | belongs to chapter | `title`, `sort_order` |
| **LessonVideo** | one per lesson (1:1) | metadata only — no upload/streaming |

**Video metadata fields:** `title`, `description`, `file_id`, `subtitle_text`.

`subtitle_text` is stored as PostgreSQL `TEXT` (not `VARCHAR`), which is the standard starting point for a future searchable field — e.g. a `tsvector` generated column and GIN index for full-text search. Search itself is out of scope.

## API overview

| Resource | Prefix | CRUD |
|----------|--------|------|
| Providers | `/providers` | list + create (open); get/update/delete (tenant-scoped) |
| Courses | `/providers/{provider_id}/courses` | full CRUD |
| Chapters | `…/courses/{course_id}/chapters` | full CRUD; `parent_id` / `roots_only` query params |
| Lessons | `…/chapters/{chapter_id}/lessons` | full CRUD |
| Video metadata | `…/lessons/{lesson_id}/video` | GET / POST / PATCH / DELETE (singular resource) |

Interactive docs (FastAPI Swagger UI): http://localhost:8000/docs

## Row Level Security (RLS)

### Why RLS

In a multi-tenant system, application bugs or forgotten `WHERE` clauses can leak data across tenants. RLS enforces isolation **in the database** for every query from the application role — including ad-hoc access and future code paths.

### How it works

1. Every tenant-owned table has a `provider_id` column.
2. Before tenant-scoped requests, the app sets a session variable:
   ```sql
   SELECT set_config('app.current_provider_id', '<uuid>', true);
   ```
3. Alembic migration `002_enable_rls` enables **FORCE ROW LEVEL SECURITY** on tenant tables with policies like:
   ```sql
   provider_id = current_setting('app.current_provider_id', true)::uuid
   ```
4. The `providers` table uses split policies (`004_providers_list_policy`): `SELECT` is open (list all providers); insert/update/delete require matching tenant context.

### Database roles

| Role | Purpose | RLS |
|------|---------|-----|
| `course` | DB owner — schema migrations only (`ADMIN_DATABASE_URL`); not used at runtime | DDL only; with `FORCE RLS`, DML would need policies too |
| `course_app` | Application runtime (`DATABASE_URL`) | **enforced** (`NOBYPASSRLS`) |

`app/database/bootstrap.py` creates `course_app` and grants table privileges. Docker entrypoint and tests both use this setup so **runtime behavior matches integration tests**.

Provider creation (`POST /providers`) sets the session variable to the new provider's UUID before insert, satisfying the insert policy.

## Quick start (Docker)

```bash
docker compose up --build
```

When ready:

- Health: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs
- Postgres: `localhost:5432` — db `course_service`, owner `course` / `course`, app role `course_app` / `course`

The `api` service runs Alembic migrations as `course`, bootstraps `course_app`, then serves the API as `course_app`.

```bash
docker compose up --build -d   # detached
docker compose down            # stop
docker compose down -v         # stop and wipe database volume
```

## Local development (API on host, DB in Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
docker compose up -d db

# Migrations and app role (admin connection required)
ADMIN_DATABASE_URL=postgresql+psycopg://course:course@localhost:5432/course_service alembic upgrade head
python -m app.database.bootstrap postgresql+psycopg://course:course@localhost:5432/course_service

uvicorn app.main:app --reload   # uses DATABASE_URL=course_app from .env
```

## Tests

Docker must be running (tests start a temporary Postgres container).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest -v
```

| Test | Covers |
|------|--------|
| `test_nested_chapters` | Chapter hierarchy (`parent_id`) |
| `test_chapter_cannot_be_own_ancestor` | Cycle prevention |
| `test_provider_cannot_access_other_providers_course` | Cross-tenant isolation at course level |
| `test_provider_cannot_access_other_providers_lesson_video` | Cross-tenant isolation at lesson/video level |

## Assumptions / simplifications

- **No authentication** — any client can pass any `provider_id` in the URL; RLS enforces *data access*, not *caller identity*. A request to `/providers/{provider_b}/…` sets `app.current_provider_id` to B, so Provider B only sees B's rows regardless of which IDs appear in the path. In production, authentication would derive the tenant from a JWT or session and set that session variable server-side — the path would not be the source of truth for tenancy.
- **Provider list is open** — `GET /providers` returns all providers (by design for discovery).
- **No explicit `provider_id` in every CRUD query** — tenant isolation relies on RLS when connected as `course_app`.
- **Denormalized `provider_id` without cross-table DB checks** — each tenant-owned row carries `provider_id` for RLS policies (with FK to `providers`). There is no database constraint ensuring e.g. `chapters.provider_id` matches the parent course's `provider_id`; consistency is enforced by the application always writing the path's `provider_id` and by RLS filtering reads. A trigger or composite foreign key could harden this in production.
- **Subtitle searchability is modeled, not implemented** — `subtitle_text` is stored as PostgreSQL `TEXT` (not `VARCHAR`) so it can grow and map cleanly to full-text search later (e.g. a generated `tsvector` column and GIN index). No search endpoint or index is added; the schema choice is the deliberate hook for a future feature.
- **Video metadata has no list endpoint** — each lesson has at most one video metadata record (1:1, enforced by a unique constraint on `lesson_id`). The API exposes a singular resource at `…/lessons/{lesson_id}/video` (GET / POST / PATCH / DELETE) rather than a collection URL, since listing would always return zero or one item.
- **Video `file_id`** is an opaque string reference to external storage (not implemented).

## Deliberately out of scope

- Video upload, transcoding, streaming
- Authentication / login / user management
- Full-text search (only modeled for future use via `TEXT`)
- Frontend
- Background jobs
- Cloud deployment / infrastructure

## Project layout

```
app/           Application package (entry, settings, routes, crud, models, schemas, database)
alembic/       Schema migrations (including RLS policies)
tests/         Integration tests (Testcontainers)
scripts/       Docker entrypoint
```
