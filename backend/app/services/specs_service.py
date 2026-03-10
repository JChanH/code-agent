"""Spec 서비스 레이어 — 비즈니스 로직."""

import os
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.exceptions.business import NotFoundException
from app.models import Spec
from app.schemas.enums import SpecSourceType
from app.repositories import spec_repository

UPLOAD_DIR = "uploads"


def list_specs(project_id: str, db: Session) -> list[Spec]:
    return spec_repository.find_by_project(project_id, db)


async def upload_spec(
    project_id: str,
    source_type: SpecSourceType,
    db: Session,
    file: UploadFile | None = None,
    raw_content: str | None = None,
) -> Spec:
    source_path = None

    if file:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename or "")[1]
        filename = f"{uuid.uuid4()}{ext}"
        dest = os.path.join(UPLOAD_DIR, filename)
        with open(dest, "wb") as f:
            f.write(await file.read())
        source_path = dest

    spec = Spec(
        project_id=project_id,
        source_type=source_type,
        source_path=source_path,
        raw_content=raw_content,
    )
    spec_repository.add(spec, db)
    db.commit()
    db.refresh(spec)
    return spec


def delete_spec(spec_id: str, db: Session) -> None:
    spec = spec_repository.find_by_id(spec_id, db)
    if not spec:
        raise NotFoundException("Spec not found")
    spec_repository.delete(spec, db)
    db.commit()
