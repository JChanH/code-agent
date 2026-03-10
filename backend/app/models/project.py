"""Project ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.common import generate_uuid


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    repo_url: Mapped[Optional[str]] = mapped_column(String(500))
    main_branch: Mapped[str] = mapped_column(String(100), default="main")
    project_stack: Mapped[str] = mapped_column(
        Enum("python", "java", "other", name="project_stack_enum"),
        default="python",
    )
    framework: Mapped[Optional[str]] = mapped_column(String(100))
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
    worktrees: Mapped[list["UserWorktree"]] = relationship(
        "UserWorktree",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    security_profile: Mapped[Optional["SecurityProfile"]] = relationship(
        "SecurityProfile",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    settings: Mapped[list["Setting"]] = relationship(
        "Setting",
        back_populates="project",
        cascade="all, delete-orphan",
    )
