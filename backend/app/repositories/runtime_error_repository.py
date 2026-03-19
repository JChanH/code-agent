"""RuntimeErrorRecord repository — DB 쿼리 전담."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.runtime_error import RuntimeErrorRecord
from app.utils.db_handler_sqlalchemy import db_conn


async def add(record: RuntimeErrorRecord, session: AsyncSession | None = None) -> RuntimeErrorRecord:
    async with db_conn.transaction(session) as s:
        s.add(record)
        await s.flush()
        await s.refresh(record)
        return record


async def find_by_project(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession | None = None,
) -> list[RuntimeErrorRecord]:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(RuntimeErrorRecord)
            .where(RuntimeErrorRecord.project_id == project_id)
            .order_by(RuntimeErrorRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


async def count_by_project(project_id: str, session: AsyncSession | None = None) -> int:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(func.count()).select_from(RuntimeErrorRecord)
            .where(RuntimeErrorRecord.project_id == project_id)
        )
        return result.scalar_one()


async def find_all(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession | None = None,
) -> list[RuntimeErrorRecord]:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(RuntimeErrorRecord)
            .order_by(RuntimeErrorRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


async def count_all(session: AsyncSession | None = None) -> int:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(func.count()).select_from(RuntimeErrorRecord)
        )
        return result.scalar_one()
