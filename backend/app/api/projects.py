"""Project API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.utils.db_handler_sqlalchemy import db_conn
from app.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import projects_service

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(db_conn.get_db)):
    return projects_service.list_projects(db)


@projects_router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(db_conn.get_db)):
    return projects_service.create_project(body, db)


@projects_router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(db_conn.get_db)):
    return projects_service.get_project(project_id, db)


@projects_router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, body: ProjectUpdate, db: Session = Depends(db_conn.get_db)):
    return projects_service.update_project(project_id, body, db)


@projects_router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(db_conn.get_db)):
    projects_service.delete_project(project_id, db)
