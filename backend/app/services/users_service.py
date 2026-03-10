"""User 서비스 레이어 — DB 조작 및 비즈니스 로직."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import UserCreate


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.username).all()


def get_user(user_id: str, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def create_user(body: UserCreate, db: Session) -> User:
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(**body.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
