# FastAPI Backend 구조 가이드라인

> 이 문서는 `new_label_ai` 프로젝트의 실제 코드베이스를 기준으로 작성된 FastAPI 백엔드 아키텍처 가이드라인입니다.
> 새로운 프로젝트 시작 시 이 구조를 기준으로 삼아 일관된 코드베이스를 유지하세요.

---

## 목차

1. [디렉토리 구조](#1-디렉토리-구조)
2. [레이어 아키텍처](#2-레이어-아키텍처)
3. [진입점 (main.py)](#3-진입점-mainpy)
4. [설정 관리 (core/config.py)](#4-설정-관리-coreconfigpy)
5. [라이프사이클 관리 (core/lifespan.py)](#5-라이프사이클-관리-corelifespanpy)
6. [데이터베이스 모델 (models/db/)](#6-데이터베이스-모델-modelsdb)
7. [DTO / 요청·응답 모델 (models/)](#7-dto--요청응답-모델-models)
8. [레포지토리 레이어 (repository/)](#8-레포지토리-레이어-repository)
9. [서비스 레이어 (service/)](#9-서비스-레이어-service)
10. [라우터 레이어 (router/)](#10-라우터-레이어-router)
11. [공통 응답 포맷 (models/result.py)](#11-공통-응답-포맷-modelsresultpy)
12. [예외 처리 (exceptions.py)](#12-예외-처리-exceptionspy)
13. [인증 / 인가 패턴](#13-인증--인가-패턴)
14. [유틸리티 레이어 (utils/)](#14-유틸리티-레이어-utils)
15. [캐시 레이어 (cache/)](#15-캐시-레이어-cache)
16. [미들웨어](#16-미들웨어)
17. [환경변수 및 .env 관리](#17-환경변수-및-env-관리)
18. [테스트 구조 (tests/)](#18-테스트-구조-tests)
19. [네이밍 컨벤션](#19-네이밍-컨벤션)
20. [의존성 주입 패턴](#20-의존성-주입-패턴)

---

## 1. 디렉토리 구조

```
backend/
├── main.py                          # FastAPI 앱 초기화, 미들웨어, 라우터 등록
├── exceptions.py                    # 전체 프로젝트 커스텀 예외 정의
├── requirements.txt                 # Python 의존성
├── .env                             # 환경변수 (git ignore 필수)
│
├── core/                            # 앱 핵심 설정
│   ├── config.py                    # Settings 클래스 (환경변수 로드)
│   ├── constants.py                 # 전역 상수
│   ├── lifespan.py                  # 앱 시작/종료 훅
│   └── user_dependencies.py        # 인증 DI (get_current_user)
│
├── models/                          # 모든 데이터 모델
│   ├── db/                          # SQLAlchemy ORM 모델 (테이블 정의)
│   │   ├── base.py                  # SQLAlchemy Base 클래스
│   │   ├── user.py
│   │   ├── product.py
│   │   └── ...
│   ├── result.py                    # 공통 ApiResponse<T> 래퍼
│   └── {domain}_model/             # 도메인별 요청/응답 Pydantic 모델
│
├── repository/                      # 데이터 접근 레이어 (DB 쿼리)
│   ├── user_repo.py
│   ├── product_repo.py
│   └── ...
│
├── service/                         # 비즈니스 로직 레이어
│   ├── __init__.py
│   ├── user_service.py
│   ├── product_service.py
│   └── ...
│
├── router/                          # API 엔드포인트 정의
│   ├── __init__.py                  # 라우터 통합 등록
│   ├── user_router.py
│   ├── product_router.py
│   └── ...
│
├── cache/                           # 캐시 레이어 (Redis)
│   ├── base.py                      # 캐시 기본 추상화
│   ├── auth_cache.py               # 인증 관련 캐시
│   └── user_cache.py               # 사용자 관련 캐시
│
├── utils/                           # 유틸리티 도구
│   ├── db_handler_sqlalchemy.py    # DB 연결 & 트랜잭션 관리
│   ├── redis_handler.py             # Redis 클라이언트 래퍼
│   ├── jwt_handler.py               # JWT 생성/검증
│   ├── email_handler.py             # 이메일 발송
│   └── file_storage.py             # 파일 업로드/저장
│
├── dtos/                            # 특수 목적 DTO (도메인 간 공유)
│   └── {domain}/
│
├── tests/                           # 테스트 파일
│   ├── test_user.py
│   └── ...
│
└── uploads/                         # 정적 파일 저장소 (로컬 개발)
```

**핵심 원칙:**
- 각 디렉토리는 단 하나의 책임을 가진다
- `models/db/` ↔ `repository/` ↔ `service/` ↔ `router/` 순서로만 의존한다
- 역방향 의존(예: repository가 service를 import)은 절대 금지

---

## 2. 레이어 아키텍처

```
요청(Request)
    │
    ▼
[router/]          ← 엔드포인트 정의, 입력 검증, DI
    │
    ▼
[service/]         ← 비즈니스 로직, 트랜잭션 조율
    │
    ▼
[repository/]      ← DB 쿼리, ORM 조작
    │
    ▼
[models/db/]       ← 테이블 구조 정의
    │
    ▼
[DB (MySQL)]
```

각 레이어의 역할:

| 레이어 | 역할 | 금지 사항 |
|--------|------|----------|
| router | 경로 정의, 파라미터 수신, 응답 포맷 | 비즈니스 로직, DB 직접 접근 |
| service | 비즈니스 규칙, 트랜잭션 관리 | DB 쿼리 직접 작성 |
| repository | DB CRUD 쿼리 | 비즈니스 판단, 예외 변환 |
| models/db | 테이블 컬럼 정의 | 비즈니스 메서드 |

---

## 3. 진입점 (main.py)

`main.py`는 앱 조립만 담당합니다. 비즈니스 로직을 직접 포함하지 않습니다.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.lifespan import lifespan
from router import main_router, user_router, v2_router

app = FastAPI(
    title="My Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# 1. CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 전역 예외 핸들러
@app.exception_handler(BusinessException)
async def business_exception_handler(request, exc):
    ...

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    ...

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    ...

# 3. 라우터 등록
app.include_router(user_router)
app.include_router(v2_router)  # /api/v2 prefix

# 5. 정적 파일
app.mount("/static", StaticFiles(directory="uploads"), name="static")
```

**체크리스트:**
- [ ] 미들웨어 등록 순서: CORS → 커스텀 미들웨어
- [ ] 예외 핸들러: 구체적인 예외 → 일반 예외 순서
- [ ] 라우터 등록은 `router/__init__.py`에서 관리
- [ ] 정적 파일 경로는 `uploads/` 디렉토리

---

## 4. 설정 관리 (core/config.py)

모든 환경변수는 `Settings` 클래스 하나에서 관리합니다.

```python
import os

class Settings:
    # 앱 기본 설정
    APP_NAME: str = "My Backend"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "DEVELOPMENT")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # DB
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")

    @property
    def DB_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # Email
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")

settings = Settings()  # 싱글톤 인스턴스
```

**규칙:**
- `settings` 싱글톤 인스턴스를 전체 프로젝트에서 import하여 사용
- 하드코딩된 설정값은 `constants.py`에 위치
- 절대로 `os.getenv()`를 라우터나 서비스에서 직접 호출하지 않음

---

## 5. 라이프사이클 관리 (core/lifespan.py)

앱 시작/종료 시 리소스 초기화 및 정리를 담당합니다.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from utils.db_handler_sqlalchemy import db_conn
from utils.redis_handler import redis_conn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # === 시작 시 ===
    await db_conn.ping()       # DB 연결 확인
    await redis_conn.ping()    # Redis 연결 확인
    print("Application started")

    yield  # 앱 실행

    # === 종료 시 (역순으로) ===
    await redis_conn.close()
    await db_conn.dispose()
    print("Application stopped")
```

**원칙:**
- 연결 풀(Connection Pool)은 여기서 초기화
- 백그라운드 스케줄러가 있다면 여기서 시작/중지
- 시작 순서와 반대로 종료

---

## 6. 데이터베이스 모델 (models/db/)

### 6.1 Base 클래스

```python
# models/db/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### 6.2 모델 정의 패턴

```python
# models/db/user.py
from sqlalchemy import BigInteger, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from models.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 공통 타임스탬프 (모든 테이블에 포함)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship
    products: Mapped[list["Product"]] = relationship("Product", back_populates="user")
```

**규칙:**
- `Mapped[type]` 타입 힌트를 사용하여 IDE 지원 활용
- Nullable 컬럼은 `Mapped[str | None]`으로 명시
- 외래키 컬럼명은 `{참조테이블_단수}_{참조컬럼}` 패턴 (예: `user_id`)

### 6.3 Enum 사용 패턴

```python
from sqlalchemy import Enum as SAEnum
import enum

class ProductStatus(str, enum.Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"

class Product(Base):
    status: Mapped[ProductStatus] = mapped_column(
        SAEnum(ProductStatus), default=ProductStatus.ONGOING
    )
```

---

## 7. DTO / 요청·응답 모델 (models/)

### 7.1 디렉토리 구조

```
models/
├── db/                        # ORM 모델 (위에서 설명)
├── result.py                  # 공통 응답 래퍼
├── user_model/
│   ├── __init__.py
│   ├── request.py             # 요청 Pydantic 모델
│   └── response.py            # 응답 Pydantic 모델
└── product_model/
    ├── __init__.py
    ├── request.py
    └── response.py
```

### 7.2 요청 모델 패턴

```python
# models/user_model/request.py
from pydantic import BaseModel, EmailStr, field_validator

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다")
        return v

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
```

### 7.3 응답 모델 패턴

```python
# models/user_model/response.py
from pydantic import BaseModel
from datetime import datetime

class UserInfoResponse(BaseModel):
    id: int
    email: str
    name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}  # ORM 모델에서 직접 변환 허용

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfoResponse
```

**규칙:**
- 요청 모델명: `{동작}{도메인}Request` (예: `LoginRequest`, `CreateProductRequest`)
- 응답 모델명: `{도메인}{내용}Response` (예: `UserInfoResponse`, `ProductListResponse`)
- ORM 객체를 응답 모델로 변환할 때는 `model_config = {"from_attributes": True}` 사용
- 절대로 ORM 모델을 API 응답에 직접 반환하지 않음

---

## 8. 레포지토리 레이어 (repository/)

DB 쿼리만 담당합니다. 비즈니스 판단을 포함하지 않습니다.

```python
# repository/user_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.db.user import User

class UserRepository:

    @staticmethod
    async def find_by_email(session: AsyncSession, email: str) -> User | None:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_by_id(session: AsyncSession, user_id: int) -> User | None:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> User:
        user = User(**kwargs)
        session.add(user)
        await session.flush()  # ID 할당을 위해 flush (commit은 service에서)
        return user

    @staticmethod
    async def update_by_id(session: AsyncSession, user_id: int, **kwargs) -> None:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**kwargs)
        )

    @staticmethod
    async def find_all_by_user_id(
        session: AsyncSession,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[User]:
        result = await session.execute(
            select(User)
            .where(User.user_id == user_id)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
```

**규칙:**
- 모든 메서드는 `@staticmethod` + `session`을 첫 번째 파라미터로 받음
- 트랜잭션 `commit`은 절대 레포지토리에서 하지 않음 (service 역할)
- 복잡한 join은 레포지토리에서 처리 가능
- 메서드명: `find_`, `create_`, `update_`, `delete_` 접두어 사용
- 단일 조회: `find_by_{field}` → `T | None` 반환
- 복수 조회: `find_all_by_{field}` → `list[T]` 반환

---

## 9. 서비스 레이어 (service/)

비즈니스 로직과 트랜잭션을 관리합니다.

```python
# service/user_service.py
import bcrypt
from utils.db_handler_sqlalchemy import db_conn
from utils.jwt_handler import create_access_token, create_refresh_token
from repository.user_repo import UserRepository
from models.user_model.request import LoginRequest
from models.user_model.response import LoginResponse, UserInfoResponse
from exceptions import (
    UserNotFoundException,
    InvalidPasswordException,
    InactiveUserException,
)


@staticmethod
async def process_login(request: LoginRequest) -> LoginResponse:
    async with db_conn.transaction() as session:
        # 1. 사용자 조회
        user = await UserRepository.find_by_email(session, request.email)
        if not user:
            raise UserNotFoundException("존재하지 않는 이메일입니다")

        # 2. 비밀번호 검증
        if not bcrypt.checkpw(request.password.encode(), user.password_hash.encode()):
            raise InvalidPasswordException("비밀번호가 올바르지 않습니다")

        # 3. 계정 상태 확인
        if not user.is_active:
            raise InactiveUserException("비활성화된 계정입니다")

        # 4. 토큰 발급
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id)

        # 5. Refresh 토큰 Redis 저장
        await auth_cache.set_refresh_token(user.id, refresh_token)

        return LoginResponse(
            access_token=access_token,
            user=UserInfoResponse.model_validate(user),
        )

@staticmethod
async def process_signup(request: SignupRequest) -> UserInfoResponse:
    async with db_conn.transaction() as session:
        # 중복 이메일 체크
        existing = await UserRepository.find_by_email(session, request.email)
        if existing:
            raise DuplicateEmailException("이미 사용 중인 이메일입니다")

        # 비밀번호 해싱
        password_hash = bcrypt.hashpw(
            request.password.encode(), bcrypt.gensalt()
        ).decode()

        # 사용자 생성
        user = await UserRepository.create(
            session,
            email=request.email,
            password_hash=password_hash,
            name=request.name,
        )

        return UserInfoResponse.model_validate(user)
```

**규칙:**
- 모든 비즈니스 로직은 서비스에 위치
- 하나의 서비스 메서드 = 하나의 유스케이스
- 트랜잭션은 `async with db_conn.transaction() as session:` 블록으로 관리
- 예외는 서비스에서 raise, 라우터에서 catch하지 않음 (전역 핸들러 사용)
- 여러 레포지토리를 조율하는 것은 서비스의 역할
- 메서드명: `process_{동작}_{도메인}` (예: `process_login`, `process_create_product`)

---

## 10. 라우터 레이어 (router/)

### 10.1 라우터 정의

```python
# router/user_router.py
from fastapi import APIRouter, Depends, Response
from core.user_dependencies import get_current_user, CurrentUser
from service.user_service import UserService
from models.user_model.request import LoginRequest, SignupRequest
from models.result import ApiResponse

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
) -> ApiResponse[LoginResponse]:
    result = await UserService.process_login(request)

    # Refresh 토큰을 HttpOnly 쿠키로 설정
    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7일
    )

    return ApiResponse.success(result)

@router.get("/info")
async def get_user_info(
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[UserInfoResponse]:
    result = await UserService.get_user_info(current_user.user_id)
    return ApiResponse.success(result)
```

### 10.2 라우터 통합 등록 (`router/__init__.py`)

```python
# router/__init__.py
from fastapi import APIRouter
from .user_router import router as user_router
from .product_router import router as product_router

# v2 라우터 그룹
v2_router = APIRouter(prefix="/api/v2")
v2_router.include_router(product_router)

__all__ = ["user_router", "v2_router"]
```

**규칙:**
- 라우터는 입력 수신 + 서비스 호출 + 응답 반환만 담당
- 비즈니스 로직을 라우터에 직접 작성하지 않음
- 모든 응답은 `ApiResponse.success(data)` 래퍼 사용
- 인증이 필요한 엔드포인트는 `Depends(get_current_user)` 추가
- `prefix`와 `tags`를 반드시 지정

### 10.3 API 버전 관리

```python
# 버전별 라우터 분리
v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

# 호환성 유지: v1 엔드포인트는 deprecated 처리
@v1_router.get("/product", deprecated=True)
async def get_product_v1():
    ...
```

---

## 11. 공통 응답 포맷 (models/result.py)

모든 API 응답은 동일한 포맷을 사용합니다.

```python
# models/result.py
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar("T")

class ErrorDetail(BaseModel):
    message: str
    code: str | None = None
    path: str | None = None

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def success(cls, data: T) -> "ApiResponse[T]":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, message: str, code: str = None) -> "ApiResponse[None]":
        return cls(
            success=False,
            error=ErrorDetail(message=message, code=code)
        )
```

**응답 예시:**

성공:
```json
{
  "success": true,
  "data": { "id": 1, "email": "user@example.com" },
  "error": null
}
```

실패:
```json
{
  "success": false,
  "data": null,
  "error": {
    "message": "존재하지 않는 이메일입니다",
    "code": "USER_NOT_FOUND",
    "path": "/user/login"
  }
}
```

---

## 12. 예외 처리 (exceptions.py)

### 12.1 예외 계층 구조

```python
# exceptions.py

# === 기본 예외 ===
class BusinessException(Exception):
    """모든 비즈니스 예외의 기본 클래스"""
    def __init__(self, message: str, status_code: int = 400, code: str = None):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)

# === 인증 예외 (401) ===
class InvalidTokenException(BusinessException):
    def __init__(self, message: str = "유효하지 않은 토큰입니다"):
        super().__init__(message, status_code=401, code="INVALID_TOKEN")

class TokenExpiredException(BusinessException):
    def __init__(self, message: str = "만료된 토큰입니다"):
        super().__init__(message, status_code=401, code="TOKEN_EXPIRED")

class MissingTokenException(BusinessException):
    def __init__(self, message: str = "토큰이 필요합니다"):
        super().__init__(message, status_code=401, code="MISSING_TOKEN")

# === 권한 예외 (403) ===
class ForbiddenException(BusinessException):
    def __init__(self, message: str = "접근 권한이 없습니다"):
        super().__init__(message, status_code=403, code="FORBIDDEN")

# === 비즈니스 예외 (400) ===
class UserNotFoundException(BusinessException):
    def __init__(self, message: str = "사용자를 찾을 수 없습니다"):
        super().__init__(message, status_code=400, code="USER_NOT_FOUND")

class DuplicateEmailException(BusinessException):
    def __init__(self, message: str = "이미 사용 중인 이메일입니다"):
        super().__init__(message, status_code=400, code="DUPLICATE_EMAIL")

class InvalidPasswordException(BusinessException):
    def __init__(self, message: str = "비밀번호가 올바르지 않습니다"):
        super().__init__(message, status_code=400, code="INVALID_PASSWORD")

# === 서버 예외 (500) ===
class ExternalAPIException(BusinessException):
    def __init__(self, message: str = "외부 API 호출에 실패했습니다"):
        super().__init__(message, status_code=500, code="EXTERNAL_API_ERROR")
```

### 12.2 전역 예외 핸들러 등록 (main.py)

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from exceptions import BusinessException
from models.result import ApiResponse

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.fail(
            message=exc.message,
            code=exc.code,
        ).model_dump(),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=ApiResponse.fail(
            message="요청 값이 올바르지 않습니다",
            code="VALIDATION_ERROR",
        ).model_dump(),
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # 예상치 못한 오류는 반드시 로깅
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ApiResponse.fail(
            message="서버 내부 오류가 발생했습니다",
            code="INTERNAL_SERVER_ERROR",
        ).model_dump(),
    )
```

**규칙:**
- 모든 커스텀 예외는 `BusinessException`을 상속
- 예외 클래스 이름으로 무슨 문제인지 명확하게 표현
- `status_code`와 `code`를 기본값으로 설정하여 서비스 코드를 간결하게 유지
- 예외를 catch하여 다시 raise할 때는 새로운 예외로 변환 (`raise NewException() from exc`)

---

## 13. 인증 / 인가 패턴

### 13.1 JWT 핸들러 (utils/jwt_handler.py)

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from core.config import settings

def create_access_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
```

### 13.2 인증 의존성 (core/user_dependencies.py)

```python
from dataclasses import dataclass
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt_handler import verify_token
from exceptions import InvalidTokenException, MissingTokenException

security = HTTPBearer(auto_error=False)

@dataclass
class CurrentUser:
    user_id: int
    email: str

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    if not credentials:
        raise MissingTokenException()

    payload = verify_token(credentials.credentials)
    if not payload:
        raise InvalidTokenException()

    if payload.get("type") != "access":
        raise InvalidTokenException()

    return CurrentUser(
        user_id=int(payload["sub"]),
        email=payload["email"],
    )
```

### 13.3 토큰 저장 전략

| 토큰 | 저장 위치 | 만료 | 비고 |
|------|-----------|------|------|
| Access Token | Response Body | 30분 | 클라이언트가 메모리에 보관 |
| Refresh Token | HttpOnly Cookie | 7일 | `secure=True`, `samesite=lax` |
| Refresh Token (서버) | Redis | 7일 | 로그아웃/탈취 시 무효화용 |

---

## 14. 유틸리티 레이어 (utils/)

### 14.1 DB 핸들러 (utils/db_handler_sqlalchemy.py)

```python
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings

class DBManager:
    def __init__(self, db_url: str):
        self._engine = create_async_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False,  # 운영환경에서는 False
        )
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,  # commit 후에도 ORM 객체 사용 가능
        )

    @asynccontextmanager
    async def transaction(self, session: AsyncSession = None):
        """트랜잭션 컨텍스트 매니저"""
        if session:
            # 이미 세션이 있으면 재사용 (중첩 트랜잭션)
            yield session
            return

        async with self._session_maker() as session:
            async with session.begin():
                try:
                    yield session
                    # 정상 종료 시 자동 commit
                except Exception:
                    await session.rollback()
                    raise

    async def ping(self) -> None:
        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        await self._engine.dispose()

# 싱글톤 인스턴스
db_conn = DBManager(settings.DB_URL)
```

### 14.2 Redis 핸들러 (utils/redis_handler.py)

```python
import json
from typing import Any
from redis.asyncio import Redis
from core.config import settings

class RedisHandler:
    def __init__(self):
        self._client = Redis.from_url(
            url=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
            decode_responses=True,
            socket_timeout=3.0,
            health_check_interval=30,
        )

    async def set_json(self, key: str, value: Any, ex: int = None) -> None:
        await self._client.set(key, json.dumps(value), ex=ex)

    async def get_json(self, key: str) -> Any | None:
        data = await self._client.get(key)
        return json.loads(data) if data else None

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._client.exists(key) > 0

    async def ping(self) -> None:
        await self._client.ping()

    async def close(self) -> None:
        await self._client.aclose()

# 싱글톤 인스턴스
redis_conn = RedisHandler()
```

**Redis 키 네이밍 규칙:**
```
{서비스명}:{도메인}:{식별자}:{용도}

예시:
user:auth:refresh_token:{user_id}      # Refresh 토큰
user:email:verification:{email}        # 이메일 인증 코드
user:email:attempts:{email}            # 인증 시도 횟수
product:cache:{product_id}             # 상품 캐시
```

---

## 15. 캐시 레이어 (cache/)

Redis 키 관리를 캐시 레이어에서 추상화합니다.

```python
# cache/auth_cache.py
from utils.redis_handler import redis_conn
from core.config import settings

class AuthCache:
    REFRESH_TOKEN_KEY = "user:auth:refresh_token:{user_id}"
    EMAIL_VERIFY_KEY = "user:email:verification:{email}"
    EMAIL_ATTEMPTS_KEY = "user:email:attempts:{email}"

    async def set_refresh_token(self, user_id: int, token: str) -> None:
        key = self.REFRESH_TOKEN_KEY.format(user_id=user_id)
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        await redis_conn.set_json(key, token, ex=ttl)

    async def get_refresh_token(self, user_id: int) -> str | None:
        key = self.REFRESH_TOKEN_KEY.format(user_id=user_id)
        return await redis_conn.get_json(key)

    async def delete_refresh_token(self, user_id: int) -> None:
        key = self.REFRESH_TOKEN_KEY.format(user_id=user_id)
        await redis_conn.delete(key)

    async def set_email_verification(self, email: str, code: str) -> None:
        key = self.EMAIL_VERIFY_KEY.format(email=email)
        await redis_conn.set_json(key, code, ex=300)  # 5분 TTL

    async def get_email_verification(self, email: str) -> str | None:
        key = self.EMAIL_VERIFY_KEY.format(email=email)
        return await redis_conn.get_json(key)

auth_cache = AuthCache()  # 싱글톤 인스턴스
```

---

## 16. 미들웨어

**미들웨어 등록 순서 (중요):**
```
1. CORSMiddleware          (먼저 처리, preflight 요청 처리)
2. Exception Handler       (예외를 응답으로 변환)
```

---

## 17. 환경변수 및 .env 관리

### 17.1 .env 파일 구조

```bash
# .env (git에 포함하지 않음)

# === App ===
ENVIRONMENT=DEVELOPMENT
BASE_URL=http://localhost:8000

# === Database ===
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=mydb

# === Redis ===
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# === JWT ===
JWT_SECRET_KEY=your-very-long-random-secret-key

# === Email ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=your_app_password

# === External APIs ===
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 17.2 .env.example 파일 (git에 포함)

```bash
# .env.example (git에 포함 - 값은 비워둠)
ENVIRONMENT=DEVELOPMENT
BASE_URL=http://localhost:8000
DB_HOST=localhost
DB_PORT=3306
DB_USER=
DB_PASSWORD=
DB_NAME=
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
JWT_SECRET_KEY=
```

**규칙:**
- `.env`는 반드시 `.gitignore`에 추가
- `.env.example`은 key만 포함하여 git에 커밋
- 운영 환경 시크릿은 환경변수나 시크릿 매니저로 관리

---

## 18. 테스트 구조 (tests/)

```
tests/
├── conftest.py              # 공통 fixture (DB, 클라이언트, 인증)
├── unit/
│   ├── test_user_service.py
│   └── test_jwt_handler.py
└── integration/
    ├── test_user_api.py
    └── test_product_api.py
```

### 18.1 conftest.py 패턴

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from main import app
from models.db.base import Base

TEST_DB_URL = "mysql+aiomysql://root:password@localhost:3306/test_db"

@pytest_asyncio.fixture(scope="session")
async def test_db():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest_asyncio.fixture
async def auth_headers(client):
    """인증이 필요한 테스트용 헤더"""
    response = await client.post("/user/login", json={
        "email": "test@example.com",
        "password": "Test1234!"
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### 18.2 서비스 단위 테스트 패턴

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import AsyncMock, patch
from service.user_service import UserService
from exceptions import UserNotFoundException

@pytest.mark.asyncio
async def test_login_user_not_found():
    with patch("service.user_service.UserRepository.find_by_email", return_value=None):
        with pytest.raises(UserNotFoundException):
            await UserService.process_login(LoginRequest(
                email="noone@example.com",
                password="password"
            ))
```

---

## 19. 네이밍 컨벤션

### 19.1 파일명

| 대상 | 규칙 | 예시 |
|------|------|------|
| 라우터 | `{도메인}_router.py` | `user_router.py` |
| 서비스 | `{도메인}_service.py` | `user_service.py` |
| 레포지토리 | `{도메인}_repo.py` | `user_repo.py` |
| DB 모델 | `{단수명}.py` | `user.py`, `product.py` |
| 요청 모델 | `request.py` (모델 폴더 내) | `models/user_model/request.py` |
| 응답 모델 | `response.py` (모델 폴더 내) | `models/user_model/response.py` |
| 캐시 | `{도메인}_cache.py` | `auth_cache.py` |

### 19.2 클래스명

| 대상 | 규칙 | 예시 |
|------|------|------|
| DB 모델 | PascalCase 단수 | `User`, `Product` |
| 요청 모델 | `{동작}{도메인}Request` | `LoginRequest`, `CreateProductRequest` |
| 응답 모델 | `{도메인}{내용}Response` | `UserInfoResponse`, `ProductListResponse` |
| 서비스 | `{도메인}Service` | `UserService`, `ProductService` |
| 레포지토리 | `{도메인}Repository` | `UserRepository`, `ProductRepository` |
| 예외 | `{상황}Exception` | `UserNotFoundException`, `DuplicateEmailException` |

### 19.3 메서드명

| 대상 | 규칙 | 예시 |
|------|------|------|
| 서비스 | `process_{동작}_{도메인}` | `process_login`, `process_create_product` |
| 레포지토리 단일 조회 | `find_by_{field}` | `find_by_email`, `find_by_id` |
| 레포지토리 복수 조회 | `find_all_by_{field}` | `find_all_by_user_id` |
| 레포지토리 생성 | `create` | `create` |
| 레포지토리 수정 | `update_by_{field}` | `update_by_id` |
| 레포지토리 삭제 | `delete_by_{field}` | `delete_by_id` |

### 19.4 API 경로

```
GET    /api/v2/{resource}           # 목록 조회
GET    /api/v2/{resource}/{id}      # 단일 조회
POST   /api/v2/{resource}          # 생성
PUT    /api/v2/{resource}/{id}      # 전체 수정
PATCH  /api/v2/{resource}/{id}      # 부분 수정
DELETE /api/v2/{resource}/{id}      # 삭제

# 특수 동작
POST   /user/login                  # 로그인
POST   /user/logout                 # 로그아웃
POST   /user/refresh                # 토큰 갱신
```

---

## 20. 의존성 주입 패턴

FastAPI의 `Depends`를 활용한 의존성 주입 패턴:

```python
# 1. 인증 의존성 (가장 흔한 패턴)
@router.get("/profile")
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
):
    ...

# 2. 공통 쿼리 파라미터 의존성
from fastapi import Query

class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        size: int = Query(default=20, ge=1, le=100),
    ):
        self.offset = (page - 1) * size
        self.limit = size

@router.get("/products")
async def list_products(
    current_user: CurrentUser = Depends(get_current_user),
    pagination: PaginationParams = Depends(),
):
    ...

# 3. 권한 체크 의존성
def require_admin(current_user: CurrentUser = Depends(get_current_user)):
    if not current_user.is_admin:
        raise ForbiddenException()
    return current_user

@router.delete("/admin/user/{user_id}")
async def delete_user(
    user_id: int,
    admin: CurrentUser = Depends(require_admin),
):
    ...
```

---

## 부록: 새 프로젝트 시작 체크리스트

### 초기 설정
- [ ] 디렉토리 구조 생성 (위 구조 그대로 복사)
- [ ] `.env` + `.env.example` 생성, `.gitignore`에 `.env` 추가
- [ ] `requirements.txt` 작성
- [ ] `core/config.py` → `Settings` 클래스 작성
- [ ] `models/db/base.py` → `Base` 클래스 생성
- [ ] `utils/db_handler_sqlalchemy.py` → `DBManager` + `db_conn` 싱글톤 생성
- [ ] `utils/redis_handler.py` → `RedisHandler` + `redis_conn` 싱글톤 생성
- [ ] `core/lifespan.py` → 시작/종료 훅 작성
- [ ] `models/result.py` → `ApiResponse<T>` 작성
- [ ] `exceptions.py` → 기본 예외 계층 작성
- [ ] `main.py` → 앱 조립 (미들웨어, 예외 핸들러, 라우터)

### 새 도메인 추가 시 순서
1. `models/db/{domain}.py` → DB 모델 정의
2. `models/{domain}_model/request.py` → 요청 모델 정의
3. `models/{domain}_model/response.py` → 응답 모델 정의
4. `repository/{domain}_repo.py` → DB 쿼리 작성
5. `service/{domain}_service.py` → 비즈니스 로직 작성
6. `router/{domain}_router.py` → 엔드포인트 정의
7. `router/__init__.py` → 라우터 등록
8. `exceptions.py` → 도메인 전용 예외 추가
9. `tests/` → 테스트 작성

### 코드 리뷰 체크리스트
- [ ] 레이어 의존성 방향이 올바른가? (router → service → repository)
- [ ] 비즈니스 로직이 service에만 있는가?
- [ ] DB 쿼리가 repository에만 있는가?
- [ ] 모든 응답이 `ApiResponse` 래퍼를 사용하는가?
- [ ] 예외가 `BusinessException`을 상속하는가?
- [ ] 인증이 필요한 엔드포인트에 `Depends(get_current_user)`가 있는가?
- [ ] 환경변수를 `settings`를 통해서만 접근하는가?
- [ ] ORM 모델이 직접 API 응답으로 반환되지 않는가?
- [ ] 트랜잭션이 `db_conn.transaction()` 컨텍스트 내에서 처리되는가?
