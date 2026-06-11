import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import chapter as chapter_crud
from app.crud import course as course_crud
from app.database.session import get_tenant_db
from app.models.chapter import Chapter
from app.schemas.chapter import ChapterResponse, CreateChapter, UpdateChapter

router = APIRouter(
    prefix="/providers/{provider_id}/courses/{course_id}/chapters",
    tags=["chapters"],
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


async def _validate_parent(
    db: AsyncSession,
    *,
    course_id: uuid.UUID,
    parent_id: uuid.UUID,
) -> Chapter:
    parent = await chapter_crud.get_chapter_by_id_and_course(
        db,
        chapter_id=parent_id,
        course_id=course_id,
    )
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent chapter not found")
    return parent


@router.get("", response_model=list[ChapterResponse])
async def list_chapters(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
    parent_id: uuid.UUID | None = Query(default=None),
    roots_only: bool = Query(default=False),
) -> list[ChapterResponse]:
    if roots_only and parent_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use either roots_only or parent_id, not both",
        )

    await _get_course_or_404(db, course_id)

    if parent_id is not None:
        await _validate_parent(db, course_id=course_id, parent_id=parent_id)

    chapters = await chapter_crud.list_chapters_by_course(
        db,
        course_id=course_id,
        parent_id=parent_id,
        roots_only=roots_only,
    )
    return [ChapterResponse.model_validate(chapter) for chapter in chapters]


@router.post("", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_chapter(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    body: CreateChapter,
    db: AsyncSession = Depends(get_tenant_db),
) -> ChapterResponse:
    await _get_course_or_404(db, course_id)

    if body.parent_id is not None:
        await _validate_parent(db, course_id=course_id, parent_id=body.parent_id)

    chapter = await chapter_crud.create_chapter(
        db,
        provider_id=provider_id,
        course_id=course_id,
        data=body,
    )
    await db.commit()
    return ChapterResponse.model_validate(chapter)


@router.get("/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> ChapterResponse:
    await _get_course_or_404(db, course_id)
    chapter = await _get_chapter_or_404(db, course_id=course_id, chapter_id=chapter_id)
    return ChapterResponse.model_validate(chapter)


@router.patch("/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    body: UpdateChapter,
    db: AsyncSession = Depends(get_tenant_db),
) -> ChapterResponse:
    await _get_course_or_404(db, course_id)
    chapter = await _get_chapter_or_404(db, course_id=course_id, chapter_id=chapter_id)

    if "parent_id" in body.model_fields_set:
        new_parent_id = body.parent_id
        if new_parent_id is not None:
            await _validate_parent(db, course_id=course_id, parent_id=new_parent_id)
            if await chapter_crud.would_create_cycle(
                db,
                chapter_id=chapter_id,
                new_parent_id=new_parent_id,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Chapter cannot be its own ancestor",
                )

    chapter = await chapter_crud.update_chapter(db, chapter, body)
    await db.commit()
    return ChapterResponse.model_validate(chapter)


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    chapter_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> Response:
    await _get_course_or_404(db, course_id)
    chapter = await _get_chapter_or_404(db, course_id=course_id, chapter_id=chapter_id)

    await chapter_crud.delete_chapter(db, chapter)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
