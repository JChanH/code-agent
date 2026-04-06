"""Task-related ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Enum, ForeignKey, JSON, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from app.models.common import generate_uuid


class Task(Base):
    __tablename__ = "tasks"

    # 아이디
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    
    # 프로젝트 아아디
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # 스펙 아이디
    spec_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("specs.id", ondelete="SET NULL"),
    )
    
    # 제목
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # 설명
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 인수 조건(테스트 확인용)
    acceptance_criteria: Mapped[Optional[Any]] = mapped_column(JSON)

    # 적용 순서
    implementation_steps: Mapped[Optional[Any]] = mapped_column(JSON)

    # code agent가 실제 수정/생성한 파일 목록 (review agent가 참조)
    files_to_modify: Mapped[Optional[Any]] = mapped_column(JSON)

    # task 상태
    status: Mapped[str] = mapped_column(
        Enum(
            'plan_reviewing', 'confirmed', 'coding', 'reviewing', 'done', 'failed',
            name="task_status_enum",
        ),
        default="plan_reviewing",
    )
    
    git_commit_hash: Mapped[Optional[str]] = mapped_column(String(40))

    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    spec: Mapped[Optional["Spec"]] = relationship("Spec", back_populates="tasks")

