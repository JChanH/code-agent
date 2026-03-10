"""Git 서비스 레이어 — worktree 조회 및 Git 명령 위임."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import UserWorktree
from app.utils.git import GitService


def get_git_service(project_id: str, user_id: str, db: Session) -> GitService:
    """사용자의 활성 worktree를 조회하고 GitService 인스턴스를 반환한다."""
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


def get_status(project_id: str, user_id: str, db: Session) -> list[dict]:
    svc = get_git_service(project_id, user_id, db)
    return svc.get_status()


def get_diff(project_id: str, user_id: str, file_path: str, staged: bool, db: Session) -> dict:
    svc = get_git_service(project_id, user_id, db)
    return {"diff": svc.get_diff(file_path, staged=staged)}


def stage_files(project_id: str, user_id: str, file_paths: list[str], db: Session) -> dict:
    svc = get_git_service(project_id, user_id, db)
    svc.stage_files(file_paths)
    return {"message": "Files staged", "files": file_paths}


def commit(project_id: str, user_id: str, message: str, db: Session) -> dict:
    svc = get_git_service(project_id, user_id, db)
    commit_hash = svc.commit(message)
    return {"message": "Committed", "hash": commit_hash}


def pull(project_id: str, user_id: str, strategy: str, db: Session) -> dict:
    svc = get_git_service(project_id, user_id, db)
    output = svc.pull(strategy=strategy)
    return {"message": "Pull completed", "output": output}


def push(project_id: str, user_id: str, db: Session) -> dict:
    svc = get_git_service(project_id, user_id, db)
    output = svc.push()
    return {"message": "Push completed", "output": output}


def get_log(project_id: str, user_id: str, count: int, db: Session) -> list[dict]:
    svc = get_git_service(project_id, user_id, db)
    return svc.get_log(count=count)


def revert_file(project_id: str, user_id: str, file_path: str, db: Session) -> dict:
    svc = get_git_service(project_id, user_id, db)
    svc.revert_file(file_path)
    return {"message": f"Reverted: {file_path}"}


def get_current_branch(project_id: str, user_id: str, db: Session) -> dict:
    svc = get_git_service(project_id, user_id, db)
    return {"branch": svc.get_current_branch()}
