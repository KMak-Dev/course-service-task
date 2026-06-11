from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateCourse(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class UpdateCourse(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
