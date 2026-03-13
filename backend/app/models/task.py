"""Task-related ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, JSON, String, Text, TIMESTAMP
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
    
    # 담당 유저 아이디
    assigned_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    
    # 제목
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # 설명
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    acceptance_criteria: Mapped[Optional[Any]] = mapped_column(JSON)
    
    # 중요도
    priority: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="task_priority_enum"),
        default="medium",
    )
    
    # 복잡도
    complexity: Mapped[str] = mapped_column(
        Enum("trivial", "low", "medium", "high", "very_high", name="task_complexity_enum"),
        default="medium",
    )
    
    # task 상태
    status: Mapped[str] = mapped_column(
        Enum(
            'plan_reviewing', 'confirmed', 'coding', 'reviewing', 'done', 'failed',
            name="task_status_enum",
        ),
        default="plan_reviewing",
    )
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    auto_approve: Mapped[bool] = mapped_column(Boolean, default=False)
    
    auto_approve_config: Mapped[Optional[Any]] = mapped_column(JSON)
    
    git_commit_hash: Mapped[Optional[str]] = mapped_column(String(40))
    
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
    assigned_user: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_tasks")
    steps: Mapped[list["TaskStep"]] = relationship(
        "TaskStep",
        back_populates="task",
        cascade="all, delete-orphan",
    )


class TaskStep(Base):
    __tablename__ = "task_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_type: Mapped[str] = mapped_column(
        Enum("plan", "plan_review", "code", "review", name="step_type_enum"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "in_progress", "completed", "rejected", "skipped", name="step_status_enum"),
        default="pending",
    )
    content: Mapped[Optional[str]] = mapped_column(Text)
    agent_messages: Mapped[Optional[Any]] = mapped_column(JSON)
    session_id: Mapped[Optional[str]] = mapped_column(String(255))
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )

    task: Mapped["Task"] = relationship("Task", back_populates="steps")
    code_changes: Mapped[list["CodeChange"]] = relationship(
        "CodeChange",
        back_populates="task_step",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="task_step",
        cascade="all, delete-orphan",
    )


class CodeChange(Base):
    __tablename__ = "code_changes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    task_step_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("task_steps.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    change_type: Mapped[str] = mapped_column(
        Enum("create", "modify", "delete", name="change_type_enum"),
        nullable=False,
    )
    diff_content: Mapped[Optional[str]] = mapped_column(Text)
    before_content: Mapped[Optional[str]] = mapped_column(Text)
    after_content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )

    task_step: Mapped["TaskStep"] = relationship("TaskStep", back_populates="code_changes")


class Review(Base):
    __tablename__ = "reviews"

    # 아이디
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    
    # Task step 아이디
    task_step_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("task_steps.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    reviewer_type: Mapped[str] = mapped_column(
        Enum("human", "auto", name="reviewer_type_enum"),
        nullable=False,
    )
    
    result: Mapped[str] = mapped_column(
        Enum("approved", "rejected", "revision_requested", name="review_result_enum"),
        nullable=False,
    )
    
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    auto_conditions: Mapped[Optional[Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )

    task_step: Mapped["TaskStep"] = relationship("TaskStep", back_populates="reviews")
