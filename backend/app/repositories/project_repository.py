"""Project repository — DB 쿼리 전담."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project
from app.utils.db_handler_sqlalchemy import db_conn


async def find_all(session: AsyncSession | None = None) -> list[Project]:
    async with db_conn.transaction(session) as s:
        result = await s.execute(select(Project).order_by(Project.created_at.desc()))
        return result.scalars().all()


async def find_by_id(project_id: str, session: AsyncSession | None = None) -> Project | None:
    async with db_conn.transaction(session) as s:
        result = await s.execute(select(Project).where(Project.id == project_id))
        return result.scalars().first()


async def find_by_name(name: str, session: AsyncSession | None = None) -> Project | None:
    async with db_conn.transaction(session) as s:
        result = await s.execute(select(Project).where(Project.name == name))
        return result.scalars().first()


async def add(project: Project, session: AsyncSession | None = None) -> Project:
    async with db_conn.transaction(session) as s:
        s.add(project)
        await s.flush()
        await s.refresh(project)
        return project


def delete(project: Project, session: AsyncSession) -> None:
    session.delete(project)
