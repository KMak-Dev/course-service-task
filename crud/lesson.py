from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.lesson import Lesson
from schemas.lesson import CreateLesson, UpdateLesson


async def create_lesson(
    db: AsyncSession,
    *,
    provider_id: UUID,
    chapter_id: UUID,
    data: CreateLesson,
) -> Lesson:
    stmt = (
        insert(Lesson)
        .values(
            provider_id=provider_id,
            chapter_id=chapter_id,
            title=data.title,
            sort_order=data.sort_order,
        )
        .returning(Lesson)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_lesson_by_id(db: AsyncSession, lesson_id: UUID) -> Lesson | None:
    stmt = select(Lesson).where(Lesson.id == lesson_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_lessons_by_chapter(db: AsyncSession, *, chapter_id: UUID) -> list[Lesson]:
    stmt = (
        select(Lesson)
        .where(Lesson.chapter_id == chapter_id)
        .order_by(Lesson.sort_order, Lesson.title)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_lesson(db: AsyncSession, lesson: Lesson, data: UpdateLesson) -> Lesson:
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return lesson

    stmt = (
        update(Lesson)
        .where(Lesson.id == lesson.id)
        .values(**updates)
        .returning(Lesson)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def delete_lesson(db: AsyncSession, lesson: Lesson) -> None:
    stmt = delete(Lesson).where(Lesson.id == lesson.id)
    await db.execute(stmt)
