"""SecurityProfile repository — DB 쿼리 전담."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SecurityProfile
from app.utils.db_handler_sqlalchemy import db_conn


async def add(profile: SecurityProfile, session: AsyncSession | None = None) -> None:
    async with db_conn.transaction(session) as s:
        s.add(profile)
