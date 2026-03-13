"""Task 서비스 레이어 — 비즈니스 로직."""

from app.exceptions.business import NotFoundException
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app.repositories import task_repository, project_repository
from app.utils.db_handler_sqlalchemy import db_conn
from app.utils.git import GitService


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


async def get_task_changes(task_id: str) -> dict:
    task = await get_task(task_id)
    if not task.git_commit_hash:
        return {"commit_hash": None, "diff": None, "files": []}
    project = await project_repository.find_by_id(task.project_id)
    if not project:
        raise NotFoundException("Project not found")
    git_svc = GitService(project.local_repo_path)
    diff = git_svc.get_commit_diff(task.git_commit_hash)
    files = git_svc.get_commit_files(task.git_commit_hash)
    return {"commit_hash": task.git_commit_hash, "diff": diff, "files": files}


async def rollback_task(task_id: str) -> Task:
    task = await get_task(task_id)
    if not task.git_commit_hash:
        raise NotFoundException("No commit found for this task")
    project = await project_repository.find_by_id(task.project_id)
    if not project:
        raise NotFoundException("Project not found")
    git_svc = GitService(project.local_repo_path)
    git_svc.revert_commit(task.git_commit_hash)
    async with db_conn.transaction() as session:
        t = await task_repository.find_by_id(task_id, session)
        t.status = "confirmed"
        t.git_commit_hash = None
        t.completed_at = None
        await session.flush()
        await session.refresh(t)
        return t
