"""Schema enums shared across domain models."""

from enum import Enum


class ProjectStack(str, Enum):
    python = "python"
    java = "java"
    other = "other"


class ProjectStatus(str, Enum):
    setup = "setup"
    designing = "designing"
    developing = "developing"
    completed = "completed"


class TaskStatus(str, Enum):
    backlog = "backlog"
    planning = "planning"
    plan_review = "plan_review"
    coding = "coding"
    reviewing = "reviewing"
    done = "done"
    failed = "failed"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TaskComplexity(str, Enum):
    trivial = "trivial"
    low = "low"
    medium = "medium"
    high = "high"
    very_high = "very_high"


class SpecSourceType(str, Enum):
    document = "document"
    image = "image"
    text = "text"
    url = "url"


class SpecStatus(str, Enum):
    uploaded = "uploaded"
    analyzing = "analyzing"
    analyzed = "analyzed"
    confirmed = "confirmed"


class WorktreeStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"
