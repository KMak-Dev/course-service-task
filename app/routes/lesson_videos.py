import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import chapter as chapter_crud
from app.crud import course as course_crud
from app.crud import lesson as lesson_crud
from app.crud import lesson_video as lesson_video_crud
from app.database.session import get_tenant_db
from app.models.chapter import Chapter
from app.models.lesson import Lesson
from app.models.lesson_video import LessonVideo
from app.schemas.lesson_video import (
    CreateLessonVideo,
    LessonVideoResponse,
    UpdateLessonVideo,
)

router = APIRouter(
    prefix="/providers/{provider_id}/courses/{course_id}/chapters/{chapter_id}/lessons/{lesson_id}/video",
    tags=["lesson-videos"],
)


async def _get_course_or_404(
    db: AsyncSession, course_id: uuid.UUID
) -> None:
    course = await course_crud.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )


async def _get_chapter_or_404(
    db: AsyncSession,
    *,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
) -> Chapter:
    chapter = await chapter_crud.get_chapter_by_id_and_course(
        db,
        chapter_id=chapter_id,
        course_id=course_id,
    )
    if chapter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )
    return chapter


async def _get_lesson_or_404(
    db: AsyncSession,
    *,
    chapter_id: uuid.UUID,
    lesson_id: uuid.UUID,
) -> Lesson:
    lesson = await lesson_crud.get_lesson_by_id_and_chapter(
        db,
        lesson_id=lesson_id,
        chapter_id=chapter_id,
    )
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    return lesson


async def _get_video_or_404(
    db: AsyncSession, *, lesson_id: uuid.UUID
) -> LessonVideo:
    video = await lesson_video_crud.get_lesson_video_by_lesson_id(
        db, lesson_id=lesson_id
    )
    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video metadata not found",
        )
    return video


@router.get("", response_model=LessonVideoResponse)
async def get_lesson_video(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> LessonVideoResponse:
    await _get_course_or_404(db, course_id)
    await _get_chapter_or_404(
        db, course_id=course_id, chapter_id=chapter_id
    )
    await _get_lesson_or_404(
        db, chapter_id=chapter_id, lesson_id=lesson_id
    )
    video = await _get_video_or_404(db, lesson_id=lesson_id)
    return LessonVideoResponse.model_validate(video)


@router.post(
    "",
    response_model=LessonVideoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson_video(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    lesson_id: uuid.UUID,
    body: CreateLessonVideo,
    db: AsyncSession = Depends(get_tenant_db),
) -> LessonVideoResponse:
    await _get_course_or_404(db, course_id)
    await _get_chapter_or_404(
        db, course_id=course_id, chapter_id=chapter_id
    )
    await _get_lesson_or_404(
        db, chapter_id=chapter_id, lesson_id=lesson_id
    )

    existing = await lesson_video_crud.get_lesson_video_by_lesson_id(
        db, lesson_id=lesson_id
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lesson already has video metadata",
        )

    video = await lesson_video_crud.create_lesson_video(
        db,
        provider_id=provider_id,
        lesson_id=lesson_id,
        data=body,
    )
    await db.commit()
    return LessonVideoResponse.model_validate(video)


@router.patch("", response_model=LessonVideoResponse)
async def update_lesson_video(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    lesson_id: uuid.UUID,
    body: UpdateLessonVideo,
    db: AsyncSession = Depends(get_tenant_db),
) -> LessonVideoResponse:
    await _get_course_or_404(db, course_id)
    await _get_chapter_or_404(
        db, course_id=course_id, chapter_id=chapter_id
    )
    await _get_lesson_or_404(
        db, chapter_id=chapter_id, lesson_id=lesson_id
    )
    video = await _get_video_or_404(db, lesson_id=lesson_id)

    video = await lesson_video_crud.update_lesson_video(db, video, body)
    await db.commit()
    return LessonVideoResponse.model_validate(video)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson_video(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> Response:
    await _get_course_or_404(db, course_id)
    await _get_chapter_or_404(
        db, course_id=course_id, chapter_id=chapter_id
    )
    await _get_lesson_or_404(
        db, chapter_id=chapter_id, lesson_id=lesson_id
    )
    video = await _get_video_or_404(db, lesson_id=lesson_id)

    await lesson_video_crud.delete_lesson_video(db, video)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
