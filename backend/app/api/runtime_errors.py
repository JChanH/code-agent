"""Runtime errors API router."""

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.runtime_error import RuntimeErrorListResponse, RuntimeErrorResponse
from app.services import runtime_errors_service

runtime_errors_router = APIRouter(prefix="/runtime-errors", tags=["runtime-errors"])


@runtime_errors_router.get("", response_model=ApiResponse[RuntimeErrorListResponse])
async def list_all_errors(limit: int = 50, offset: int = 0):
    records, total = await runtime_errors_service.list_all_errors(limit, offset)
    items = [RuntimeErrorResponse.model_validate(r) for r in records]
    return ApiResponse.ok(RuntimeErrorListResponse(items=items, total=total, limit=limit, offset=offset))


@runtime_errors_router.get("/project/{project_id}", response_model=ApiResponse[RuntimeErrorListResponse])
async def list_errors_by_project(project_id: str, limit: int = 50, offset: int = 0):
    records, total = await runtime_errors_service.list_errors_by_project(project_id, limit, offset)
    items = [RuntimeErrorResponse.model_validate(r) for r in records]
    return ApiResponse.ok(RuntimeErrorListResponse(items=items, total=total, limit=limit, offset=offset))
