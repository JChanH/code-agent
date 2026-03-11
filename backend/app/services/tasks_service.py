"""Task 서비스 레이어 — 비즈니스 로직."""

from app.exceptions.business import NotFoundException
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app.repositories import task_repository
from app.utils.db_handler_sqlalchemy import db_conn


async def list_tasks(project_id: str) -> list[Task]:
    return await task_repository.find_by_project(project_id)


async def get_task(task_id: str) -> Task:
    task = await task_repository.find_by_id(task_id)
    if not task:
        raise NotFoundException("Task not found")
    return task


async def create_task(project_id: str, body: TaskCreate) -> Task:
    async with db_conn.transaction() as session:
        data = body.model_dump()
        data["project_id"] = project_id
        task = Task(**data)
        return await task_repository.add(task, session)


async def update_task(task_id: str, body: TaskUpdate) -> Task:
    async with db_conn.transaction() as session:
        task = await task_repository.find_by_id(task_id, session)
        if not task:
            raise NotFoundException("Task not found")
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(task, key, value)
        await session.flush()
        await session.refresh(task)
        return task


async def delete_task(task_id: str) -> None:
    async with db_conn.transaction() as session:
        task = await task_repository.find_by_id(task_id, session)
        if not task:
            raise NotFoundException("Task not found")
        task_repository.delete(task, session)
