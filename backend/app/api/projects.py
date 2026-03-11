"""Project API router."""

from fastapi import APIRouter

from app.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.common import ApiResponse
from app.services import projects_service

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.get("", response_model=ApiResponse[list[ProjectResponse]])
async def list_projects():
    return ApiResponse.ok(await projects_service.list_projects())


@projects_router.post("", response_model=ApiResponse[ProjectResponse], status_code=201)
async def create_project(body: ProjectCreate):
    return ApiResponse.ok(await projects_service.create_project(body))


@projects_router.get("/{project_id}", response_model=ApiResponse[ProjectResponse])
async def get_project(project_id: str):
    return ApiResponse.ok(await projects_service.get_project(project_id))


@projects_router.patch("/{project_id}", response_model=ApiResponse[ProjectResponse])
async def update_project(project_id: str, body: ProjectUpdate):
    return ApiResponse.ok(await projects_service.update_project(project_id, body))


@projects_router.delete("/{project_id}", response_model=ApiResponse[None])
async def delete_project(project_id: str):
    await projects_service.delete_project(project_id)
    return ApiResponse.ok(None)
