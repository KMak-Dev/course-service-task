from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateProvider(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class UpdateProvider(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
