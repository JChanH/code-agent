"""Review agent — acceptance criteria를 pytest로 검증합니다.

Flow:
  1단계: Claude API + agentic loop로 테스트 작성 및 pytest 실행
  2단계: submit_review_result 도구 강제 호출로 구조화 결과 반환
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import anthropic

from app.models import Task, Project
from app.agents.prompts import load_prompt
from app.agents.tools.agent_loop import run_agent_loop
from app.agents.tools.registry import get_tool_definitions
from app.websocket.messages import BroadcastFn, msg_agent_message
from app.config import get_settings

logger = logging.getLogger(__name__)

REVIEW_ENABLED = True

# submit_review_result 도구 — SDK의 output_format=json_schema 대체
_SUBMIT_TOOL: dict[str, Any] = {
    "name": "submit_review_result",
    "description": (
        "리뷰 결과를 제출합니다. 테스트 실행 후 반드시 이 도구를 사용해 결과를 반환하세요."
    ),
    "input_schema": {
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
    },
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

    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # 1단계: 테스트 작성 + pytest 실행 (자유 분석) — 히스토리 보존
    async def on_message(payload: dict) -> None:
        if broadcast:
            await broadcast(msg_agent_message(payload, task_id=task.id, agent="review"))

    initial_messages = [{"role": "user", "content": prompt}]

    _, history = await run_agent_loop(
        client=client,
        model="claude-sonnet-4-6",
        messages=initial_messages,
        tool_names=["read_file", "glob_files", "grep_search", "write_file", "bash_exec"],
        max_turns=14,
        working_dir=project.local_repo_path,
        on_message=on_message,
    )

    # 2단계: 1단계 히스토리를 이어받아 submit_review_result 강제 호출
    history.append({
        "role": "user",
        "content": (
            "테스트 실행이 완료되었습니다. "
            "지금까지의 결과를 바탕으로 submit_review_result 도구를 사용해 최종 결과를 제출하세요."
        ),
    })

    all_tools = get_tool_definitions(["read_file", "glob_files", "grep_search", "write_file", "bash_exec"])
    all_tools.append(_SUBMIT_TOOL)

    parsed: dict | None = None

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=history,
        tools=all_tools,
        tool_choice={"type": "tool", "name": "submit_review_result"},
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_review_result":
            parsed = block.input
            break

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
