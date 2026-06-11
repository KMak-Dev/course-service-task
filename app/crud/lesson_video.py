from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson_video import LessonVideo
from app.schemas.lesson_video import CreateLessonVideo, UpdateLessonVideo


async def create_lesson_video(
    db: AsyncSession,
    *,
    provider_id: UUID,
    lesson_id: UUID,
    data: CreateLessonVideo,
) -> LessonVideo:
    stmt = (
        insert(LessonVideo)
        .values(
            provider_id=provider_id,
            lesson_id=lesson_id,
            title=data.title,
            description=data.description,
            file_id=data.file_id,
            subtitle_text=data.subtitle_text,
        )
        .returning(LessonVideo)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_lesson_video_by_id(db: AsyncSession, video_id: UUID) -> LessonVideo | None:
    stmt = select(LessonVideo).where(LessonVideo.id == video_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_lesson_video_by_lesson_id(
    db: AsyncSession,
    *,
    lesson_id: UUID,
) -> LessonVideo | None:
    stmt = select(LessonVideo).where(LessonVideo.lesson_id == lesson_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_lesson_video(
    db: AsyncSession,
    video: LessonVideo,
    data: UpdateLessonVideo,
) -> LessonVideo:
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return video

    stmt = (
        update(LessonVideo)
        .where(LessonVideo.id == video.id)
        .values(**updates)
        .returning(LessonVideo)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def delete_lesson_video(db: AsyncSession, video: LessonVideo) -> None:
    stmt = delete(LessonVideo).where(LessonVideo.id == video.id)
    await db.execute(stmt)
