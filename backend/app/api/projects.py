"""Project API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.security.profiles import DEFAULT_PROFILES
from app.database import get_db
from app.models import Project, SecurityProfile
from app.schemas import ProjectCreate, ProjectResponse, ProjectUpdate

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@projects_router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
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


@projects_router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@projects_router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, body: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@projects_router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
