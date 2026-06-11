import os
from collections.abc import AsyncIterator, Iterator
from urllib.parse import quote_plus, urlparse

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from app.config import settings
import database.session as db_session

APP_DB_USER = "course_app"
APP_DB_PASSWORD = "course"


def _async_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql+psycopg2://"):
        return raw_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


def _build_async_url(
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


def _setup_app_user(admin_url: str) -> str:
    parsed = urlparse(admin_url.replace("postgresql+psycopg://", "postgresql://"))
    database = parsed.path.lstrip("/")
    app_url = _build_async_url(
        host=parsed.hostname or "localhost",
        port=parsed.port,
        user=APP_DB_USER,
        password=APP_DB_PASSWORD,
        database=database,
    )

    with create_engine(admin_url).connect() as conn:
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
        conn.commit()

    return app_url


def _configure_test_database(url: str) -> None:
    os.environ["DATABASE_URL"] = url
    settings.database_url = url
    db_session.configure_database(url)


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:16") as postgres:
        admin_url = _async_database_url(postgres.get_connection_url())
        os.environ["DATABASE_URL"] = admin_url
        settings.database_url = admin_url

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", admin_url)
        command.upgrade(alembic_cfg, "head")

        app_url = _setup_app_user(admin_url)
        _configure_test_database(app_url)

        yield app_url


@pytest.fixture(autouse=True)
async def clean_db(database_url: str) -> AsyncIterator[None]:
    yield
    async with db_session.engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE providers, courses, chapters, lessons, lesson_videos "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture
async def client(database_url: str) -> AsyncIterator[AsyncClient]:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def create_provider(client: AsyncClient, name: str = "Provider A") -> str:
    response = await client.post("/providers", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]
