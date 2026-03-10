"""User and worktree API routers."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, User, UserWorktree
from app.schemas import (
    UserCreate,
    UserResponse,
    WorktreeCreate,
    WorktreeResponse,
)
from app.utils.git import WorktreeManager

users_router = APIRouter(prefix="/users", tags=["users"])

# GET /api/projects/{project_id}/worktrees, POST /api/projects/{project_id}/worktrees
project_worktrees_router = APIRouter(
    prefix="/projects/{project_id}/worktrees",
    tags=["worktrees"],
)

# DELETE /api/worktrees/{worktree_id}
worktrees_router = APIRouter(prefix="/worktrees", tags=["worktrees"])


@users_router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.username).all()


@users_router.post("", response_model=UserResponse, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(**body.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@users_router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@project_worktrees_router.get("", response_model=list[WorktreeResponse])
def list_worktrees(project_id: str, db: Session = Depends(get_db)):
    return (
        db.query(UserWorktree)
        .filter(UserWorktree.project_id == project_id)
        .all()
    )


@project_worktrees_router.post("", response_model=WorktreeResponse, status_code=201)
def create_worktree(project_id: str, body: WorktreeCreate, db: Session = Depends(get_db)):
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


@worktrees_router.delete("/{worktree_id}", status_code=204)
def delete_worktree(worktree_id: str, db: Session = Depends(get_db)):
    worktree = db.query(UserWorktree).filter(UserWorktree.id == worktree_id).first()
    if not worktree:
        raise HTTPException(status_code=404, detail="Worktree not found")
    db.delete(worktree)
    db.commit()
