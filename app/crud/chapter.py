from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter import Chapter
from app.schemas.chapter import CreateChapter, UpdateChapter


async def create_chapter(
    db: AsyncSession,
    *,
    provider_id: UUID,
    course_id: UUID,
    data: CreateChapter,
) -> Chapter:
    stmt = (
        insert(Chapter)
        .values(
            provider_id=provider_id,
            course_id=course_id,
            parent_id=data.parent_id,
            title=data.title,
            description=data.description,
            sort_order=data.sort_order,
        )
        .returning(Chapter)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_chapter_by_id(db: AsyncSession, chapter_id: UUID) -> Chapter | None:
    stmt = select(Chapter).where(Chapter.id == chapter_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_chapter_by_id_and_course(
    db: AsyncSession,
    *,
    chapter_id: UUID,
    course_id: UUID,
) -> Chapter | None:
    stmt = select(Chapter).where(Chapter.id == chapter_id, Chapter.course_id == course_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def would_create_cycle(
    db: AsyncSession,
    *,
    chapter_id: UUID,
    new_parent_id: UUID,
) -> bool:
    if chapter_id == new_parent_id:
        return True

    current_id: UUID | None = new_parent_id
    while current_id is not None:
        if current_id == chapter_id:
            return True
        parent = await get_chapter_by_id(db, current_id)
        if parent is None:
            return False
        current_id = parent.parent_id
    return False


async def list_chapters_by_course(
    db: AsyncSession,
    *,
    course_id: UUID,
    parent_id: UUID | None = None,
    roots_only: bool = False,
) -> list[Chapter]:
    stmt = select(Chapter).where(Chapter.course_id == course_id)
    if roots_only:
        stmt = stmt.where(Chapter.parent_id.is_(None))
    elif parent_id is not None:
        stmt = stmt.where(Chapter.parent_id == parent_id)
    stmt = stmt.order_by(Chapter.sort_order, Chapter.title)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_chapter(db: AsyncSession, chapter: Chapter, data: UpdateChapter) -> Chapter:
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return chapter

    stmt = (
        update(Chapter)
        .where(Chapter.id == chapter.id)
        .values(**updates)
        .returning(Chapter)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def delete_chapter(db: AsyncSession, chapter: Chapter) -> None:
    stmt = delete(Chapter).where(Chapter.id == chapter.id)
    await db.execute(stmt)
