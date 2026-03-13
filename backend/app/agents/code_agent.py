"""코드 에이전트 — Task를 구현하고 pytest 테스트를 작성합니다."""

from __future__ import annotations

import logging
from typing import Callable, Awaitable

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Task, Project
from app.agents.prompts import load_prompt

logger = logging.getLogger(__name__)

Broadcaster = Callable[[dict], Awaitable[None]]


def _build_prompt(task: Task, project: Project, review_context: dict | None = None) -> str:
    criteria_text = ""
    if task.acceptance_criteria:
        criteria_list = "\n".join(f"  - {c}" for c in task.acceptance_criteria)
        criteria_text = f"\n## 수용 기준\n{criteria_list}\n"

    retry_section = ""
    if review_context:
        attempt = review_context.get("attempt", 1)
        retry_section = (
            f"\n## ⚠️ 이전 리뷰 실패 결과 (시도 {attempt}회차) — 반드시 수정하세요\n\n"
            f"### 테스트 실행 결과\n{review_context.get('test_output', '없음')}\n\n"
            f"### 수용 기준 검토\n{review_context.get('overall_feedback', '없음')}\n"
        )

    return load_prompt(
        "code_agent.md",
        task_title=task.title,
        task_description=task.description,
        criteria_text=criteria_text,
        project_name=project.name,
        project_stack=project.project_stack,
        framework=project.framework or "미지정",
        local_repo_path=project.local_repo_path,
        retry_section=retry_section,
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
        max_turns=50,
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
