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

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        Enum("document", "image", "text", "url", name="spec_source_type_enum"),
        nullable=False,
    )
    source_path: Mapped[Optional[str]] = mapped_column(String(500))
    raw_content: Mapped[Optional[str]] = mapped_column(Text)
    analysis_result: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum("uploaded", "analyzing", "analyzed", "confirmed", name="spec_status_enum"),
        default="uploaded",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="specs")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="spec")
