from fastapi import APIRouter

from routes.chapters import router as chapters_router
from routes.courses import router as courses_router
from routes.providers import router as providers_router

api_router = APIRouter()
api_router.include_router(providers_router)
api_router.include_router(courses_router)
api_router.include_router(chapters_router)

__all__ = ["api_router"]
