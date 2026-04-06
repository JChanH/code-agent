"""Git management API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.db_handler_sqlalchemy import db_conn
from app.schemas import (
    GitCommitRequest,
    GitFileStatus,
    GitLogEntry,
    GitPullRequest,
    GitStageRequest,
)
from app.schemas.common import ApiResponse
from app.services import git_service

git_router = APIRouter(prefix="/projects/{project_id}/git", tags=["git"])


@git_router.get("/status", response_model=ApiResponse[list[GitFileStatus]])
async def git_status(
    project_id: str,
    db: AsyncSession = Depends(db_conn.get_db),
):
    return ApiResponse.ok(await git_service.get_status(project_id, db))


@git_router.get("/diff", response_model=ApiResponse[dict])
async def git_diff(
    project_id: str,
    file_path: str = Query(...),
    staged: bool = Query(False),
    db: AsyncSession = Depends(db_conn.get_db),
):
    return ApiResponse.ok(await git_service.get_diff(project_id, file_path, staged, db))


@git_router.post("/stage", response_model=ApiResponse[dict])
async def git_stage(
    project_id: str,
    body: GitStageRequest,
    db: AsyncSession = Depends(db_conn.get_db),
):
    return ApiResponse.ok(await git_service.stage_files(project_id, body.file_paths, db))


@git_router.post("/commit", response_model=ApiResponse[dict])
async def git_commit(
    project_id: str,
    body: GitCommitRequest,
    db: AsyncSession = Depends(db_conn.get_db),
):
    return ApiResponse.ok(await git_service.commit(project_id, body.message, db))


@git_router.post("/pull", response_model=ApiResponse[dict])
async def git_pull(
    project_id: str,
    body: GitPullRequest = GitPullRequest(),
    db: AsyncSession = Depends(db_conn.get_db),
):
    return ApiResponse.ok(await git_service.pull(project_id, body.strategy, db))


@git_router.post("/push", response_model=ApiResponse[dict])
async def git_push(
    project_id: str,
    db: AsyncSession = Depends(db_conn.get_db),
):
    return ApiResponse.ok(await git_service.push(project_id, db))


@git_router.get("/log", response_model=ApiResponse[list[GitLogEntry]])
async def git_log(
    project_id: str,
    count: int = Query(20, le=100),
    db: AsyncSession = Depends(db_conn.get_db),
):
    return ApiResponse.ok(await git_service.get_log(project_id, count, db))


@git_router.post("/revert", response_model=ApiResponse[dict])
async def git_revert_file(
    project_id: str,
    file_path: str = Query(...),
    db: AsyncSession = Depends(db_conn.get_db),
):
    return ApiResponse.ok(await git_service.revert_file(project_id, file_path, db))


@git_router.get("/branch", response_model=ApiResponse[dict])
async def git_current_branch(
    project_id: str,
    db: AsyncSession = Depends(db_conn.get_db),
):
    return ApiResponse.ok(await git_service.get_current_branch(project_id, db))
