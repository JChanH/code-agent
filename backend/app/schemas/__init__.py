"""Pydantic schemas for API request/response validation."""

from app.schemas.common import ApiResponse, ErrorDetail
from app.schemas.enums import (
    ProjectStack,
    ProjectStatus,
    SpecSourceType,
    SpecStatus,
    TaskComplexity,
    TaskPriority,
    TaskStatus,
    WorktreeStatus,
)
from app.schemas.git import (
    GitCommitRequest,
    GitFileStatus,
    GitLogEntry,
    GitPullRequest,
    GitStageRequest,
)
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.spec import SpecCreate, SpecResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.schemas.user import UserCreate, UserResponse
from app.schemas.worktree import WorktreeCreate, WorktreeResponse

__all__ = [
    "ApiResponse",
    "ErrorDetail",
    "ProjectStack",
    "ProjectStatus",
    "TaskStatus",
    "TaskPriority",
    "TaskComplexity",
    "SpecSourceType",
    "SpecStatus",
    "WorktreeStatus",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "UserCreate",
    "UserResponse",
    "WorktreeCreate",
    "WorktreeResponse",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "SpecCreate",
    "SpecResponse",
    "GitFileStatus",
    "GitCommitRequest",
    "GitStageRequest",
    "GitPullRequest",
    "GitLogEntry",
]
