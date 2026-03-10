"""Worktree 서비스 레이어 — DB 조작 및 비즈니스 로직."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Project, User, UserWorktree
from app.schemas import WorktreeCreate
from app.utils.git import WorktreeManager


def list_worktrees(project_id: str, db: Session) -> list[UserWorktree]:
    return (
        db.query(UserWorktree)
        .filter(UserWorktree.project_id == project_id)
        .all()
    )


def create_worktree(project_id: str, body: WorktreeCreate, db: Session) -> UserWorktree:
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = (
        db.query(UserWorktree)
        .filter(
            UserWorktree.user_id == body.user_id,
            UserWorktree.project_id == project_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Worktree already exists for this user/project")

    if project.repo_url:
        mgr = WorktreeManager(project.repo_url)
        mgr.create_worktree(body.user_id, body.branch_name)

    data = body.model_dump()
    data["project_id"] = project_id
    worktree = UserWorktree(**data)
    db.add(worktree)
    db.commit()
    db.refresh(worktree)
    return worktree


def delete_worktree(worktree_id: str, db: Session) -> None:
    worktree = db.query(UserWorktree).filter(UserWorktree.id == worktree_id).first()
    if not worktree:
        raise HTTPException(status_code=404, detail="Worktree not found")
    db.delete(worktree)
    db.commit()
