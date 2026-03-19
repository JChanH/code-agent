"""Runtime error ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Enum, Index, JSON, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base
from app.models.common import generate_uuid


class RuntimeErrorRecord(Base):
    __tablename__ = "runtime_errors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    error_code: Mapped[str] = mapped_column(String(50), nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)

    project_id: Mapped[str] = mapped_column(String(255), nullable=False)

    level: Mapped[str] = mapped_column(
        Enum("error", "warning", "critical", "info", name="runtime_error_level_enum"),
        nullable=False,
        default="error",
    )

    error_timestamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    metadata_: Mapped[Optional[Any]] = mapped_column("metadata", JSON)

    fix_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        Enum("pending", "analyzing", "analyzed", "resolved", "ignored", name="runtime_error_status_enum"),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )

    __table_args__ = (Index("ix_runtime_errors_project_id", "project_id"),)
