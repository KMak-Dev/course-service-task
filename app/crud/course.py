from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.schemas.course import CreateCourse, UpdateCourse


async def create_course(
    db: AsyncSession,
    *,
    provider_id: UUID,
    data: CreateCourse,
) -> Course:
    stmt = (
        insert(Course)
        .values(
            provider_id=provider_id,
            title=data.title,
            description=data.description,
        )
        .returning(Course)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_course_by_id(
    db: AsyncSession, course_id: UUID
) -> Course | None:
    stmt = select(Course).where(Course.id == course_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_courses_by_provider(
    db: AsyncSession, *, provider_id: UUID
) -> list[Course]:
    stmt = (
        select(Course)
        .where(Course.provider_id == provider_id)
        .order_by(Course.title)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_course(
    db: AsyncSession, course: Course, data: UpdateCourse
) -> Course:
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return course

    stmt = (
        update(Course)
        .where(Course.id == course.id)
        .values(**updates)
        .returning(Course)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def delete_course(db: AsyncSession, course: Course) -> None:
    stmt = delete(Course).where(Course.id == course.id)
    await db.execute(stmt)
