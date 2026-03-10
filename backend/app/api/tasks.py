"""Task API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task
from app.schemas import TaskCreate, TaskResponse, TaskUpdate

# GET /api/projects/{project_id}/tasks, POST /api/projects/{project_id}/tasks
project_tasks_router = APIRouter(
    prefix="/projects/{project_id}/tasks",
    tags=["tasks"],
)

# GET /api/tasks/{task_id}, PATCH /api/tasks/{task_id}, DELETE /api/tasks/{task_id}
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@project_tasks_router.get("", response_model=list[TaskResponse])
def list_tasks(project_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.sort_order, Task.created_at)
        .all()
    )


@project_tasks_router.post("", response_model=TaskResponse, status_code=201)
def create_task(project_id: str, body: TaskCreate, db: Session = Depends(get_db)):
    data = body.model_dump()
    data["project_id"] = project_id
    task = Task(**data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@tasks_router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@tasks_router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, body: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


@tasks_router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
