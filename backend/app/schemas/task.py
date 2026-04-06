"""Task-related request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.enums import TaskStatus


class TaskCreate(BaseModel):
    project_id: str
    spec_id: Optional[str] = None
    title: str
    description: str
    acceptance_criteria: Optional[list[str]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[list[str]] = None
    status: Optional[TaskStatus] = None


class TaskResponse(BaseModel):
    id: str
    project_id: str
    spec_id: Optional[str]
    title: str
    description: str
    acceptance_criteria: Optional[list[str]]
    status: TaskStatus
    git_commit_hash: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
