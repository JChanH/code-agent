"""Runtime errors API router."""

from fastapi import APIRouter, HTTPException

from app.schemas.common import ApiResponse
from app.schemas.runtime_error import RuntimeErrorListResponse, RuntimeErrorResponse, RuntimeErrorSourcePathUpdate, RuntimeErrorStatusUpdate
from app.services import runtime_errors_service

runtime_errors_router = APIRouter(prefix="/runtime-errors", tags=["runtime-errors"])

# 모든 오류 리스트 조회
@runtime_errors_router.get("")
async def list_all_errors(
    limit: int = 50,
    offset: int = 0
) -> ApiResponse[RuntimeErrorListResponse]:
    records, total = await runtime_errors_service.list_all_errors(limit, offset)
    items = [RuntimeErrorResponse.model_validate(r) for r in records]
    return ApiResponse.ok(
        RuntimeErrorListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )
    )


# 프로젝트별 오류 리스트 조회
@runtime_errors_router.get("/project/{project_id}")
async def list_errors_by_project(
    project_id: str,
    limit: int = 50,
    offset: int = 0
) -> ApiResponse[RuntimeErrorListResponse]:
    records, total = await runtime_errors_service.list_errors_by_project(project_id, limit, offset)
    items = [RuntimeErrorResponse.model_validate(r) for r in records]
    return ApiResponse.ok(
        RuntimeErrorListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )
    )


# 오류 상태값 변경
@runtime_errors_router.patch("/{error_id}/status")
async def update_error_status(
    error_id: str,
    body: RuntimeErrorStatusUpdate
) -> ApiResponse[RuntimeErrorResponse]:
    record = await runtime_errors_service.update_status(error_id, body.status)
    if not record:
        raise HTTPException(status_code=404, detail="Runtime error not found")
    return ApiResponse.ok(
        RuntimeErrorResponse.model_validate(record)
    )


# 소스코드 경로 변경
@runtime_errors_router.patch("/{error_id}/source-path")
async def update_error_source_path(
    error_id: str,
    body: RuntimeErrorSourcePathUpdate
) -> ApiResponse[RuntimeErrorResponse]:
    record = await runtime_errors_service.update_source_path(error_id, body.source_path)
    if not record:
        raise HTTPException(status_code=404, detail="Runtime error not found")
    return ApiResponse.ok(
        RuntimeErrorResponse.model_validate(record)
    )
