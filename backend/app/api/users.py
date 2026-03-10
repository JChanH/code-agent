"""User and worktree API routers."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.utils.db_handler_sqlalchemy import db_conn
from app.schemas import UserCreate, UserResponse, WorktreeCreate, WorktreeResponse
from app.schemas.common import ApiResponse
from app.services import users_service, worktrees_service

users_router = APIRouter(prefix="/users", tags=["users"])
project_worktrees_router = APIRouter(prefix="/projects/{project_id}/worktrees", tags=["worktrees"])
worktrees_router = APIRouter(prefix="/worktrees", tags=["worktrees"])


@users_router.get("", response_model=ApiResponse[list[UserResponse]])
def list_users(db: Session = Depends(db_conn.get_db)):
    return ApiResponse.ok(users_service.list_users(db))


@users_router.post("", response_model=ApiResponse[UserResponse], status_code=201)
def create_user(body: UserCreate, db: Session = Depends(db_conn.get_db)):
    return ApiResponse.ok(users_service.create_user(body, db))


@users_router.get("/{user_id}", response_model=ApiResponse[UserResponse])
def get_user(user_id: str, db: Session = Depends(db_conn.get_db)):
    return ApiResponse.ok(users_service.get_user(user_id, db))


@project_worktrees_router.get("", response_model=ApiResponse[list[WorktreeResponse]])
def list_worktrees(project_id: str, db: Session = Depends(db_conn.get_db)):
    return ApiResponse.ok(worktrees_service.list_worktrees(project_id, db))


@project_worktrees_router.post("", response_model=ApiResponse[WorktreeResponse], status_code=201)
def create_worktree(project_id: str, body: WorktreeCreate, db: Session = Depends(db_conn.get_db)):
    return ApiResponse.ok(worktrees_service.create_worktree(project_id, body, db))


@worktrees_router.delete("/{worktree_id}", response_model=ApiResponse[None])
def delete_worktree(worktree_id: str, db: Session = Depends(db_conn.get_db)):
    worktrees_service.delete_worktree(worktree_id, db)
    return ApiResponse.ok(None)
