"""Task 서비스 레이어 — DB 조작 및 비즈니스 로직."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Task
from app.schemas import TaskCreate, TaskUpdate


def list_tasks(project_id: str, db: Session) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.sort_order, Task.created_at)
        .all()
    )


def get_task(task_id: str, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def create_task(project_id: str, body: TaskCreate, db: Session) -> Task:
    data = body.model_dump()
    data["project_id"] = project_id
    task = Task(**data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(task_id: str, body: TaskUpdate, db: Session) -> Task:
    task = get_task(task_id, db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(task_id: str, db: Session) -> None:
    task = get_task(task_id, db)
    db.delete(task)
    db.commit()
