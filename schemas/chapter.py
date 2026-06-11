from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateChapter(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None
    sort_order: int = Field(default=0, ge=0)


class UpdateChapter(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None
    sort_order: int | None = Field(default=None, ge=0)


class ChapterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    course_id: UUID
    parent_id: UUID | None
    title: str
    description: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
