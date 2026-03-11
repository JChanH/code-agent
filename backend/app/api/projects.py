"""Project API router."""

from fastapi import APIRouter

from app.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.common import ApiResponse
from app.services import projects_service

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.get("")
async def list_projects(
) -> ApiResponse[list[ProjectResponse]]:
    return ApiResponse.ok(await projects_service.list_projects())


@projects_router.post("")
async def create_project(
    body: ProjectCreate
) -> ApiResponse[ProjectResponse]:
    return ApiResponse.ok(await projects_service.create_project(body))


@projects_router.get("/{project_id}")
async def get_project(
    project_id: str
) -> ApiResponse[ProjectResponse]:
    return ApiResponse.ok(await projects_service.get_project(project_id))


@projects_router.patch("/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectUpdate
) -> ApiResponse[ProjectResponse]:
    return ApiResponse.ok(await projects_service.update_project(project_id, body))


@projects_router.delete("/{project_id}")
async def delete_project(
    project_id: str
) -> ApiResponse[None]:
    await projects_service.delete_project(project_id)
    return ApiResponse.ok(None)
