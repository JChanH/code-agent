"""Git management API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

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
def git_status(
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(git_service.get_status(project_id, user_id, db))


@git_router.get("/diff", response_model=ApiResponse[dict])
def git_diff(
    project_id: str,
    file_path: str = Query(...),
    user_id: str = Query(...),
    staged: bool = Query(False),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(git_service.get_diff(project_id, user_id, file_path, staged, db))


@git_router.post("/stage", response_model=ApiResponse[dict])
def git_stage(
    project_id: str,
    body: GitStageRequest,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(git_service.stage_files(project_id, user_id, body.file_paths, db))


@git_router.post("/commit", response_model=ApiResponse[dict])
def git_commit(
    project_id: str,
    body: GitCommitRequest,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(git_service.commit(project_id, user_id, body.message, db))


@git_router.post("/pull", response_model=ApiResponse[dict])
def git_pull(
    project_id: str,
    body: GitPullRequest = GitPullRequest(),
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(git_service.pull(project_id, user_id, body.strategy, db))


@git_router.post("/push", response_model=ApiResponse[dict])
def git_push(
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(git_service.push(project_id, user_id, db))


@git_router.get("/log", response_model=ApiResponse[list[GitLogEntry]])
def git_log(
    project_id: str,
    user_id: str = Query(...),
    count: int = Query(20, le=100),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(git_service.get_log(project_id, user_id, count, db))


@git_router.post("/revert", response_model=ApiResponse[dict])
def git_revert_file(
    project_id: str,
    file_path: str = Query(...),
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(git_service.revert_file(project_id, user_id, file_path, db))


@git_router.get("/branch", response_model=ApiResponse[dict])
def git_current_branch(
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    return ApiResponse.ok(git_service.get_current_branch(project_id, user_id, db))
