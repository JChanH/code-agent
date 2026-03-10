"""SecurityProfile repository — DB 쿼리 전담."""

from sqlalchemy.orm import Session

from app.models import SecurityProfile


def add(profile: SecurityProfile, db: Session) -> None:
    db.add(profile)
