import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def set_provider_context(session: AsyncSession, provider_id: uuid.UUID) -> None:
    await session.execute(
        text("SELECT set_config('app.current_provider_id', :provider_id, true)"),
        {"provider_id": str(provider_id)},
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_tenant_db(provider_id: uuid.UUID) -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        await set_provider_context(session, provider_id)
        yield session
