import os
from collections.abc import AsyncIterator, Iterator

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

from app.config import settings
import app.database.session as db_session
from app.database.bootstrap import setup_app_user


def _async_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql+psycopg2://"):
        return raw_url.replace(
            "postgresql+psycopg2://", "postgresql+psycopg://", 1
        )
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


def _configure_test_database(url: str) -> None:
    os.environ["DATABASE_URL"] = url
    settings.database_url = url
    db_session.configure_database(url)


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:16") as postgres:
        admin_url = _async_database_url(postgres.get_connection_url())
        os.environ["ADMIN_DATABASE_URL"] = admin_url
        settings.database_url = admin_url

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        app_url = setup_app_user(admin_url)
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
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as http_client:
        yield http_client


async def create_provider(
    client: AsyncClient, name: str = "Provider A"
) -> str:
    response = await client.post("/providers", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]
