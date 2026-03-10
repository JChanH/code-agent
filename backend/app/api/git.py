"""Git management API router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.utils.db_handler_sqlalchemy import db_conn
from app.models import UserWorktree
from app.schemas import (
    GitCommitRequest,
    GitFileStatus,
    GitLogEntry,
    GitPullRequest,
    GitStageRequest,
)
from app.utils.git import GitService

git_router = APIRouter(prefix="/projects/{project_id}/git", tags=["git"])


def _get_git_service(project_id: str, user_id: str, db: Session) -> GitService:
    worktree = (
        db.query(UserWorktree)
        .filter(
            UserWorktree.project_id == project_id,
            UserWorktree.user_id == user_id,
            UserWorktree.status == "active",
        )
        .first()
    )
    if not worktree:
        raise HTTPException(
            status_code=404,
            detail="No active worktree found for this user/project",
        )
    return GitService(worktree.worktree_path)


@git_router.get("/status", response_model=list[GitFileStatus])
def git_status(
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    return svc.get_status()


@git_router.get("/diff")
def git_diff(
    project_id: str,
    file_path: str = Query(...),
    user_id: str = Query(...),
    staged: bool = Query(False),
    db: Session = Depends(db_conn.get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    return {"diff": svc.get_diff(file_path, staged=staged)}


@git_router.post("/stage")
def git_stage(
    project_id: str,
    body: GitStageRequest,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    svc.stage_files(body.file_paths)
    return {"message": "Files staged", "files": body.file_paths}


@git_router.post("/commit")
def git_commit(
    project_id: str,
    body: GitCommitRequest,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    commit_hash = svc.commit(body.message)
    return {"message": "Committed", "hash": commit_hash}


@git_router.post("/pull")
def git_pull(
    project_id: str,
    body: GitPullRequest = GitPullRequest(),
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    output = svc.pull(strategy=body.strategy)
    return {"message": "Pull completed", "output": output}


@git_router.post("/push")
def git_push(
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    output = svc.push()
    return {"message": "Push completed", "output": output}


@git_router.get("/log", response_model=list[GitLogEntry])
def git_log(
    project_id: str,
    user_id: str = Query(...),
    count: int = Query(20, le=100),
    db: Session = Depends(db_conn.get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    return svc.get_log(count=count)


@git_router.post("/revert")
def git_revert_file(
    project_id: str,
    file_path: str = Query(...),
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    svc.revert_file(file_path)
    return {"message": f"Reverted: {file_path}"}


@git_router.get("/branch")
def git_current_branch(
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(db_conn.get_db),
):
    svc = _get_git_service(project_id, user_id, db)
    return {"branch": svc.get_current_branch()}
