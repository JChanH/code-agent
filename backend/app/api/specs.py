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

# DELETE /api/specs/{spec_id}, POST /api/specs/{spec_id}/final-confirm
specs_router = APIRouter(prefix="/specs", tags=["specs"])


@project_specs_router.get("")
async def list_specs(
    project_id: str
) -> ApiResponse[list[SpecResponse]]:
    """
    프로젝트에 속한 모든 Spec 목록을 조회합니다.

    - project_id: 조회할 프로젝트의 ID
    """
    return ApiResponse.ok(await specs_service.list_specs(project_id))


@project_specs_router.post("")
async def upload_spec(
    project_id: str,
    source_type: SpecSourceType = Form(SpecSourceType.document),
    file: UploadFile = File(None),
    raw_content: str = Form(None),
) -> ApiResponse[SpecResponse]:
    """
    프로젝트에 새 Spec을 업로드합니다.

    - project_id: 대상 프로젝트의 ID
    - source_type: Spec 소스 유형 (document, text 등)
    - file: 업로드할 파일 (source_type이 document일 때 사용)
    - raw_content: 직접 입력한 텍스트 내용 (source_type이 text일 때 사용)
    """
    return ApiResponse.ok(
        await specs_service.upload_spec(project_id, source_type, file=file, raw_content=raw_content)
    )


@specs_router.delete("/{spec_id}")
async def delete_spec(
    spec_id: str
) -> ApiResponse[None]:
    """
    지정한 Spec을 삭제합니다.

    - spec_id: 삭제할 Spec의 ID
    """
    await specs_service.delete_spec(spec_id)
    return ApiResponse.ok(None)


@specs_router.post("/{spec_id}/final-confirm")
async def final_confirm_spec(
    spec_id: str
) -> ApiResponse[dict]:
    """
    Spec을 최종 확정합니다.

    - 모든 Task가 'confirmed' 상태일 때 Spec을 'final_confirmed'로 변경합니다.
    """
    spec = await spec_repository.find_by_id(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")

    if spec.status == "analyzing":
        raise HTTPException(
            status_code=409,
            detail="분석 중인 Spec은 확정할 수 없습니다.",
        )

    async with db_conn.transaction() as session:
        fresh_spec = await spec_repository.find_by_id(spec_id, session)
        fresh_spec.status = "final_confirmed"
        await session.flush()

    tasks = await task_repository.find_by_project(spec.project_id)
    spec_tasks = [t for t in tasks if t.spec_id == spec_id]
    confirmed_count = sum(1 for t in spec_tasks if t.status == "confirmed")

    return ApiResponse.ok(
        {
            "spec_id": spec_id,
            "status": "final_confirmed",
            "task_count": len(spec_tasks),
            "confirmed_count": confirmed_count,
            "message": f"{confirmed_count}/{len(spec_tasks)}개 Task가 확정되었습니다.",
        }
    )
