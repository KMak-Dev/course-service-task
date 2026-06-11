import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import chapter as chapter_crud
from crud import course as course_crud
from crud import lesson as lesson_crud
from database.session import get_tenant_db
from models.chapter import Chapter
from models.lesson import Lesson
from schemas.lesson import CreateLesson, LessonResponse, UpdateLesson

router = APIRouter(
    prefix="/providers/{provider_id}/courses/{course_id}/chapters/{chapter_id}/lessons",
    tags=["lessons"],
)


async def _get_course_or_404(db: AsyncSession, course_id: uuid.UUID) -> None:
    course = await course_crud.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


@router.get("", response_model=list[LessonResponse])
async def list_lessons(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> list[LessonResponse]:
    await _get_course_or_404(db, course_id)
    await _get_chapter_or_404(db, course_id=course_id, chapter_id=chapter_id)

    lessons = await lesson_crud.list_lessons_by_chapter(db, chapter_id=chapter_id)
    return [LessonResponse.model_validate(lesson) for lesson in lessons]


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    body: CreateLesson,
    db: AsyncSession = Depends(get_tenant_db),
) -> LessonResponse:
    await _get_course_or_404(db, course_id)
    await _get_chapter_or_404(db, course_id=course_id, chapter_id=chapter_id)

    lesson = await lesson_crud.create_lesson(
        db,
        provider_id=provider_id,
        chapter_id=chapter_id,
        data=body,
    )
    await db.commit()
    return LessonResponse.model_validate(lesson)


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> LessonResponse:
    await _get_course_or_404(db, course_id)
    await _get_chapter_or_404(db, course_id=course_id, chapter_id=chapter_id)
    lesson = await _get_lesson_or_404(db, chapter_id=chapter_id, lesson_id=lesson_id)
    return LessonResponse.model_validate(lesson)


@router.patch("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    lesson_id: uuid.UUID,
    body: UpdateLesson,
    db: AsyncSession = Depends(get_tenant_db),
) -> LessonResponse:
    await _get_course_or_404(db, course_id)
    await _get_chapter_or_404(db, course_id=course_id, chapter_id=chapter_id)
    lesson = await _get_lesson_or_404(db, chapter_id=chapter_id, lesson_id=lesson_id)

    lesson = await lesson_crud.update_lesson(db, lesson, body)
    await db.commit()
    return LessonResponse.model_validate(lesson)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> Response:
    await _get_course_or_404(db, course_id)
    await _get_chapter_or_404(db, course_id=course_id, chapter_id=chapter_id)
    lesson = await _get_lesson_or_404(db, chapter_id=chapter_id, lesson_id=lesson_id)

    await lesson_crud.delete_lesson(db, lesson)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
