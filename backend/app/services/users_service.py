"""User 서비스 레이어 — 비즈니스 로직."""

from app.exceptions.business import BusinessException, ConflictException, NotFoundException
from app.models import User
from app.schemas import UserCreate
from app.repositories import user_repository
from app.utils.db_handler_sqlalchemy import db_conn


async def list_users() -> list[User]:
    try:
        return await user_repository.find_all()
    except Exception as e:
        raise BusinessException(f"Failed to retrieve users: {e}")


async def get_user(user_id: str) -> User:
    try:
        user = await user_repository.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user
    except Exception as e:
        raise BusinessException(f"Failed to retrieve user: {e}")


async def create_user(body: UserCreate) -> User:
    try:
        async with db_conn.transaction() as session:
            existing = await user_repository.find_by_username(body.username, session)
            if existing:
                raise ConflictException("Username already exists")
            user = User(**body.model_dump())
            return await user_repository.add(user, session)
    except Exception as e:
        raise BusinessException(f"Failed to create user: {e}")
