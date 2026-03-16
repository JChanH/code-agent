"""코드 에이전트 — Task를 구현하고 pytest 테스트를 작성합니다."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Awaitable

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Task, Project
from app.agents.prompts import load_prompt
from app.agents.guidemap_agent import guidemap_exists, _get_guidemap_path

logger = logging.getLogger(__name__)

Broadcaster = Callable[[dict], Awaitable[None]]

_GUIDELINE_PATH = Path(__file__).parent / "guidemap" / "PYTHON_FASTAPI_BACKEND_GUIDELINE.md"


def _build_prompt(task: Task, project: Project, review_context: dict | None = None) -> str:
    criteria_text = ""
    if task.acceptance_criteria:
        criteria_list = "\n".join(f"  - {c}" for c in task.acceptance_criteria)
        criteria_text = f"\n## Acceptance Criteria\n{criteria_list}\n"

    retry_section = ""
    if review_context:
        attempt = review_context.get("attempt", 1)
        retry_section = (
            f"\n## Previous Review Failed (Attempt {attempt}) — Fix the issues below\n\n"
            f"### Test Output\n{review_context.get('test_output', 'N/A')}\n\n"
            f"### Acceptance Criteria Review\n{review_context.get('overall_feedback', 'N/A')}\n"
        )

    guideline_section = ""
    if project.project_stack == "python" and project.framework == "fastapi":
        if project.project_type == "new":
            guideline_section = (
                f"\n## Framework Guideline\n"
                f"Read `{_GUIDELINE_PATH}` using the Read tool and follow its rules.\n"
            )
        elif guidemap_exists(project.name):
            guidemap_content = _get_guidemap_path(project.name).read_text(encoding="utf-8")
            guideline_section = f"\n## Project Guide\n{guidemap_content}\n"

    target_files_section = ""
    if task.target_files:
        files_list = "\n".join(f"  - {f}" for f in task.target_files)
        target_files_section = (
            f"\n## Target Files\n"
            f"Create or modify these files (relative to `{project.local_repo_path}`):\n"
            f"{files_list}\n"
            f"Read these files first (and their neighbors for patterns), then implement.\n"
        )

    return load_prompt(
        "code_agent.md",
        task_title=task.title,
        task_description=task.description,
        criteria_text=criteria_text,
        project_name=project.name,
        project_stack=project.project_stack,
        framework=project.framework or "unspecified",
        local_repo_path=project.local_repo_path,
        retry_section=retry_section,
        guideline_section=guideline_section,
        target_files_section=target_files_section,
    )


async def run_code_agent(
    task: Task,
    project: Project,
    review_context: dict | None = None,
    broadcast: Broadcaster | None = None,
) -> None:
    """
    Task를 구현하고 테스트를 작성합니다.

    :param task: 구현할 Task
    :param project: 프로젝트 정보 (local_repo_path 포함)
    :param review_context: 이전 리뷰 실패 결과 (재시도 시 주입)
    :param broadcast: WebSocket 브로드캐스트 콜백
    """
    prompt = _build_prompt(task, project, review_context)

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        permission_mode="bypassPermissions",
        max_turns=10,
    )

    async for message in query(prompt=prompt, options=options):
        if broadcast:
            try:
                msg_data = message.model_dump() if hasattr(message, "model_dump") else str(message)
            except Exception:
                msg_data = str(message)
            await broadcast({
                "type": "agent_message",
                "task_id": task.id,
                "agent": "code",
                "message": msg_data,
            })
