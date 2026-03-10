"""UserWorktree repository — DB 쿼리 전담."""

from sqlalchemy.orm import Session

from app.models import UserWorktree


def find_by_project(project_id: str, db: Session) -> list[UserWorktree]:
    return (
        db.query(UserWorktree)
        .filter(UserWorktree.project_id == project_id)
        .all()
    )


def find_by_id(worktree_id: str, db: Session) -> UserWorktree | None:
    return db.query(UserWorktree).filter(UserWorktree.id == worktree_id).first()


def find_by_user_and_project(user_id: str, project_id: str, db: Session) -> UserWorktree | None:
    return (
        db.query(UserWorktree)
        .filter(
            UserWorktree.user_id == user_id,
            UserWorktree.project_id == project_id,
        )
        .first()
    )


def find_active_by_user_and_project(user_id: str, project_id: str, db: Session) -> UserWorktree | None:
    return (
        db.query(UserWorktree)
        .filter(
            UserWorktree.project_id == project_id,
            UserWorktree.user_id == user_id,
            UserWorktree.status == "active",
        )
        .first()
    )


def add(worktree: UserWorktree, db: Session) -> None:
    db.add(worktree)


def delete(worktree: UserWorktree, db: Session) -> None:
    db.delete(worktree)
