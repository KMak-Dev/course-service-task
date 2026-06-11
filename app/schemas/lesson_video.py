from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateLessonVideo(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    file_id: str = Field(min_length=1, max_length=255)
    subtitle_text: str = ""


class UpdateLessonVideo(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    file_id: str | None = Field(default=None, min_length=1, max_length=255)
    subtitle_text: str | None = None


class LessonVideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    lesson_id: UUID
    title: str
    description: str | None
    file_id: str
    subtitle_text: str
    created_at: datetime
    updated_at: datetime
