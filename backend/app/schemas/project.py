"""Project-related request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from pydantic import model_validator
from app.schemas.enums import ProjectStack, ProjectStatus, ProjectType


class ProjectCreate(BaseModel):
    project_type: ProjectType = ProjectType.existing
    name: str
    description: Optional[str] = None
    repo_url: str
    local_repo_path: Optional[str] = None
    main_branch: str = "main"
    project_stack: ProjectStack = ProjectStack.python
    framework: Optional[str] = "fastapi"

    @model_validator(mode="after")
    def validate_local_repo_path(self) -> "ProjectCreate":
        if self.project_type == ProjectType.existing and not self.local_repo_path:
            raise ValueError("기존 프로젝트는 로컬 경로(local_repo_path)가 필요합니다.")
        return self


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    repo_url: Optional[str] = None
    local_repo_path: Optional[str] = None
    main_branch: Optional[str] = None
    project_stack: Optional[ProjectStack] = None
    framework: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    project_type: ProjectType
    repo_url: str
    local_repo_path: Optional[str]
    main_branch: str
    project_stack: ProjectStack
    framework: Optional[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
