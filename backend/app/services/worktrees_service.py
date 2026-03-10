"""Worktree 서비스 레이어 — 비즈니스 로직."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import UserWorktree
from app.schemas import WorktreeCreate
from app.utils.git import WorktreeManager
from app.repositories import project_repository, user_repository, worktree_repository


def list_worktrees(project_id: str, db: Session) -> list[UserWorktree]:
    return worktree_repository.find_by_project(project_id, db)


def create_worktree(project_id: str, body: WorktreeCreate, db: Session) -> UserWorktree:
    user = user_repository.find_by_id(body.user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    project = project_repository.find_by_id(project_id, db)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = worktree_repository.find_by_user_and_project(body.user_id, project_id, db)
    if existing:
        raise HTTPException(status_code=409, detail="Worktree already exists for this user/project")

    if project.repo_url:
        mgr = WorktreeManager(project.repo_url)
        mgr.create_worktree(body.user_id, body.branch_name)

    data = body.model_dump()
    data["project_id"] = project_id
    worktree = UserWorktree(**data)
    worktree_repository.add(worktree, db)
    db.commit()
    db.refresh(worktree)
    return worktree


def delete_worktree(worktree_id: str, db: Session) -> None:
    worktree = worktree_repository.find_by_id(worktree_id, db)
    if not worktree:
        raise HTTPException(status_code=404, detail="Worktree not found")
    worktree_repository.delete(worktree, db)
    db.commit()
