"""UserWorktree repository — DB 쿼리 전담."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserWorktree
from app.utils.db_handler_sqlalchemy import db_conn


async def find_by_project(project_id: str, session: AsyncSession | None = None) -> list[UserWorktree]:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(UserWorktree).where(UserWorktree.project_id == project_id)
        )
        return result.scalars().all()


async def find_by_id(worktree_id: str, session: AsyncSession | None = None) -> UserWorktree | None:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(UserWorktree).where(UserWorktree.id == worktree_id)
        )
        return result.scalars().first()


async def find_by_user_and_project(
    user_id: str, project_id: str, session: AsyncSession | None = None
) -> UserWorktree | None:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(UserWorktree).where(
                UserWorktree.user_id == user_id,
                UserWorktree.project_id == project_id,
            )
        )
        return result.scalars().first()


async def find_active_by_user_and_project(
    user_id: str, project_id: str, session: AsyncSession | None = None
) -> UserWorktree | None:
    async with db_conn.transaction(session) as s:
        result = await s.execute(
            select(UserWorktree).where(
                UserWorktree.project_id == project_id,
                UserWorktree.user_id == user_id,
                UserWorktree.status == "active",
            )
        )
        return result.scalars().first()


async def add(worktree: UserWorktree, session: AsyncSession | None = None) -> UserWorktree:
    async with db_conn.transaction(session) as s:
        s.add(worktree)
        await s.flush()
        await s.refresh(worktree)
        return worktree


def delete(worktree: UserWorktree, session: AsyncSession) -> None:
    session.delete(worktree)
