"""Spec-related request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.enums import SpecSourceType, SpecStatus


class SpecCreate(BaseModel):
    project_id: str
    source_type: SpecSourceType
    raw_content: Optional[str] = None


class SpecResponse(BaseModel):
    id: str
    project_id: str
    source_type: SpecSourceType
    source_path: Optional[str]
    raw_content: Optional[str]
    status: SpecStatus
    created_at: datetime

    class Config:
        from_attributes = True
