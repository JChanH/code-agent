"""Project 서비스 레이어 — 비즈니스 로직."""

from app.agents.security.profiles import DEFAULT_PROFILES
from app.exceptions.business import NotFoundException
from app.models import Project, SecurityProfile
from app.schemas import ProjectCreate, ProjectUpdate
from app.repositories import project_repository, security_profile_repository
from app.utils.db_handler_sqlalchemy import db_conn


async def list_projects() -> list[Project]:
    return await project_repository.find_all()


async def get_project(project_id: str) -> Project:
    project = await project_repository.find_by_id(project_id)
    if not project:
        raise NotFoundException("Project not found")
    return project


async def create_project(body: ProjectCreate) -> Project:
    async with db_conn.transaction() as session:
        project = Project(**body.model_dump())
        await project_repository.add(project, session)

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
        await security_profile_repository.add(security_profile, session)
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
