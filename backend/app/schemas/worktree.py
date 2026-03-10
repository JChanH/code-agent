"""Worktree-related request/response schemas."""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.enums import WorktreeStatus


class WorktreeCreate(BaseModel):
    user_id: str
    project_id: str
    worktree_path: str
    branch_name: str


class WorktreeResponse(BaseModel):
    id: str
    user_id: str
    project_id: str
    worktree_path: str
    branch_name: str
    status: WorktreeStatus
    created_at: datetime

    class Config:
        from_attributes = True
