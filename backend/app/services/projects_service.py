"""Project 서비스 레이어 — 비즈니스 로직."""

from sqlalchemy.orm import Session

from app.agents.security.profiles import DEFAULT_PROFILES
from app.exceptions.business import NotFoundException
from app.models import Project, SecurityProfile
from app.schemas import ProjectCreate, ProjectUpdate
from app.repositories import project_repository, security_profile_repository


def list_projects(db: Session) -> list[Project]:
    return project_repository.find_all(db)


def get_project(project_id: str, db: Session) -> Project:
    project = project_repository.find_by_id(project_id, db)
    if not project:
        raise NotFoundException("Project not found")
    return project


def create_project(body: ProjectCreate, db: Session) -> Project:
    project = Project(**body.model_dump())
    project_repository.add(project, db)
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
    security_profile_repository.add(security_profile, db)
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
    project_repository.delete(project, db)
    db.commit()
