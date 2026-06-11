import uuid

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import set_provider_context
from app.models.provider import Provider
from app.schemas.provider import CreateProvider, UpdateProvider


async def create_provider(db: AsyncSession, data: CreateProvider) -> Provider:
    provider_id = uuid.uuid4()
    await set_provider_context(db, provider_id)

    stmt = (
        insert(Provider)
        .values(id=provider_id, name=data.name)
        .returning(Provider)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def list_providers(db: AsyncSession) -> list[Provider]:
    stmt = select(Provider).order_by(Provider.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_provider_by_id(db: AsyncSession, provider_id: uuid.UUID) -> Provider | None:
    stmt = select(Provider).where(Provider.id == provider_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_provider(
    db: AsyncSession,
    provider: Provider,
    data: UpdateProvider,
) -> Provider:
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return provider

    stmt = (
        update(Provider)
        .where(Provider.id == provider.id)
        .values(**updates)
        .returning(Provider)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def delete_provider(db: AsyncSession, provider: Provider) -> None:
    stmt = delete(Provider).where(Provider.id == provider.id)
    await db.execute(stmt)
