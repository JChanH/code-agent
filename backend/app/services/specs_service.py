"""Spec 서비스 레이어 — 비즈니스 로직."""

import os
import uuid

from fastapi import UploadFile

from app.exceptions.business import BusinessException, NotFoundException
from app.models import Spec
from app.schemas.enums import SpecSourceType
from app.repositories import spec_repository
from app.utils.db_handler_sqlalchemy import db_conn

UPLOAD_DIR = os.path.join(os.environ.get("APP_DATA_DIR", "uploads"), "uploads")


async def list_specs(project_id: str) -> list[Spec]:
    return await spec_repository.find_by_project(project_id)


# 올린 파일 저장(문서는 pdf와 doc만 허용)
async def upload_spec(
    project_id: str,
    source_type: SpecSourceType,
    file: UploadFile | None = None,
    raw_content: str | None = None,
) -> Spec:
    source_path = None

    if file:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in (".pdf", ".doc", ".docx"):
            raise BusinessException("pdf, doc, docx 파일만 업로드할 수 있습니다.")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{uuid.uuid4()}{ext}"
        dest = os.path.join(UPLOAD_DIR, filename)
        with open(dest, "wb") as f:
            f.write(await file.read())
        source_path = dest

    async with db_conn.transaction() as session:
        spec = Spec(
            project_id=project_id,
            source_type=source_type,
            source_path=source_path,
            raw_content=raw_content,
        )
        return await spec_repository.add(spec, session)
        

async def delete_spec(spec_id: str) -> None:
    async with db_conn.transaction() as session:
        spec = await spec_repository.find_by_id(spec_id, session)
        if not spec:
            raise NotFoundException("Spec not found")
        await spec_repository.delete(spec, session)
