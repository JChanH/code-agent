"""Task API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.utils.db_handler_sqlalchemy import db_conn
from app.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.services import tasks_service

# GET /api/projects/{project_id}/tasks, POST /api/projects/{project_id}/tasks
project_tasks_router = APIRouter(
    prefix="/projects/{project_id}/tasks",
    tags=["tasks"],
)

# GET /api/tasks/{task_id}, PATCH /api/tasks/{task_id}, DELETE /api/tasks/{task_id}
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@project_tasks_router.get("", response_model=list[TaskResponse])
def list_tasks(project_id: str, db: Session = Depends(db_conn.get_db)):
    return tasks_service.list_tasks(project_id, db)


@project_tasks_router.post("", response_model=TaskResponse, status_code=201)
def create_task(project_id: str, body: TaskCreate, db: Session = Depends(db_conn.get_db)):
    return tasks_service.create_task(project_id, body, db)


@tasks_router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(db_conn.get_db)):
    return tasks_service.get_task(task_id, db)


@tasks_router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, body: TaskUpdate, db: Session = Depends(db_conn.get_db)):
    return tasks_service.update_task(task_id, body, db)


@tasks_router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(db_conn.get_db)):
    tasks_service.delete_task(task_id, db)
