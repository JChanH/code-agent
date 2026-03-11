"""Spec API router."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.repositories import spec_repository, task_repository
from app.schemas import SpecResponse
from app.schemas.common import ApiResponse
from app.schemas.enums import SpecSourceType
from app.services import specs_service
from app.utils.db_handler_sqlalchemy import db_conn

# GET /api/projects/{project_id}/specs, POST /api/projects/{project_id}/specs
project_specs_router = APIRouter(
    prefix="/projects/{project_id}/specs",
    tags=["specs"],
)

# DELETE /api/specs/{spec_id}, POST /api/specs/{spec_id}/confirm
specs_router = APIRouter(prefix="/specs", tags=["specs"])


@project_specs_router.get("", response_model=ApiResponse[list[SpecResponse]])
async def list_specs(project_id: str):
    return ApiResponse.ok(await specs_service.list_specs(project_id))


@project_specs_router.post("", response_model=ApiResponse[SpecResponse], status_code=201)
async def upload_spec(
    project_id: str,
    source_type: SpecSourceType = Form(SpecSourceType.document),
    file: UploadFile = File(None),
    raw_content: str = Form(None),
):
    return ApiResponse.ok(
        await specs_service.upload_spec(project_id, source_type, file=file, raw_content=raw_content)
    )


@specs_router.delete("/{spec_id}", response_model=ApiResponse[None])
async def delete_spec(spec_id: str):
    await specs_service.delete_spec(spec_id)
    return ApiResponse.ok(None)


@specs_router.post("/{spec_id}/confirm", response_model=ApiResponse[dict])
async def confirm_spec(spec_id: str):
    """
    분석된 Spec을 확정합니다.

    - Spec 상태: 'analyzed' → 'confirmed'
    - 연결된 Task들 상태: 'backlog' (이미 분석 시 저장됨)
    - 이후 개발 단계(DevPhase) Kanban의 Backlog 컬럼에 표시됩니다.
    """
    spec = await spec_repository.find_by_id(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")

    if spec.status not in ("analyzed", "confirmed"):
        raise HTTPException(
            status_code=409,
            detail=f"분석 완료된 Spec만 확정할 수 있습니다. 현재 상태: {spec.status}",
        )

    async with db_conn.transaction() as session:
        fresh_spec = await spec_repository.find_by_id(spec_id, session)
        fresh_spec.status = "confirmed"
        await session.flush()

    # 연결된 Task 목록 조회
    tasks = await task_repository.find_by_project(spec.project_id)
    spec_tasks = [t for t in tasks if t.spec_id == spec_id]

    return ApiResponse.ok(
        {
            "spec_id": spec_id,
            "status": "confirmed",
            "task_count": len(spec_tasks),
            "message": f"{len(spec_tasks)}개 Task가 개발 단계 Backlog으로 이동했습니다.",
        }
    )
