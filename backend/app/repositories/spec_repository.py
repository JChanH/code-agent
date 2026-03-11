"""Spec repository — DB 쿼리 전담."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Spec
from app.utils.db_handler_sqlalchemy import db_conn


async def find_by_project(project_id: str, session: AsyncSession | None = None) -> list[Spec]:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(Spec)
            .where(Spec.project_id == project_id)
            .order_by(Spec.created_at.desc())
        )
        return result.scalars().all()


async def find_by_id(spec_id: str, session: AsyncSession | None = None) -> Spec | None:
    async with db_conn.transaction(session) as s:
        result = await s.execute(select(Spec).where(Spec.id == spec_id))
        return result.scalars().first()


async def add(spec: Spec, session: AsyncSession | None = None) -> Spec:
    async with db_conn.transaction(session) as s:
        s.add(spec)
        await s.flush()
        await s.refresh(spec)
        return spec


async def delete(spec: Spec, session: AsyncSession) -> None:
    await session.delete(spec)
