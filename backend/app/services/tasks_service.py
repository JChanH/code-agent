"""Task 서비스 레이어 — 비즈니스 로직."""

from sqlalchemy.orm import Session

from app.exceptions.business import NotFoundException
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app.repositories import task_repository


def list_tasks(project_id: str, db: Session) -> list[Task]:
    return task_repository.find_by_project(project_id, db)


def get_task(task_id: str, db: Session) -> Task:
    task = task_repository.find_by_id(task_id, db)
    if not task:
        raise NotFoundException("Task not found")
    return task


def create_task(project_id: str, body: TaskCreate, db: Session) -> Task:
    data = body.model_dump()
    data["project_id"] = project_id
    task = Task(**data)
    task_repository.add(task, db)
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
    task_repository.delete(task, db)
    db.commit()
