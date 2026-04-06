"""Project 서비스 레이어 — 비즈니스 로직."""

from app.exceptions.business import NotFoundException
from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate
from app.repositories import project_repository
from app.utils.db_handler_sqlalchemy import db_conn


async def list_projects() -> list[Project]:
    return await project_repository.find_all()


async def get_project(project_id: str) -> Project:
    project = await project_repository.find_by_id(project_id)
    if not project:
        raise NotFoundException("Project not found")
    return project


# 프로젝트 생성
async def create_project(request: ProjectCreate) -> Project:
    async with db_conn.transaction() as session:
        project = Project(**request.model_dump())
        await project_repository.add(project, session)
        return project


async def update_project(project_id: str, body: ProjectUpdate) -> Project:
    async with db_conn.transaction() as session:
        project = await project_repository.find_by_id(project_id, session)
        if not project:
            raise NotFoundException("Project not found")
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        await session.flush()
        await session.refresh(project)
        return project


async def delete_project(project_id: str) -> None:
    async with db_conn.transaction() as session:
        project = await project_repository.find_by_id(project_id, session)
        if not project:
            raise NotFoundException("Project not found")
        project_repository.delete(project, session)
