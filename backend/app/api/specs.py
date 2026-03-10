"""Spec API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Spec
from app.schemas import SpecCreate, SpecResponse

specs_router = APIRouter(prefix="/specs", tags=["specs"])


@specs_router.get("", response_model=list[SpecResponse])
def list_specs(project_id: str = Query(None), db: Session = Depends(get_db)):
    q = db.query(Spec)
    if project_id:
        q = q.filter(Spec.project_id == project_id)
    return q.order_by(Spec.created_at.desc()).all()


@specs_router.post("", response_model=SpecResponse, status_code=201)
def create_spec(body: SpecCreate, db: Session = Depends(get_db)):
    spec = Spec(**body.model_dump())
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec
