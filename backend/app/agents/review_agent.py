"""Review agent — TODO: pytest 실행 방식으로 교체 예정."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Awaitable

from app.models import Task, Project

logger = logging.getLogger(__name__)

Broadcaster = Callable[[dict], Awaitable[None]]


@dataclass
class ReviewResult:
    passed: bool
    test_output: str
    overall_feedback: str


async def run_review_agent(
    task: Task,
    project: Project,  # noqa: ARG001
    broadcast: Broadcaster | None = None,
) -> ReviewResult:
    # TODO: 실제 검증 로직 구현 예정 (pytest 실행 방식으로 교체)
    logger.info("review_agent skipped — auto-pass (task_id=%s)", task.id)
    return ReviewResult(
        passed=True,
        test_output="Review skipped (auto-pass).",
        overall_feedback="",
    )
