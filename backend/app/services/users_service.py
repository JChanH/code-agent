"""User 서비스 레이어 — 비즈니스 로직."""

from sqlalchemy.orm import Session

from app.exceptions.business import ConflictException, NotFoundException
from app.models import User
from app.schemas import UserCreate
from app.repositories import user_repository


def list_users(db: Session) -> list[User]:
    return user_repository.find_all(db)


def get_user(user_id: str, db: Session) -> User:
    user = user_repository.find_by_id(user_id, db)
    if not user:
        raise NotFoundException("User not found")
    return user


def create_user(body: UserCreate, db: Session) -> User:
    existing = user_repository.find_by_username(body.username, db)
    if existing:
        raise ConflictException("Username already exists")
    user = User(**body.model_dump())
    user_repository.add(user, db)
    db.commit()
    db.refresh(user)
    return user
