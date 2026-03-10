"""User repository — DB 쿼리 전담."""

from sqlalchemy.orm import Session

from app.models import User


def find_all(db: Session) -> list[User]:
    return db.query(User).order_by(User.username).all()


def find_by_id(user_id: str, db: Session) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def find_by_username(username: str, db: Session) -> User | None:
    return db.query(User).filter(User.username == username).first()


def add(user: User, db: Session) -> None:
    db.add(user)
