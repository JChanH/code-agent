"""Task repository — DB 쿼리 전담."""

from sqlalchemy.orm import Session

from app.models import Task


def find_by_project(project_id: str, db: Session) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.sort_order, Task.created_at)
        .all()
    )


def find_by_id(task_id: str, db: Session) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def add(task: Task, db: Session) -> None:
    db.add(task)


def delete(task: Task, db: Session) -> None:
    db.delete(task)
