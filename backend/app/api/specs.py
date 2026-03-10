"""Spec API router."""

import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.utils.db_handler_sqlalchemy import db_conn
from app.models import Spec
from app.schemas import SpecResponse
from app.schemas.enums import SpecSourceType

UPLOAD_DIR = "uploads"

# GET /api/projects/{project_id}/specs, POST /api/projects/{project_id}/specs
project_specs_router = APIRouter(
    prefix="/projects/{project_id}/specs",
    tags=["specs"],
)

# DELETE /api/specs/{spec_id}
specs_router = APIRouter(prefix="/specs", tags=["specs"])


@project_specs_router.get("", response_model=list[SpecResponse])
def list_specs(project_id: str, db: Session = Depends(db_conn.get_db)):
    return (
        db.query(Spec)
        .filter(Spec.project_id == project_id)
        .order_by(Spec.created_at.desc())
        .all()
    )


@project_specs_router.post("", response_model=SpecResponse, status_code=201)
async def upload_spec(
    project_id: str,
    source_type: SpecSourceType = Form(SpecSourceType.document),
    file: UploadFile = File(None),
    raw_content: str = Form(None),
    db: Session = Depends(db_conn.get_db),
):
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


@specs_router.delete("/{spec_id}", status_code=204)
def delete_spec(spec_id: str, db: Session = Depends(db_conn.get_db)):
    spec = db.query(Spec).filter(Spec.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")
    db.delete(spec)
    db.commit()
