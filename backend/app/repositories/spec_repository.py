"""Spec repository — DB 쿼리 전담."""

from sqlalchemy.orm import Session

from app.models import Spec


def find_by_project(project_id: str, db: Session) -> list[Spec]:
    return (
        db.query(Spec)
        .filter(Spec.project_id == project_id)
        .order_by(Spec.created_at.desc())
        .all()
    )


def find_by_id(spec_id: str, db: Session) -> Spec | None:
    return db.query(Spec).filter(Spec.id == spec_id).first()


def add(spec: Spec, db: Session) -> None:
    db.add(spec)


def delete(spec: Spec, db: Session) -> None:
    db.delete(spec)
