"""Review agent — runs pytest and verifies acceptance criteria."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Task, Project
from app.agents.prompts import load_prompt

logger = logging.getLogger(__name__)

Broadcaster = Callable[[dict], Awaitable[None]]

REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "passed": {
            "type": "boolean",
            "description": "true if all tests pass AND all acceptance criteria are met",
        },
        "test_output": {
            "type": "string",
            "description": "Full pytest output",
        },
        "overall_feedback": {
            "type": "string",
            "description": "Specific fix directions to pass to code_agent on retry",
        },
    },
    "required": ["passed", "test_output", "overall_feedback"],
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
        criteria_text = f"\n## Acceptance Criteria\n{criteria_list}\n"

    target_files_section = ""
    if task.target_files:
        files_list = "\n".join(f"  - {project.local_repo_path}/{f}" for f in task.target_files)
        target_files_section = f"\n## Implementation Files\nReview these files:\n{files_list}\n"

    return load_prompt(
        "review_agent.md",
        task_title=task.title,
        task_description=task.description,
        criteria_text=criteria_text,
        local_repo_path=project.local_repo_path,
        target_files_section=target_files_section,
    )


async def run_review_agent(
    task: Task,
    project: Project,
    broadcast: Broadcaster | None = None,
) -> ReviewResult:
    """
    Runs pytest and verifies acceptance criteria, returning a ReviewResult.

    :param task: Task to verify
    :param project: Project info (including local_repo_path)
    :param broadcast: WebSocket broadcast callback
    """
    prompt = _build_prompt(task, project)

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        permission_mode="bypassPermissions",
        max_turns=15,
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
        logger.error("review_agent returned no result (task_id=%s)", task.id)
        return ReviewResult(
            passed=False,
            test_output="Review agent returned no result.",
            overall_feedback="No agent result. Please retry.",
        )

    return ReviewResult(
        passed=parsed.get("passed", False),
        test_output=parsed.get("test_output", ""),
        overall_feedback=parsed.get("overall_feedback", ""),
    )
