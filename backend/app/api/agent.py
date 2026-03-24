"""Agent execution API router."""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.agents.design_agent_v2 import analyze_spec_and_create_tasks
from app.agents.orchestrator import run_task
from app.repositories import spec_repository, task_repository, project_repository
from app.schemas.common import ApiResponse
from app.services.guidemap_service import trigger_guidemap_generation

agent_router = APIRouter(prefix="/agent", tags=["agent"])


@agent_router.post("/run/{task_id}")
async def run_agent(task_id: str, background_tasks: BackgroundTasks):
    """Task의 코드 생성 → 리뷰 사이클을 백그라운드로 실행합니다."""
    task = await task_repository.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "confirmed":
        raise HTTPException(
            status_code=409,
            detail=f"confirmed 상태의 Task만 실행할 수 있습니다. 현재 상태: {task.status}",
        )

    background_tasks.add_task(run_task, task_id)

    return ApiResponse.ok({
        "status": "queued",
        "task_id": task_id,
        "message": "에이전트 실행이 시작되었습니다. WebSocket으로 진행상황을 확인하세요.",
    })


@agent_router.post("/specs/{spec_id}/analyze", response_model=ApiResponse[dict])
async def analyze_spec(spec_id: str, background_tasks: BackgroundTasks):
    """
    Spec을 분석하여 Task 목록으로 분해합니다.

    [subprocess]
    - Spec 상태를 'analyzing'으로 즉시 변경
    - Design Agent를 백그라운드로 실행(claude agent sdk - subprocess)
    - 진행상황은 WebSocket(/ws/{project_id})으로 실시간 전송
    """
    spec = await spec_repository.find_by_id(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")

    if spec.status == "analyzing":
        raise HTTPException(status_code=409, detail="이미 분석 중입니다.")
    
    background_tasks.add_task(analyze_spec_and_create_tasks, spec_id)

    return ApiResponse.ok(
        {"spec_id": spec_id, "status": "analyzing", "message": "분석이 시작되었습니다. WebSocket으로 진행상황을 확인하세요."}
    )


@agent_router.post("/projects/{project_id}/generate-guidemap", response_model=ApiResponse[dict])
async def generate_guidemap(project_id: str, background_tasks: BackgroundTasks):
    """
    기존 프로젝트의 guidemap을 생성(또는 재생성)합니다.

    - existing 타입 프로젝트에만 적용됩니다.
    - 진행상황은 WebSocket(/ws/{project_id})으로 실시간 전송됩니다.
    """
    project = await project_repository.find_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.project_type != "existing":
        raise HTTPException(status_code=400, detail="existing 타입 프로젝트에만 적용 가능합니다.")

    background_tasks.add_task(trigger_guidemap_generation, project_id)

    return ApiResponse.ok({
        "project_id": project_id,
        "status": "generating",
        "message": "Guidemap 생성이 시작되었습니다. WebSocket으로 진행상황을 확인하세요.",
    })
