"""Task-related request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.enums import TaskComplexity, TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    project_id: str
    spec_id: Optional[str] = None
    assigned_user_id: Optional[str] = None
    title: str
    description: str
    acceptance_criteria: Optional[list[str]] = None
    priority: TaskPriority = TaskPriority.medium
    complexity: TaskComplexity = TaskComplexity.medium
    auto_approve: bool = False
    auto_approve_config: Optional[dict] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_user_id: Optional[str] = None
    acceptance_criteria: Optional[list[str]] = None
    priority: Optional[TaskPriority] = None
    complexity: Optional[TaskComplexity] = None
    status: Optional[TaskStatus] = None
    sort_order: Optional[int] = None
    auto_approve: Optional[bool] = None
    auto_approve_config: Optional[dict] = None


class TaskResponse(BaseModel):
    id: str
    project_id: str
    spec_id: Optional[str]
    assigned_user_id: Optional[str]
    title: str
    description: str
    acceptance_criteria: Optional[list[str]]
    priority: TaskPriority
    complexity: TaskComplexity
    status: TaskStatus
    sort_order: int
    auto_approve: bool
    auto_approve_config: Optional[dict]
    git_commit_hash: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
