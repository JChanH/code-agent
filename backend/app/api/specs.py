"""Spec API router."""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.utils.db_handler_sqlalchemy import db_conn
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
def list_specs(project_id: str, db: Session = Depends(db_conn.get_db)):
    return ApiResponse.ok(specs_service.list_specs(project_id, db))


@project_specs_router.post("", response_model=ApiResponse[SpecResponse], status_code=201)
async def upload_spec(
    project_id: str,
    source_type: SpecSourceType = Form(SpecSourceType.document),
    file: UploadFile = File(None),
    raw_content: str = Form(None),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(
        await specs_service.upload_spec(project_id, source_type, db, file=file, raw_content=raw_content)
    )


@specs_router.delete("/{spec_id}", response_model=ApiResponse[None])
def delete_spec(spec_id: str, db: Session = Depends(db_conn.get_db)):
    specs_service.delete_spec(spec_id, db)
    return ApiResponse.ok(None)
