"""Spec API router."""

from fastapi import APIRouter, File, Form, UploadFile

from app.schemas import SpecResponse
from app.schemas.common import ApiResponse
from app.schemas.enums import SpecSourceType
from app.services import specs_service

# GET /api/projects/{project_id}/specs, POST /api/projects/{project_id}/specs
project_specs_router = APIRouter(
    prefix="/projects/{project_id}/specs",
    tags=["specs"],
)

# DELETE /api/specs/{spec_id}
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
