"""Spec ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from app.models.common import generate_uuid


class Spec(Base):
    __tablename__ = "specs"

    # 아이디
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    
    # 프로젝트 아이디
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # 외부 소스 타입
    source_type: Mapped[str] = mapped_column(
        Enum("document", "image", "text", name="spec_source_type_enum"),
        nullable=False,
    )
    
    # 소스 저장 경로
    source_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # 문자열 소스
    raw_content: Mapped[Optional[str]] = mapped_column(Text)
    
    # 분석 결과
    analysis_result: Mapped[Optional[str]] = mapped_column(Text)
    
    # 상태
    status: Mapped[str] = mapped_column(
        Enum("uploaded", "analyzing", "final_confirmed", name="spec_status_enum"),
        default="uploaded",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="specs")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="spec")
