"""
SQLAlchemy Base 클래스

모든 ORM 모델은 이 Base 클래스를 상속받아야 합니다.
테이블/인덱스/제약조건은 수동 DDL로 관리합니다.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    DeclarativeBase: SQLAlchemy ORM 모델 기본 클래스

    [NOTE]
        * 모든 테이블 모델은 해당 클래스 상속
        * ORM은 조회/저장만 담당하고, DDL은 수동으로 관리합니다.
    """
    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}