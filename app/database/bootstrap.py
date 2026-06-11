"""Create the application DB role and grant privileges (RLS-enforced runtime user)."""

from __future__ import annotations

import os
import sys
from urllib.parse import quote_plus, urlparse

from sqlalchemy import create_engine, text

APP_DB_USER = "course_app"
APP_DB_PASSWORD = "course"


def normalize_sync_url(url: str) -> str:
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def build_async_url(
    *,
    host: str,
    port: int | None,
    user: str,
    password: str,
    database: str,
) -> str:
    auth = f"{quote_plus(user)}:{quote_plus(password)}"
    netloc = f"{auth}@{host}"
    if port:
        netloc += f":{port}"
    return f"postgresql+psycopg://{netloc}/{database}"


def setup_app_user(admin_url: str) -> str:
    sync_admin_url = normalize_sync_url(admin_url)
    parsed = urlparse(sync_admin_url.replace("postgresql+psycopg://", "postgresql://", 1))
    database = parsed.path.lstrip("/")
    admin_user = parsed.username or "postgres"
    app_url = build_async_url(
        host=parsed.hostname or "localhost",
        port=parsed.port,
        user=APP_DB_USER,
        password=APP_DB_PASSWORD,
        database=database,
    )

    with create_engine(sync_admin_url).connect() as conn:
        conn.execute(
            text(
                f"""
                DO $$ BEGIN
                  CREATE ROLE {APP_DB_USER} LOGIN PASSWORD '{APP_DB_PASSWORD}'
                    NOSUPERUSER NOBYPASSRLS;
                EXCEPTION WHEN duplicate_object THEN NULL;
                END $$;
                """
            )
        )
        conn.execute(text(f'GRANT CONNECT ON DATABASE "{database}" TO {APP_DB_USER}'))
        conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {APP_DB_USER}"))
        conn.execute(
            text(
                f"GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE "
                f"ON ALL TABLES IN SCHEMA public TO {APP_DB_USER}"
            )
        )
        conn.execute(
            text(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {APP_DB_USER}")
        )
        conn.execute(
            text(
                f"""
                ALTER DEFAULT PRIVILEGES FOR ROLE {admin_user} IN SCHEMA public
                  GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON TABLES TO {APP_DB_USER}
                """
            )
        )
        conn.execute(
            text(
                f"""
                ALTER DEFAULT PRIVILEGES FOR ROLE {admin_user} IN SCHEMA public
                  GRANT USAGE, SELECT ON SEQUENCES TO {APP_DB_USER}
                """
            )
        )
        conn.commit()

    return app_url


def main() -> None:
    admin_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ADMIN_DATABASE_URL")
    if not admin_url:
        raise SystemExit("Usage: python -m app.database.bootstrap <admin_database_url>")

    setup_app_user(admin_url)


if __name__ == "__main__":
    main()
