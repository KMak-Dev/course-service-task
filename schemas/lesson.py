from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateLesson(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(default=0, ge=0)


class UpdateLesson(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    sort_order: int | None = Field(default=None, ge=0)


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    chapter_id: UUID
    title: str
    sort_order: int
    created_at: datetime
    updated_at: datetime
