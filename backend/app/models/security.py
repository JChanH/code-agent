"""Security profile ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Enum, ForeignKey, JSON, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from app.models.common import generate_uuid


class SecurityProfile(Base):
    __tablename__ = "security_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    stack_type: Mapped[str] = mapped_column(
        Enum("python", "java", "other", name="security_stack_enum"),
        nullable=False,
    )
    allowed_commands: Mapped[Any] = mapped_column(JSON, nullable=False)
    blocked_commands: Mapped[Any] = mapped_column(JSON, nullable=False)
    allowed_paths: Mapped[Optional[Any]] = mapped_column(JSON)
    blocked_paths: Mapped[Optional[Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="security_profile")
