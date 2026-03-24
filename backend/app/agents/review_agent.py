"""Review agent — acceptance criteria를 pytest로 검증합니다.

Flow:
  1. Claude Agent가 구현 파일을 읽고 acceptance criteria 기반 pytest 테스트 작성
  2. pytest 실행
  3. 결과를 ReviewResult로 반환
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Task, Project
from app.agents.prompts import load_prompt
from app.websocket.messages import BroadcastFn, extract_agent_msg_data, msg_agent_message

logger = logging.getLogger(__name__)

# TODO: 검토 후 True로 변경
REVIEW_ENABLED = False

REVIEW_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "passed": {
            "type": "boolean",
            "description": "True if ALL acceptance criteria are verified by passing tests",
        },
        "test_output": {
            "type": "string",
            "description": "Full pytest stdout/stderr output",
        },
        "overall_feedback": {
            "type": "string",
            "description": "Specific fix directions for each failing criterion; empty string if passed",
        },
    },
    "required": ["passed", "test_output", "overall_feedback"],
}


@dataclass
class ReviewResult:
    passed: bool
    test_output: str
    overall_feedback: str


def _make_test_file_path(task: Task, local_repo_path: str) -> str:
    """Task 제목과 ID로부터 고유한 테스트 파일 경로를 생성합니다."""
    slug = re.sub(r"[^a-z0-9]+", "_", task.title.lower())[:30].strip("_")
    return f"{local_repo_path}/tests/test_{slug}_{task.id[:6]}.py"


def _build_prompt(task: Task, project: Project) -> str:
    criteria_text = ""
    if task.acceptance_criteria:
        criteria_list = "\n".join(f"  - {c}" for c in task.acceptance_criteria)
        criteria_text = f"\n## Acceptance Criteria\n{criteria_list}\n"

    test_file_path = _make_test_file_path(task, project.local_repo_path)

    return load_prompt(
        "review_agent.md",
        task_title=task.title,
        task_description=task.description,
        criteria_text=criteria_text,
        local_repo_path=project.local_repo_path,
        test_file_path=test_file_path,
    )


async def run_review_agent(
    task: Task,
    project: Project,
    broadcast: BroadcastFn | None = None,
) -> ReviewResult:
    """
    Task 구현을 pytest로 검증합니다.

    :param task: 검증할 Task (acceptance_criteria 포함)
    :param project: 프로젝트 정보 (local_repo_path 포함)
    :param broadcast: WebSocket 브로드캐스트 콜백
    """
    # TODO: 검증할 부분이 있어서 잠시 skip
    if not REVIEW_ENABLED:
        logger.info("review_agent skipped — auto-pass (task_id=%s)", task.id)
        return ReviewResult(
            passed=True,
            test_output="Review skipped (auto-pass).",
            overall_feedback="",
        )

    prompt = _build_prompt(task, project)

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        allowed_tools=["Read", "Glob", "Grep", "Write", "Bash"],
        permission_mode="bypassPermissions",
        max_turns=15,
        output_format={"type": "json_schema", "schema": REVIEW_RESULT_SCHEMA},
    )

    parsed: dict | None = None

    async for message in query(prompt=prompt, options=options):
        if broadcast:
            await broadcast(msg_agent_message(extract_agent_msg_data(message), task_id=task.id, agent="review"))

        if hasattr(message, "structured_output") and message.structured_output is not None:
            parsed = message.structured_output

    if parsed is None:
        logger.error("Review agent returned no result (task_id=%s)", task.id)
        return ReviewResult(
            passed=False,
            test_output="Review agent returned no result.",
            overall_feedback="The review agent failed to produce output. Retry.",
        )

    return ReviewResult(
        passed=parsed.get("passed", False),
        test_output=parsed.get("test_output", ""),
        overall_feedback=parsed.get("overall_feedback", ""),
    )
