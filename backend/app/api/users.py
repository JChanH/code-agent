"""User and worktree API routers."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, User, UserWorktree
from app.schemas import (
    UserCreate,
    UserResponse,
    WorktreeCreate,
    WorktreeResponse,
)
from app.services.git import WorktreeManager

users_router = APIRouter(prefix="/users", tags=["users"])
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


@worktrees_router.get("", response_model=list[WorktreeResponse])
def list_worktrees(
    project_id: str = Query(None),
    user_id: str = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(UserWorktree)
    if project_id:
        q = q.filter(UserWorktree.project_id == project_id)
    if user_id:
        q = q.filter(UserWorktree.user_id == user_id)
    return q.all()


@worktrees_router.post("", response_model=WorktreeResponse, status_code=201)
def create_worktree(body: WorktreeCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    project = db.query(Project).filter(Project.id == body.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = (
        db.query(UserWorktree)
        .filter(
            UserWorktree.user_id == body.user_id,
            UserWorktree.project_id == body.project_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Worktree already exists for this user/project")

    if project.repo_url:
        mgr = WorktreeManager(project.repo_url)
        mgr.create_worktree(body.user_id, body.branch_name)

    worktree = UserWorktree(**body.model_dump())
    db.add(worktree)
    db.commit()
    db.refresh(worktree)
    return worktree
