"""User and worktree ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base
from app.models.common import generate_uuid


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )

    worktrees: Mapped[list["UserWorktree"]] = relationship(
        "UserWorktree",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="assigned_user",
    )


class UserWorktree(Base):
    __tablename__ = "user_worktrees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    worktree_path: Mapped[str] = mapped_column(String(500), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", "archived", name="worktree_status_enum"),
        default="active",
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

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="unique_user_project"),
    )

    user: Mapped["User"] = relationship("User", back_populates="worktrees")
    project: Mapped["Project"] = relationship("Project", back_populates="worktrees")
