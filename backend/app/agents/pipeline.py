"""Development pipeline — code_agent → review_agent 순차 실행 파이프라인.

Flow:
  confirmed
    → (code_agent) → coding
    → (review_agent) → reviewing
    → pass: done
    → fail: retry code_agent up to MAX_RETRIES times (with previous review context injected)
    → exceeded: failed
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.agents.code_agent import run_code_agent
from app.agents.review_agent import run_review_agent, ReviewResult
from app.repositories import task_repository, project_repository
from app.utils.db_handler_sqlalchemy import db_conn
from app.utils.git import GitService
from app.websocket import make_broadcaster
from app.websocket.messages import msg_task_update, msg_review_result

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def _update_task_status(task_id: str, status: str) -> None:
    async with db_conn.transaction() as session:
        task = await task_repository.find_by_id(task_id, session)
        if task:
            task.status = status
            now = datetime.now(timezone.utc)
            if status == "coding" and task.started_at is None:
                task.started_at = now
            elif status in ("done", "failed"):
                task.completed_at = now
            await session.flush()


async def run_task(task_id: str) -> None:
    """
    Runs the full development cycle for a single Task.

    :param task_id: ID of the Task to run (status must be 'confirmed')
    """
    await _run_task_inner(task_id)


async def _run_task_inner(task_id: str) -> None:
    task = await task_repository.find_by_id(task_id)
    if not task:
        logger.error("Task not found: %s", task_id)
        return

    project = await project_repository.find_by_id(task.project_id)
    if not project:
        logger.error("Project not found: %s", task.project_id)
        return

    broadcast = make_broadcaster(project.id)

    review_context: dict | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info("Task started (task=%s, attempt=%d/%d)", task_id, attempt, MAX_RETRIES)

        # ── 1. Coding phase ───────────────────────────────────────────────────
        await _update_task_status(task_id, "coding")
        await broadcast(msg_task_update(task_id, "coding", attempt=attempt))

        try:
            modified_files = await run_code_agent(task, project, review_context=review_context, broadcast=broadcast)
        except Exception as exc:
            logger.exception("code_agent failed (task=%s, attempt=%d): %s", task_id, attempt, exc)
            await _update_task_status(task_id, "failed")
            await broadcast(msg_task_update(task_id, "failed", error=str(exc)))
            return

        # code agent가 수정한 파일 목록을 DB에 저장 후 task 객체 갱신
        if modified_files:
            async with db_conn.transaction() as session:
                t = await task_repository.find_by_id(task_id, session)
                if t:
                    t.files_to_modify = modified_files
                    await session.flush()
            task = await task_repository.find_by_id(task_id) or task

        # ── 2. Review phase ───────────────────────────────────────────────────
        await _update_task_status(task_id, "reviewing")
        await broadcast(msg_task_update(task_id, "reviewing", attempt=attempt))

        try:
            result: ReviewResult = await run_review_agent(task, project, broadcast=broadcast)
        except Exception as exc:
            logger.exception("review_agent failed (task=%s, attempt=%d): %s", task_id, attempt, exc)
            await _update_task_status(task_id, "failed")
            await broadcast(msg_task_update(task_id, "failed", error=str(exc)))
            return

        await broadcast(
            msg_review_result(
                task_id=task_id,
                attempt=attempt,
                passed=result.passed,
                test_output=result.test_output,
                feedback=result.overall_feedback,
            )
        )

        # ── 3. Pass → auto-commit → done ──────────────────────────────────────
        if result.passed:
            commit_hash: str | None = None
            try:
                git_svc = GitService(project.local_repo_path)
                git_svc.stage_all()
                if git_svc.has_staged_changes():
                    commit_hash = git_svc.commit(f"feat: {task.title}")
                    logger.info("Auto-committed (task=%s, hash=%s)", task_id, commit_hash)
                else:
                    logger.warning("Auto-commit skipped — no changes staged (task=%s)", task_id)
            except Exception as exc:
                logger.warning("Auto-commit failed (task=%s): %s", task_id, exc)

            async with db_conn.transaction() as session:
                t = await task_repository.find_by_id(task_id, session)
                if t:
                    t.status = "done"
                    t.completed_at = datetime.now(timezone.utc)
                    if commit_hash:
                        t.git_commit_hash = commit_hash
                    await session.flush()

            await broadcast(msg_task_update(task_id, "done"))
            logger.info("Task completed (task=%s, attempt=%d)", task_id, attempt)
            return

        # ── 4. Fail → build context for next attempt ──────────────────────────
        logger.warning(
            "Review failed, scheduling retry (task=%s, attempt=%d/%d)",
            task_id, attempt, MAX_RETRIES,
        )
        review_context = {
            "attempt": attempt,
            "test_output": result.test_output,
            "overall_feedback": result.overall_feedback,
        }

    # ── 5. Max retries exceeded → failed ──────────────────────────────────────
    await _update_task_status(task_id, "failed")
    await broadcast(msg_task_update(task_id, "failed", error=f"Max retries exceeded ({MAX_RETRIES})"))
    logger.error("Task exceeded max retries (task=%s)", task_id)
