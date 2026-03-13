"""Project API router."""

from fastapi import APIRouter, BackgroundTasks

from app.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.common import ApiResponse
from app.services import projects_service
from app.services.guidemap_service import trigger_guidemap_generation

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.get("")
async def list_projects(
) -> ApiResponse[list[ProjectResponse]]:
    """
    모든 프로젝트 목록을 조회합니다.

    Args:
        없음

    Returns:
        ApiResponse[list[ProjectResponse]]: 프로젝트 목록을 담은 공통 응답 객체
    """
    return ApiResponse.ok(await projects_service.list_projects())


@projects_router.post("")
async def create_project(
    body: ProjectCreate,
    background_tasks: BackgroundTasks,
) -> ApiResponse[ProjectResponse]:
    """
    새로운 프로젝트를 생성합니다.

    Args:
        body (ProjectCreate): 생성할 프로젝트 정보 (이름, 설명 등)

    Returns:
        ApiResponse[ProjectResponse]: 생성된 프로젝트 정보를 담은 공통 응답 객체
    """
    project = await projects_service.create_project(body)
    if body.project_type == "existing" and body.local_repo_path:
        background_tasks.add_task(trigger_guidemap_generation, project.id)
    return ApiResponse.ok(project)


@projects_router.get("/{project_id}")
async def get_project(
    project_id: str
) -> ApiResponse[ProjectResponse]:
    """
    특정 프로젝트의 상세 정보를 조회합니다.

    Args:
        project_id (str): 조회할 프로젝트의 고유 ID

    Returns:
        ApiResponse[ProjectResponse]: 조회된 프로젝트 정보를 담은 공통 응답 객체
    """
    return ApiResponse.ok(await projects_service.get_project(project_id))


@projects_router.patch("/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectUpdate
) -> ApiResponse[ProjectResponse]:
    """
    특정 프로젝트의 정보를 수정합니다.

    Args:
        project_id (str): 수정할 프로젝트의 고유 ID
        body (ProjectUpdate): 수정할 프로젝트 정보 (이름, 설명 등)

    Returns:
        ApiResponse[ProjectResponse]: 수정된 프로젝트 정보를 담은 공통 응답 객체
    """
    return ApiResponse.ok(await projects_service.update_project(project_id, body))


@projects_router.delete("/{project_id}")
async def delete_project(
    project_id: str
) -> ApiResponse[None]:
    """
    특정 프로젝트를 삭제합니다.

    Args:
        project_id (str): 삭제할 프로젝트의 고유 ID

    Returns:
        ApiResponse[None]: 성공 여부를 담은 공통 응답 객체 (데이터 없음)
    """
    await projects_service.delete_project(project_id)
    return ApiResponse.ok(None)
