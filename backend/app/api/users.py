"""User and worktree API routers."""

from fastapi import APIRouter

from app.schemas import UserCreate, UserResponse, WorktreeCreate, WorktreeResponse
from app.schemas.common import ApiResponse
from app.services import users_service, worktrees_service

users_router = APIRouter(prefix="/users", tags=["users"])
project_worktrees_router = APIRouter(prefix="/projects/{project_id}/worktrees", tags=["worktrees"])
worktrees_router = APIRouter(prefix="/worktrees", tags=["worktrees"])


@users_router.get("", response_model=ApiResponse[list[UserResponse]])
async def list_users():
    return ApiResponse.ok(await users_service.list_users())


@users_router.post("", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(body: UserCreate):
    return ApiResponse.ok(await users_service.create_user(body))


@users_router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(user_id: str):
    return ApiResponse.ok(await users_service.get_user(user_id))


@project_worktrees_router.get("", response_model=ApiResponse[list[WorktreeResponse]])
async def list_worktrees(project_id: str):
    return ApiResponse.ok(await worktrees_service.list_worktrees(project_id))


@project_worktrees_router.post("", response_model=ApiResponse[WorktreeResponse], status_code=201)
async def create_worktree(project_id: str, body: WorktreeCreate):
    return ApiResponse.ok(await worktrees_service.create_worktree(project_id, body))


@worktrees_router.delete("/{worktree_id}", response_model=ApiResponse[None])
async def delete_worktree(worktree_id: str):
    await worktrees_service.delete_worktree(worktree_id)
    return ApiResponse.ok(None)
