import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import course as course_crud
from app.database.session import get_tenant_db
from app.schemas.course import CourseResponse, CreateCourse, UpdateCourse

router = APIRouter(
    prefix="/providers/{provider_id}/courses", tags=["courses"]
)


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> list[CourseResponse]:
    courses = await course_crud.list_courses_by_provider(
        db, provider_id=provider_id
    )
    return [CourseResponse.model_validate(course) for course in courses]


@router.post(
    "", response_model=CourseResponse, status_code=status.HTTP_201_CREATED
)
async def create_course(
    provider_id: uuid.UUID,
    body: CreateCourse,
    db: AsyncSession = Depends(get_tenant_db),
) -> CourseResponse:
    course = await course_crud.create_course(
        db, provider_id=provider_id, data=body
    )
    await db.commit()
    return CourseResponse.model_validate(course)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> CourseResponse:
    course = await course_crud.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    return CourseResponse.model_validate(course)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    body: UpdateCourse,
    db: AsyncSession = Depends(get_tenant_db),
) -> CourseResponse:
    course = await course_crud.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    course = await course_crud.update_course(db, course, body)
    await db.commit()
    return CourseResponse.model_validate(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    provider_id: uuid.UUID,
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> Response:
    course = await course_crud.get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    await course_crud.delete_course(db, course)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
