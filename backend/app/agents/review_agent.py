"""리뷰 에이전트 — pytest 실행 및 수용 기준을 검증합니다."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Task, Project

logger = logging.getLogger(__name__)

Broadcaster = Callable[[dict], Awaitable[None]]

REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "passed": {
            "type": "boolean",
            "description": "테스트 전체 통과 AND 수용 기준 모두 충족 시 true",
        },
        "test_output": {
            "type": "string",
            "description": "pytest 실행 결과 전체 출력",
        },
        "criteria_results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["criterion", "passed", "reason"],
            },
        },
        "overall_feedback": {
            "type": "string",
            "description": "재시도 시 code_agent에 전달할 구체적인 수정 방향",
        },
    },
    "required": ["passed", "test_output", "criteria_results", "overall_feedback"],
}


@dataclass
class ReviewResult:
    passed: bool
    test_output: str
    overall_feedback: str


def _build_prompt(task: Task, project: Project) -> str:
    criteria_text = ""
    if task.acceptance_criteria:
        criteria_list = "\n".join(f"  - {c}" for c in task.acceptance_criteria)
        criteria_text = f"\n## 수용 기준\n{criteria_list}\n"

    return f"""당신은 코드 리뷰어입니다.
아래 Task의 구현을 검증하세요.

## Task 정보
- 제목: {task.title}
- 설명: {task.description}
{criteria_text}
## 프로젝트 경로
{project.local_repo_path}

## 검증 순서
1. Bash로 pytest 실행
   `cd {project.local_repo_path} && python -m pytest tests/ -v --tb=short 2>&1`
2. 테스트 결과(passed/failed) 확인
3. 각 수용 기준 항목을 실제 코드(Read, Glob)로 확인하여 충족 여부 판단

## 판정 기준
- passed=true: 모든 테스트 통과 AND 모든 수용 기준 충족
- passed=false: 테스트 하나라도 실패 OR 수용 기준 하나라도 미충족

overall_feedback에는 실패한 이유와 구체적인 수정 방향을 작성하세요.
결과를 JSON으로 반환하세요.
"""


async def run_review_agent(
    task: Task,
    project: Project,
    broadcast: Broadcaster | None = None,
) -> ReviewResult:
    """
    pytest 실행 및 수용 기준을 검증하여 ReviewResult를 반환합니다.

    :param task: 검증할 Task
    :param project: 프로젝트 정보 (local_repo_path 포함)
    :param broadcast: WebSocket 브로드캐스트 콜백
    """
    prompt = _build_prompt(task, project)

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep", "Bash"],
        permission_mode="bypassPermissions",
        max_turns=20,
        output_format={"type": "json_schema", "schema": REVIEW_SCHEMA},
    )

    parsed: dict | None = None

    async for message in query(prompt=prompt, options=options):
        if broadcast:
            try:
                msg_data = message.model_dump() if hasattr(message, "model_dump") else str(message)
            except Exception:
                msg_data = str(message)
            await broadcast({
                "type": "agent_message",
                "task_id": task.id,
                "agent": "review",
                "message": msg_data,
            })

        if hasattr(message, "structured_output") and message.structured_output is not None:
            parsed = message.structured_output
        elif hasattr(message, "result") and message.result:
            try:
                parsed = json.loads(message.result)
            except (json.JSONDecodeError, TypeError):
                pass

    if not parsed:
        logger.error("review_agent 결과 없음 (task_id=%s)", task.id)
        return ReviewResult(
            passed=False,
            test_output="리뷰 에이전트가 결과를 반환하지 않았습니다.",
            overall_feedback="에이전트 실행 결과가 없습니다. 재시도하세요.",
        )

    return ReviewResult(
        passed=parsed.get("passed", False),
        test_output=parsed.get("test_output", ""),
        overall_feedback=parsed.get("overall_feedback", ""),
    )
