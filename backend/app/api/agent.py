"""Agent execution API router."""

import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.agents.design_agent import analyze_spec_and_create_tasks
from app.repositories import spec_repository
from app.schemas.common import ApiResponse

agent_router = APIRouter(prefix="/agent", tags=["agent"])


@agent_router.post("/run/{task_id}")
async def run_agent(task_id: str):
    """Phase 3에서 구현 예정 — 개발 에이전트 실행."""
    return {
        "status": "queued",
        "task_id": task_id,
        "message": "Agent execution will be implemented in Phase 3",
    }


@agent_router.post("/specs/{spec_id}/analyze", response_model=ApiResponse[dict])
async def analyze_spec(spec_id: str, background_tasks: BackgroundTasks):
    """
    Spec을 비동기로 분석하여 Task 목록으로 분해합니다.

    - Spec 상태를 'analyzing'으로 즉시 변경
    - Design Agent를 백그라운드로 실행
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
