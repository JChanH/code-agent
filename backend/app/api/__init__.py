"""API router package exports."""

from app.api.agent import agent_router
from app.api.git import git_router
from app.api.legacy import legacy_router
from app.api.projects import projects_router
from app.api.runtime_errors import runtime_errors_router
from app.api.specs import project_specs_router, specs_router
from app.api.tasks import project_tasks_router, tasks_router
from app.api.users import project_worktrees_router, users_router, worktrees_router

__all__ = [
    "projects_router",
    "users_router",
    "project_worktrees_router",
    "worktrees_router",
    "project_tasks_router",
    "tasks_router",
    "project_specs_router",
    "specs_router",
    "git_router",
    "agent_router",
    "legacy_router",
    "runtime_errors_router",
]
