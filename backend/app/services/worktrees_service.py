"""Worktree 서비스 레이어 — 비즈니스 로직."""

from app.exceptions.business import ConflictException, NotFoundException
from app.models import UserWorktree
from app.schemas import WorktreeCreate
from app.utils.git import WorktreeManager
from app.repositories import project_repository, user_repository, worktree_repository
from app.utils.db_handler_sqlalchemy import db_conn


async def list_worktrees(project_id: str) -> list[UserWorktree]:
    return await worktree_repository.find_by_project(project_id)


async def create_worktree(project_id: str, body: WorktreeCreate) -> UserWorktree:
    async with db_conn.transaction() as session:
        user = await user_repository.find_by_id(body.user_id, session)
        if not user:
            raise NotFoundException("User not found")

        project = await project_repository.find_by_id(project_id, session)
        if not project:
            raise NotFoundException("Project not found")

        existing = await worktree_repository.find_by_user_and_project(body.user_id, project_id, session)
        if existing:
            raise ConflictException("Worktree already exists for this user/project")

        if project.repo_url:
            mgr = WorktreeManager(project.repo_url)
            mgr.create_worktree(body.user_id, body.branch_name)

        data = body.model_dump()
        data["project_id"] = project_id
        worktree = UserWorktree(**data)
        return await worktree_repository.add(worktree, session)


async def delete_worktree(worktree_id: str) -> None:
    async with db_conn.transaction() as session:
        worktree = await worktree_repository.find_by_id(worktree_id, session)
        if not worktree:
            raise NotFoundException("Worktree not found")
        worktree_repository.delete(worktree, session)
