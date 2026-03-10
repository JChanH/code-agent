"""User-related request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
