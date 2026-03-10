"""Project 서비스 레이어 — DB 조작 및 비즈니스 로직."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.security.profiles import DEFAULT_PROFILES
from app.models import Project, SecurityProfile
from app.schemas import ProjectCreate, ProjectUpdate


def list_projects(db: Session) -> list[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


def get_project(project_id: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def create_project(body: ProjectCreate, db: Session) -> Project:
    project = Project(**body.model_dump())
    db.add(project)
    db.flush()

    stack = body.project_stack or "python"
    profile_data = DEFAULT_PROFILES.get(stack, DEFAULT_PROFILES["python"])
    security_profile = SecurityProfile(
        project_id=project.id,
        stack_type=stack,
        allowed_commands=profile_data["allowed_commands"],
        blocked_commands=profile_data["blocked_commands"],
        allowed_paths=profile_data.get("allowed_path_patterns"),
        blocked_paths=profile_data.get("blocked_path_patterns"),
    )
    db.add(security_profile)
    db.commit()
    db.refresh(project)
    return project


def update_project(project_id: str, body: ProjectUpdate, db: Session) -> Project:
    project = get_project(project_id, db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(project_id: str, db: Session) -> None:
    project = get_project(project_id, db)
    db.delete(project)
    db.commit()
