"""Spec 서비스 레이어 — DB 조작 및 비즈니스 로직."""

import os
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models import Spec
from app.schemas.enums import SpecSourceType

UPLOAD_DIR = "uploads"


def list_specs(project_id: str, db: Session) -> list[Spec]:
    return (
        db.query(Spec)
        .filter(Spec.project_id == project_id)
        .order_by(Spec.created_at.desc())
        .all()
    )


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
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


def delete_spec(spec_id: str, db: Session) -> None:
    spec = db.query(Spec).filter(Spec.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")
    db.delete(spec)
    db.commit()
