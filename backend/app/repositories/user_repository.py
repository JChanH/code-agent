"""User repository — DB 쿼리 전담."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.utils.db_handler_sqlalchemy import db_conn


async def find_all(session: AsyncSession | None = None) -> list[User]:
    async with db_conn.transaction(session) as s:
        result = await s.execute(select(User).order_by(User.username))
        return result.scalars().all()


async def find_by_id(user_id: str, session: AsyncSession | None = None) -> User | None:
    async with db_conn.transaction(session) as s:
        result = await s.execute(select(User).where(User.id == user_id))
        return result.scalars().first()


async def find_by_username(username: str, session: AsyncSession | None = None) -> User | None:
    async with db_conn.transaction(session) as s:
        result = await s.execute(select(User).where(User.username == username))
        return result.scalars().first()


async def add(user: User, session: AsyncSession | None = None) -> User:
    async with db_conn.transaction(session) as s:
        s.add(user)
        await s.flush()
        await s.refresh(user)
        return user


async def delete(user: User, session: AsyncSession | None = None) -> None:
    async with db_conn.transaction(session) as s:
        await s.delete(user)
