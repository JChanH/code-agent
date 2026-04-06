"""Project ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from app.models.common import generate_uuid


class Project(Base):
    __tablename__ = "projects"
    
    # 아이디
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    
    # 프로젝트 이름
    name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    
    # 프로젝트 설명
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # 프로젝트 타입
    project_type: Mapped[str] = mapped_column(
        Enum("new", "existing", name="project_type_enum"),
        nullable=False,
        default="existing",
    )
    
    # git url
    repo_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    
    # 로컬 경로
    local_repo_path: Mapped[str] = mapped_column(
        String(1000), nullable=False
    )
    
    # 메인 브랜치
    main_branch: Mapped[str] = mapped_column(
        String(100), default="main"
    )
    
    # 사용하는 프로그램 언어
    project_stack: Mapped[str] = mapped_column(
        Enum("python", "java", "other", name="project_stack_enum"),
        default="python",
    )
    
    # 사용라는 프레임 워크
    framework: Mapped[Optional[str]] = mapped_column(String(100))
    
    # 프로젝트 상태
    status: Mapped[str] = mapped_column(
        Enum("setup", "designing", "developing", "completed", name="project_status_enum"),
        default="setup",
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    specs: Mapped[list["Spec"]] = relationship(
        "Spec",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    settings: Mapped[list["Setting"]] = relationship(
        "Setting",
        back_populates="project",
        cascade="all, delete-orphan",
    )
