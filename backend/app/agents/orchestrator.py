"""개발 오케스트레이터 — code_agent → review_agent 흐름을 관리합니다.

흐름:
  confirmed
    → (code_agent) → coding
    → (review_agent) → reviewing
    → 통과: done
    → 실패: 최대 MAX_RETRIES회까지 code_agent 재시도 (이전 리뷰 결과 컨텍스트 주입)
    → 초과: failed
"""

from __future__ import annotations

import logging

from app.agents.code_agent import run_code_agent
from app.agents.review_agent import run_review_agent, ReviewResult
from app.repositories import task_repository, project_repository
from app.utils.db_handler_sqlalchemy import db_conn
from app.websocket import ws_manager

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def _update_task_status(task_id: str, status: str) -> None:
    async with db_conn.transaction() as session:
        task = await task_repository.find_by_id(task_id, session)
        if task:
            task.status = status
            await session.flush()


async def run_task(task_id: str) -> None:
    """
    Task 1개의 전체 개발 사이클을 실행합니다.

    :param task_id: 실행할 Task ID (status == 'confirmed' 이어야 함)
    """
    task = await task_repository.find_by_id(task_id)
    if not task:
        logger.error("Task not found: %s", task_id)
        return

    project = await project_repository.find_by_id(task.project_id)
    if not project:
        logger.error("Project not found: %s", task.project_id)
        return

    async def broadcast(msg: dict) -> None:
        await ws_manager.broadcast(project.id, msg)

    review_context: dict | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info("Task 실행 시작 (task=%s, attempt=%d/%d)", task_id, attempt, MAX_RETRIES)

        # ── 1. 코딩 단계 ──────────────────────────────────────────────────────
        await _update_task_status(task_id, "coding")
        await broadcast({
            "type": "task_update",
            "task_id": task_id,
            "status": "coding",
            "attempt": attempt,
        })

        try:
            await run_code_agent(task, project, review_context=review_context, broadcast=broadcast)
        except Exception as exc:
            logger.exception("code_agent 실패 (task=%s, attempt=%d): %s", task_id, attempt, exc)
            await _update_task_status(task_id, "failed")
            await broadcast({
                "type": "task_update",
                "task_id": task_id,
                "status": "failed",
                "error": str(exc),
            })
            return

        # ── 2. 리뷰 단계 ──────────────────────────────────────────────────────
        await _update_task_status(task_id, "reviewing")
        await broadcast({
            "type": "task_update",
            "task_id": task_id,
            "status": "reviewing",
            "attempt": attempt,
        })

        try:
            result: ReviewResult = await run_review_agent(task, project, broadcast=broadcast)
        except Exception as exc:
            logger.exception("review_agent 실패 (task=%s, attempt=%d): %s", task_id, attempt, exc)
            await _update_task_status(task_id, "failed")
            await broadcast({
                "type": "task_update",
                "task_id": task_id,
                "status": "failed",
                "error": str(exc),
            })
            return

        await broadcast({
            "type": "review_result",
            "task_id": task_id,
            "attempt": attempt,
            "passed": result.passed,
            "test_output": result.test_output,
            "feedback": result.overall_feedback,
        })

        # ── 3. 통과 → 완료 ────────────────────────────────────────────────────
        if result.passed:
            await _update_task_status(task_id, "done")
            await broadcast({
                "type": "task_update",
                "task_id": task_id,
                "status": "done",
            })
            logger.info("Task 완료 (task=%s, attempt=%d)", task_id, attempt)
            return

        # ── 4. 실패 → 다음 시도 컨텍스트 구성 ────────────────────────────────
        logger.warning(
            "리뷰 실패, 재시도 예정 (task=%s, attempt=%d/%d)",
            task_id, attempt, MAX_RETRIES,
        )
        review_context = {
            "attempt": attempt,
            "test_output": result.test_output,
            "overall_feedback": result.overall_feedback,
        }

    # ── 5. 최대 재시도 초과 → failed ──────────────────────────────────────────
    await _update_task_status(task_id, "failed")
    await broadcast({
        "type": "task_update",
        "task_id": task_id,
        "status": "failed",
        "error": f"최대 재시도 횟수({MAX_RETRIES}회) 초과",
    })
    logger.error("Task 최대 재시도 초과 (task=%s)", task_id)
