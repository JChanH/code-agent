"""Task repository — DB 쿼리 전담."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task
from app.utils.db_handler_sqlalchemy import db_conn


async def find_by_project(project_id: str, session: AsyncSession | None = None) -> list[Task]:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.created_at)
        )
        return result.scalars().all()


async def find_by_id(task_id: str, session: AsyncSession | None = None) -> Task | None:
    async with db_conn.transaction(session) as s:
        result = await s.execute(select(Task).where(Task.id == task_id))
        return result.scalars().first()


async def add(task: Task, session: AsyncSession | None = None) -> Task:
    async with db_conn.transaction(session) as s:
        s.add(task)
        await s.flush()
        await s.refresh(task)
        return task


async def delete(task: Task, session: AsyncSession | None = None) -> None:
    async with db_conn.transaction(session) as s:
        await s.delete(task)
