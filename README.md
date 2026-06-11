# Course Service

> [English README](README_eng.md)

Backend-Grundlage für eine **Multi-Tenant-Online-Kursplattform**: Anbieter verwalten eigene Kurse, verschachtelte Kapitel, Lektionen und Video-Metadaten pro Lektion. Umgesetzt mit **FastAPI**, **PostgreSQL 16** und **Row Level Security (RLS)**.

## Technologieauswahl

| Wahl | Begründung |
|------|------------|
| **Python + FastAPI** | Async-first HTTP-API mit automatischer OpenAPI-Dokumentation; Pydantic liefert Request-/Response-Validierung out of the box. |
| **SQLAlchemy 2.0 (async)** | Ausgereiftes ORM mit explizitem Statement-basiertem CRUD; passt zu einer Schichtenarchitektur ohne viel Magie. |
| **PostgreSQL 16** | Native RLS für mandantenseitige Isolation auf Datenbankebene; `TEXT`-Spalten ermöglichen spätere Volltextsuche auf Untertiteln. |
| **Alembic** | Versionierte Schema-Migrationen inklusive RLS-Policies. |
| **Testcontainers** | Integrationstests gegen echtes PostgreSQL mit demselben RLS-Verhalten wie in Docker/lokalem Betrieb. |

## Architektur

```
app/routes/    → HTTP-Handler (Pydantic in/out, Depends für DB-Sessions)
app/crud/      → Datenbankzugriff (select / insert / update / delete)
app/models/    → SQLAlchemy-ORM-Modelle
app/schemas/   → Pydantic Request-/Response-Modelle
app/database/  → Engine, Session-Dependencies, Bootstrap der App-Rolle
```

**Request-Flow:** Route → CRUD → PostgreSQL. Mandantenbezogene Routen injizieren eine DB-Session, die `app.current_provider_id` setzt; RLS-Policies filtern Zeilen automatisch.

**API-Struktur:** verschachtelte REST-Ressourcen unter `/providers/{provider_id}/…`, sodass die Mandantenzuordnung in jeder URL explizit ist. Keine Authentifizierungsschicht — `provider_id` im Pfad steht stellvertretend für ein zukünftiges Auth-Token.

## Domänenmodell

| Entität | Beziehungen | Anmerkungen |
|---------|-------------|-------------|
| **Provider** | besitzt viele Kurse | Mandanten-Wurzel |
| **Course** | gehört zu einem Provider; hat viele Kapitel | `title`, `description` |
| **Chapter** | gehört zu einem Kurs; **verschachtelbar** via `parent_id` | Hierarchie + `sort_order`; Zyklusverhinderung bei Updates |
| **Lesson** | gehört zu einem Kapitel | `title`, `sort_order` |
| **LessonVideo** | eines pro Lektion (1:1) | nur Metadaten — kein Upload/Streaming |

**Video-Metadaten-Felder:** `title`, `description`, `file_id`, `subtitle_text`.

`subtitle_text` wird als PostgreSQL-`TEXT` (nicht `VARCHAR`) gespeichert — der übliche Ausgangspunkt für ein später durchsuchbares Feld, z. B. eine generierte `tsvector`-Spalte und ein GIN-Index für Volltextsuche. Die Suche selbst ist bewusst nicht implementiert.

## API-Übersicht

| Ressource | Präfix | CRUD |
|-----------|--------|------|
| Providers | `/providers` | Liste + Erstellen (offen); Abrufen/Aktualisieren/Löschen (mandantengebunden) |
| Courses | `/providers/{provider_id}/courses` | vollständiges CRUD |
| Chapters | `…/courses/{course_id}/chapters` | vollständiges CRUD; Query-Parameter `parent_id` / `roots_only` |
| Lessons | `…/chapters/{chapter_id}/lessons` | vollständiges CRUD |
| Video-Metadaten | `…/lessons/{lesson_id}/video` | GET / POST / PATCH / DELETE (Singular-Ressource) |

Interaktive Dokumentation: http://localhost:8000/docs

## Row Level Security (RLS)

### Warum RLS

In einem Multi-Tenant-System können Anwendungsfehler oder vergessene `WHERE`-Klauseln Daten zwischen Mandanten durchsickern lassen. RLS erzwingt die Isolation **in der Datenbank** für jede Abfrage der Anwendungsrolle — einschließlich Ad-hoc-Zugriff und zukünftiger Codepfade.

### Funktionsweise

1. Jede mandantengebundene Tabelle hat eine `provider_id`-Spalte.
2. Vor mandantenbezogenen Requests setzt die App eine Session-Variable:
   ```sql
   SELECT set_config('app.current_provider_id', '<uuid>', true);
   ```
3. Die Alembic-Migration `002_enable_rls` aktiviert **FORCE ROW LEVEL SECURITY** auf Mandantentabellen mit Policies wie:
   ```sql
   provider_id = current_setting('app.current_provider_id', true)::uuid
   ```
4. Die Tabelle `providers` nutzt getrennte Policies (`004_providers_list_policy`): `SELECT` ist offen (alle Provider auflisten); Insert/Update/Delete erfordern passenden Mandantenkontext.

### Datenbankrollen

| Rolle | Zweck | RLS |
|-------|-------|-----|
| `course` | DB-Owner — nur Migrationen (`ADMIN_DATABASE_URL`) | umgeht RLS (Superuser) |
| `course_app` | Anwendungslaufzeit (`DATABASE_URL`) | **erzwungen** (`NOBYPASSRLS`) |

`app/database/bootstrap.py` legt `course_app` an und vergibt Tabellenrechte. Docker-Entrypoint und Tests nutzen dasselbe Setup, sodass **Laufzeitverhalten und Integrationstests übereinstimmen**.

Beim Anlegen eines Providers (`POST /providers`) wird die Session-Variable vor dem Insert auf die UUID des neuen Providers gesetzt, um die Insert-Policy zu erfüllen.

## Schnellstart (Docker)

```bash
docker compose up --build
```

Wenn bereit:

- Health: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs
- Postgres: `localhost:5432` — DB `course_service`, Owner `course` / `course`, App-Rolle `course_app` / `course`

Der `api`-Service führt Alembic-Migrationen als `course` aus, bootstrapped `course_app` und startet die API dann als `course_app`.

```bash
docker compose up --build -d   # im Hintergrund
docker compose down            # stoppen
docker compose down -v         # stoppen und Datenbank-Volume löschen
```

## Manueller API-Test (curl)

```bash
curl -s -X POST http://localhost:8000/providers \
  -H "Content-Type: application/json" \
  -d '{"name": "Provider A"}' | jq
```

```bash
export PROVIDER_ID="<id-hier-einfügen>"

curl -s http://localhost:8000/providers | jq
curl -s http://localhost:8000/providers/$PROVIDER_ID | jq

curl -s -X POST "http://localhost:8000/providers/$PROVIDER_ID/courses" \
  -H "Content-Type: application/json" \
  -d '{"title": "Mein Kurs"}' | jq
```

## Lokale Entwicklung (API auf dem Host, DB in Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
docker compose up -d db

# Migrationen und App-Rolle (Admin-Verbindung erforderlich)
ADMIN_DATABASE_URL=postgresql+psycopg://course:course@localhost:5432/course_service alembic upgrade head
python -m app.database.bootstrap postgresql+psycopg://course:course@localhost:5432/course_service

uvicorn app.main:app --reload   # nutzt DATABASE_URL=course_app aus .env
```

## Tests

Integrationstests nutzen [Testcontainers](https://testcontainers.com/), um eine temporäre PostgreSQL-16-Instanz zu starten, Migrationen als Admin auszuführen, `course_app` zu bootstrappen und die API in-process via `httpx` zu testen (kein separater Server). **Docker muss laufen.**

```bash
pip install -e ".[dev]"
pytest -v
```

| Test | Abdeckung |
|------|-----------|
| `test_nested_chapters` | Kapitelhierarchie (`parent_id`) |
| `test_chapter_cannot_be_own_ancestor` | Zyklusverhinderung |
| `test_provider_cannot_access_other_providers_course` | Mandantenisolation auf Kursebene |
| `test_provider_cannot_access_other_providers_lesson_video` | Mandantenisolation auf Lektions-/Videoebene |

Nach jedem Test werden Mandantentabellen geleert, um Isolation innerhalb der Session sicherzustellen.

## Abdeckung der Aufgabenanforderungen

| Anforderung | Umsetzung |
|-------------|-----------|
| Multi-Tenancy via `provider_id` | Spalte auf allen Mandantentabellen + verschachtelte API-Pfade |
| Trennung auf DB-Ebene | PostgreSQL RLS mit `FORCE`, Laufzeitrolle `course_app` |
| Domänenmodell (Kurs, Kapitel, Lektion, Video) | `app/models/` + Alembic-Migrationen |
| Verschachtelte Kapitel | `parent_id` Self-FK, Zyklusprüfung im CRUD |
| Video-Metadaten-Felder | `LessonVideo`-Modell (`title`, `description`, `file_id`, `subtitle_text`) |
| CRUD-API | `app/routes/` für alle Ressourcen |
| Eingabevalidierung / Fehlerbehandlung | Pydantic-Schemas; 404, 400, 409, 422 |
| 2–3 Tests | 4 Integrationstests in `tests/` |
| README | diese Datei (engl.: [README_eng.md](README_eng.md)) |

## Annahmen / Vereinfachungen

- **Keine Authentifizierung** — jeder Client kann beliebige `provider_id`-Werte in der URL übergeben; RLS erzwingt *Datenzugriff*, nicht die *Identität des Aufrufers*. Ein Request an `/providers/{provider_b}/…` setzt `app.current_provider_id` auf B, sodass Provider B nur die Zeilen von B sieht — unabhängig davon, welche IDs im Pfad stehen. In Produktion würde die Authentifizierung den Mandanten aus einem JWT oder einer Session ableiten und diese Session-Variable serverseitig setzen — der Pfad wäre nicht die Quelle der Wahrheit für die Mandantenzuordnung.
- **Provider-Liste ist offen** — `GET /providers` liefert alle Provider (bewusst für Auffindbarkeit).
- **Kein explizites `provider_id` in jeder CRUD-Abfrage** — Mandantenisolation verlässt sich auf RLS bei Verbindung als `course_app`.
- **Denormalisiertes `provider_id` ohne tabellenübergreifende DB-Prüfungen** — jede mandantengebundene Zeile trägt `provider_id` für RLS-Policies. Es gibt keine Datenbank-Constraint, die z. B. sicherstellt, dass `chapters.provider_id` zur `provider_id` des übergeordneten Kurses passt; Konsistenz wird durch die Anwendung erzwungen (sie schreibt immer die `provider_id` aus dem Pfad) und durch RLS beim Lesen. Ein Trigger oder zusammengesetzter Fremdschlüssel könnte das in Produktion härten.
- **Untertitel-Durchsuchbarkeit ist modelliert, nicht implementiert** — `subtitle_text` wird als PostgreSQL-`TEXT` (nicht `VARCHAR`) gespeichert, damit das Feld wachsen kann und sich später sauber auf Volltextsuche abbilden lässt (z. B. generierte `tsvector`-Spalte und GIN-Index). Kein Such-Endpunkt oder Index ist vorhanden; die Schema-Wahl ist der bewusste Ankerpunkt für ein zukünftiges Feature.
- **Video-Metadaten haben keinen List-Endpunkt** — jede Lektion hat höchstens einen Video-Metadaten-Datensatz (1:1, erzwungen durch Unique-Constraint auf `lesson_id`). Die API exponiert eine Singular-Ressource unter `…/lessons/{lesson_id}/video` (GET / POST / PATCH / DELETE) statt einer Collection-URL, da eine Liste immer null oder ein Element zurückgeben würde.
- **Video-`file_id`** ist eine undurchsichtige String-Referenz auf externen Speicher (nicht implementiert).

## Bewusst nicht im Scope

- Video-Upload, Transcoding, Streaming
- Authentifizierung / Login / Benutzerverwaltung
- Volltextsuche (nur für die Zukunft via `TEXT` modelliert)
- Frontend
- Hintergrundjobs
- Cloud-Deployment / Infrastruktur

## Projektstruktur

```
app/           Anwendungspaket (Entry, Settings, Routes, CRUD, Models, Schemas, Database)
alembic/       Schema-Migrationen (inkl. RLS-Policies)
tests/         Integrationstests (Testcontainers)
scripts/       Docker-Entrypoint
```
