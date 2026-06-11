from fastapi import APIRouter

from routes.chapters import router as chapters_router
from routes.courses import router as courses_router
from routes.lesson_videos import router as lesson_videos_router
from routes.lessons import router as lessons_router
from routes.providers import router as providers_router

api_router = APIRouter()
api_router.include_router(providers_router)
api_router.include_router(courses_router)
api_router.include_router(chapters_router)
api_router.include_router(lessons_router)
api_router.include_router(lesson_videos_router)

__all__ = ["api_router"]
