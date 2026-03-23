"""Redis BLPOP consumer — runtime error queue processor."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

import redis.asyncio as aioredis

from app.models.runtime_error import RuntimeErrorRecord
from app.repositories import runtime_error_repository
from app.websocket import ws_manager
from app.websocket.messages import (
    msg_runtime_error,
    msg_runtime_error_agent_message,
    msg_runtime_error_update,
)

logger = logging.getLogger(__name__)

QUEUE_KEY = "runtime:error_queue"
BLPOP_TIMEOUT = 5  # seconds — allows clean shutdown polling


class RuntimeErrorConsumer:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    # 앱 시작할때 + redis 시작 이후에 시작
    def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._consume_loop(), name="redis_error_consumer")
        logger.info("RuntimeErrorConsumer started.")

    # 앱 끝날때 redis + 종료 전에 실행
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("RuntimeErrorConsumer stopped.")

    async def _consume_loop(self) -> None:
        from app.redis import redis_client

        retry_delay = 1.0
        max_retry_delay = 60.0

        while self._running:
            try:
                result = await redis_client.client.blpop(QUEUE_KEY, timeout=BLPOP_TIMEOUT)
                if result is None:
                    continue

                retry_delay = 1.0
                _, raw = result
                await self._handle_message(raw)

            except aioredis.RedisError as exc:
                logger.error("Redis error in consumer: %s. Retrying in %.0fs.", exc, retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

            except asyncio.CancelledError:
                break

            except Exception as exc:
                logger.exception("Unexpected error in consumer: %s", exc)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

    async def _handle_message(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Malformed JSON in queue: %.120s", raw)
            return

        project_id = payload.get("project_id")
        error_code = payload.get("error_code")
        message = payload.get("message")

        if not all([project_id, error_code, message]):
            logger.warning("Missing required fields in runtime error payload: %s", payload)
            return

        error_timestamp = _parse_timestamp(payload.get("timestamp"))

        # analyzing 상태로 즉시 저장
        record = RuntimeErrorRecord(
            error_code=error_code,
            message=message,
            project_id=project_id,
            level=payload.get("level", "error"),
            error_timestamp=error_timestamp,
            metadata_=payload.get("metadata") or {},
            status="analyzing",
        )

        saved = await runtime_error_repository.add(record)
        logger.info("Runtime error saved (analyzing): %s [%s] %s", saved.id, saved.error_code, saved.project_id)

        # WebSocket으로 analyzing 상태 즉시 전송
        await ws_manager.broadcast(project_id, msg_runtime_error(_build_runtime_error_data(saved)))

        # 백그라운드로 agent 분석 실행
        asyncio.create_task(
            _run_analysis(saved),
            name=f"analyze_error_{saved.id}",
        )


async def _run_analysis(record: RuntimeErrorRecord) -> None:
    """agent로 오류 분석 후 resolved 상태로 업데이트."""
    from app.agents.runtime_error_agent import analyze_runtime_error
    from app.repositories import project_repository

    # TODO: task 추가 버튼을 누루며 즉시 개발에 inprocess 부분에 넣기

    try:
        # project_id(프로젝트 이름)로 프로젝트 조회 → local_repo_path 획득
        project = await project_repository.find_by_name(record.project_id)
        if not project or not project.local_repo_path:
            logger.warning(
                "Project not found or local_repo_path missing for project_name=%s, error_id=%s — ignoring",
                record.project_id, record.id,
            )
            await runtime_error_repository.update_status(record.id, "ignored")
            await ws_manager.broadcast(record.project_id, msg_runtime_error_update(record.id, "ignored"))
            return

        async def _on_progress(log_line: str) -> None:
            await ws_manager.broadcast(
                record.project_id,
                msg_runtime_error_agent_message(record.id, log_line),
            )

        fix_suggestion = await analyze_runtime_error(
            error_id=record.id,
            error_code=record.error_code,
            message=record.message,
            level=record.level,
            project_id=record.project_id,
            local_repo_path=project.local_repo_path,
            metadata=record.metadata_,
            on_progress=_on_progress,
        )

        updated = await runtime_error_repository.update_analysis_result(
            error_id=record.id,
            fix_suggestion=fix_suggestion,
            status="resolved",
        )

        if updated:
            logger.info("Runtime error resolved: %s", updated.id)
            await ws_manager.broadcast(
                record.project_id,
                msg_runtime_error_update(updated.id, updated.status, fix_suggestion=updated.fix_suggestion),
            )

    except Exception as exc:
        logger.exception("Analysis task failed for error_id=%s: %s", record.id, exc)
        await runtime_error_repository.update_status(record.id, "failed")
        await ws_manager.broadcast(record.project_id, msg_runtime_error_update(record.id, "failed"))


def _build_runtime_error_data(record: RuntimeErrorRecord) -> dict:
    return {
        "id": record.id,
        "error_code": record.error_code,
        "message": record.message,
        "project_id": record.project_id,
        "level": record.level,
        "error_timestamp": record.error_timestamp.isoformat() if record.error_timestamp else None,
        "metadata": record.metadata_,
        "fix_suggestion": record.fix_suggestion,
        "status": record.status,
        "created_at": record.created_at.isoformat(),
    }


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


error_consumer = RuntimeErrorConsumer()
