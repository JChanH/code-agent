from __future__ import annotations

import json
import logging

from app.config import get_settings

from contextlib import asynccontextmanager  # 비동기 컨텍스트 메니저 사용 doco
from typing import AsyncGenerator  # 비동기 제너레이터
from functools import wraps  # 데코에서 함수 정보 유지

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import (
    AsyncSession,  # 비동기 세션 객체 타입
    async_sessionmaker,  # 세션을 찍어내는 factory
    create_async_engine,  # 비동기 db 엔진 생성
)
from sqlalchemy import text  # raw sql


class DBManager:
    def __init__(
        self,
        db_url: str,
        *,
        pool_size: int = 10,  # 최대로 유지하는 연결은 10개
        max_overflow: int = 20,  # 연결 몰리는 경우에는 20까지 임시 생성(나머지는 대기)
        pool_pre_ping: bool = True,  # 연결 사용전에 ping(실패하면 자동 재연결)
        pool_recycle: int = 3600,  # 1시간에 한번 연결 초기화(강제)
        echo: bool = False,  # 로그 출력 여부
    ):
        
        # 비동기 db 엔진 생성 및 재사용
        self._engine = create_async_engine(
            db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle,
            echo=False,
            json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
            # echo=settings.ENVIRONMENT == "development",
        )

        # 세션 생성 공장 
        self._session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,  # 세션 타입 명시
            expire_on_commit=False,  # commit 이후에 ORM 객체 데이터를 만료하지 않음
        )

    # ---------------------------
    # Transaction (Dependency)
    # ---------------------------
    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        """
        FastAPI Depends()로 사용하기 위한 세션 주입 함수

        정상 종료 시 자동으로 commit, 예외 발생 시 자동으로 rollback
        """
        session_id = id(self._session_maker)  # 세션 객체의 고유 ID
        logger.debug("[Session %s] 세션 생성 시작", session_id)

        async with self._session_maker() as session:
            try:
                logger.debug("[Session %s] 세션 열림 - DB 연결 준비 완료", session_id)
                yield session  # 코루틴만 일시 정지 상태
                await session.commit()  # 정상 종료 시 자동 commit
                logger.debug("[Session %s] 작업 완료 - 커밋 후 세션 정상 종료", session_id)
            except Exception as e:
                logger.error("[Session %s] 에러 발생: %s - 롤백 실행", session_id, e)
                await session.rollback()
                raise
            finally:
                logger.debug("[Session %s] 세션 닫힘 - 리소스 해제", session_id)

    # ---------------------------
    # Transaction (Context Manager)
    # ---------------------------
    @asynccontextmanager
    async def transaction(
        self,
        session: AsyncSession | None = None,
        *,
        nested: bool = True,
    ):
        """
        컨텍스트 매니저 방식 트랜잭션

        세션이 없으면 자동 생성, 있으면 기존 세션 사용 (중첩 트랜잭션 지원)

        Usage:
            # 세션 자동 생성
            async with db_manager.transaction() as session:
                await session.execute(...)

            # 기존 세션으로 중첩 트랜잭션
            async with db_manager.transaction(existing_session):
                await existing_session.execute(...)
        """
        # 세션이 없으면 새로 생성
        if session is None:
            async with self._session_maker() as new_session:
                async with new_session.begin():
                    yield new_session
        else:
            # 트랜젝션이 열려있나 확인
            in_tx = session.in_transaction()

            if nested and in_tx:
                async with session.begin_nested():  # savepoint
                    yield session
            else:
                async with session.begin():  # 일반
                    yield session

    # ---------------------------
    # Transaction (Decorator)
    # ---------------------------
    def transaction_decorator(self, read_only: bool = False):
        """
        데코레이터 방식 트랜잭션

        자동으로 세션을 생성하고 트랜잭션을 관리합니다.
        함수의 kwargs에 'session' 파라미터로 AsyncSession을 주입합니다.

        Args:
            read_only: 읽기 전용 트랜잭션 여부 (향후 확장용)

        Usage:
            @db_manager.transaction_decorator()
            async def save_data(data: dict, session: AsyncSession):
                await session.execute(...)

        Note:
            - 예외 발생 시 자동으로 rollback됩니다
            - 정상 종료 시 자동으로 commit됩니다
        """
        def deco(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async with self._session_maker() as session:
                    async with session.begin():
                        try:
                            # 기존 session 키워드 인자가 있으면 제거
                            kwargs.pop('session', None)

                            # 새로운 session을 kwargs에 주입
                            result = await func(*args, **kwargs, session=session)
                            return result

                        except Exception:
                            # rollback은 context manager에서 자동 처리
                            raise

            return wrapper
        return deco

    # ---------------------------
    # Healthcheck / Shutdown
    # ---------------------------
    async def ping(self) -> None:
        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        await self._engine.dispose()


db_conn = DBManager(db_url=get_settings().async_database_url)