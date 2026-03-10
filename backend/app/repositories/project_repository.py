"""Project repository — DB 쿼리 전담."""

from sqlalchemy.orm import Session

from app.models import Project


def find_all(db: Session) -> list[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


def find_by_id(project_id: str, db: Session) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()


def add(project: Project, db: Session) -> None:
    db.add(project)


def delete(project: Project, db: Session) -> None:
    db.delete(project)
