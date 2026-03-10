"""SQLAlchemy ORM models matching the DB schema from the development plan."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Enum, Integer, Boolean,
    ForeignKey, JSON, TIMESTAMP, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ──────────────────────────────────────────────
# Project
# ──────────────────────────────────────────────
class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    repo_url = Column(String(500))
    main_branch = Column(String(100), default="main")
    project_stack = Column(
        Enum("python", "java", "other", name="project_stack_enum"),
        default="python",
    )
    framework = Column(String(100))
    status = Column(
        Enum("setup", "designing", "developing", "completed", name="project_status_enum"),
        default="setup",
    )
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    specs = relationship("Spec", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    worktrees = relationship("UserWorktree", back_populates="project", cascade="all, delete-orphan")
    security_profile = relationship("SecurityProfile", back_populates="project", uselist=False, cascade="all, delete-orphan")
    settings = relationship("Setting", back_populates="project", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# User & Worktree
# ──────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    worktrees = relationship("UserWorktree", back_populates="user", cascade="all, delete-orphan")
    assigned_tasks = relationship("Task", back_populates="assigned_user")


class UserWorktree(Base):
    __tablename__ = "user_worktrees"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    worktree_path = Column(String(500), nullable=False)
    branch_name = Column(String(255), nullable=False)
    status = Column(
        Enum("active", "inactive", "archived", name="worktree_status_enum"),
        default="active",
    )
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="unique_user_project"),
    )

    # Relationships
    user = relationship("User", back_populates="worktrees")
    project = relationship("Project", back_populates="worktrees")


# ──────────────────────────────────────────────
# Spec (Design Phase)
# ──────────────────────────────────────────────
class Spec(Base):
    __tablename__ = "specs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(
        Enum("document", "image", "text", "url", name="spec_source_type_enum"),
        nullable=False,
    )
    source_path = Column(String(500))
    raw_content = Column(Text)
    analysis_result = Column(Text)  # JSON string
    status = Column(
        Enum("uploaded", "analyzing", "analyzed", "confirmed", name="spec_status_enum"),
        default="uploaded",
    )
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="specs")
    tasks = relationship("Task", back_populates="spec")


# ──────────────────────────────────────────────
# Task
# ──────────────────────────────────────────────
class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    spec_id = Column(String(36), ForeignKey("specs.id", ondelete="SET NULL"))
    assigned_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    acceptance_criteria = Column(JSON)
    priority = Column(
        Enum("low", "medium", "high", "critical", name="task_priority_enum"),
        default="medium",
    )
    complexity = Column(
        Enum("trivial", "low", "medium", "high", "very_high", name="task_complexity_enum"),
        default="medium",
    )
    status = Column(
        Enum(
            "backlog", "planning", "plan_review",
            "coding", "reviewing", "done", "failed",
            name="task_status_enum",
        ),
        default="backlog",
    )
    dependencies = Column(JSON)  # [task_id, ...]
    sort_order = Column(Integer, default=0)
    auto_approve = Column(Boolean, default=False)
    auto_approve_config = Column(JSON)
    git_commit_hash = Column(String(40))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="tasks")
    spec = relationship("Spec", back_populates="tasks")
    assigned_user = relationship("User", back_populates="assigned_tasks")
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# Task Step (Plan / Code / Review)
# ──────────────────────────────────────────────
class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    step_type = Column(
        Enum("plan", "plan_review", "code", "review", name="step_type_enum"),
        nullable=False,
    )
    status = Column(
        Enum("pending", "in_progress", "completed", "rejected", "skipped", name="step_status_enum"),
        default="pending",
    )
    content = Column(Text)
    agent_messages = Column(JSON)
    session_id = Column(String(255))
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    task = relationship("Task", back_populates="steps")
    code_changes = relationship("CodeChange", back_populates="task_step", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="task_step", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# Code Change
# ──────────────────────────────────────────────
class CodeChange(Base):
    __tablename__ = "code_changes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_step_id = Column(String(36), ForeignKey("task_steps.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False)
    change_type = Column(
        Enum("create", "modify", "delete", name="change_type_enum"),
        nullable=False,
    )
    diff_content = Column(Text)
    before_content = Column(Text)
    after_content = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    task_step = relationship("TaskStep", back_populates="code_changes")


# ──────────────────────────────────────────────
# Review
# ──────────────────────────────────────────────
class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_step_id = Column(String(36), ForeignKey("task_steps.id", ondelete="CASCADE"), nullable=False)
    reviewer_type = Column(
        Enum("human", "auto", name="reviewer_type_enum"),
        nullable=False,
    )
    result = Column(
        Enum("approved", "rejected", "revision_requested", name="review_result_enum"),
        nullable=False,
    )
    feedback = Column(Text)
    auto_conditions = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    task_step = relationship("TaskStep", back_populates="reviews")


# ──────────────────────────────────────────────
# Security Profile
# ──────────────────────────────────────────────
class SecurityProfile(Base):
    __tablename__ = "security_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    stack_type = Column(
        Enum("python", "java", "other", name="security_stack_enum"),
        nullable=False,
    )
    allowed_commands = Column(JSON, nullable=False)
    blocked_commands = Column(JSON, nullable=False)
    allowed_paths = Column(JSON)
    blocked_paths = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="security_profile")


# ──────────────────────────────────────────────
# Settings
# ──────────────────────────────────────────────
class Setting(Base):
    __tablename__ = "settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"))
    setting_key = Column(String(255), nullable=False)
    setting_value = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("project_id", "setting_key", name="unique_setting"),
    )

    # Relationships
    project = relationship("Project", back_populates="settings")
