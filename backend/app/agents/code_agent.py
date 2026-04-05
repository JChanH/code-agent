"""코드 에이전트 — Task를 구현하고 pytest 테스트를 작성합니다."""

from __future__ import annotations

import logging
from pathlib import Path

import anthropic

from app.models import Task, Project
from app.agents.prompts import load_prompt
from app.agents.guidemap_agent import guidemap_exists, get_guidemap_context
from app.agents.tools.agent_loop import run_agent_loop
from app.websocket.messages import BroadcastFn, msg_agent_message
from app.config import get_settings

logger = logging.getLogger(__name__)

# NOTE: 임시
_GUIDELINE_PATH = Path(__file__).parent / "guidemap" / "PYTHON_FASTAPI_BACKEND_GUIDELINE.md"


def _build_prompt(task: Task, project: Project, review_context: dict | None = None) -> str:
    # TODO 좀더 구조적으로 정리할수 있는지 코드 분석하기
    criteria_text = ""
    if task.acceptance_criteria:
        criteria_list = "\n".join(f"  - {c}" for c in task.acceptance_criteria)
        criteria_text = f"\n## Acceptance Criteria\n{criteria_list}\n"

    plan_section = ""
    if task.implementation_steps:
        steps_list = "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(task.implementation_steps))
        plan_section = f"\n## Implementation Plan\n{steps_list}\n"

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
            guidemap_content = get_guidemap_context(project.name)
            guideline_section = f"\n## Project Guide\n{guidemap_content}\n"

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
        plan_section=plan_section,
    )


async def run_code_agent(
    task: Task,
    project: Project,
    review_context: dict | None = None,
    broadcast: BroadcastFn | None = None,
) -> None:
    """
    Task를 구현하고 테스트를 작성합니다.

    :param task: 구현할 Task
    :param project: 프로젝트 정보 (local_repo_path 포함)
    :param review_context: 이전 리뷰 실패 결과 (재시도 시 주입)
    :param broadcast: WebSocket 브로드캐스트 콜백
    """
    prompt = _build_prompt(task, project, review_context)

    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def on_message(payload: dict) -> None:
        if broadcast:
            await broadcast(msg_agent_message(payload, task_id=task.id, agent="code"))

    await run_agent_loop(
        client=client,
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": prompt}],
        tool_names=["read_file", "write_file", "edit_file", "glob_files", "grep_search", "bash_exec"],
        max_turns=20,
        working_dir=project.local_repo_path,
        on_message=on_message,
    )
