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

logger = logging.getLogger(__name__)

QUEUE_KEY = "runtime:error_queue"
BLPOP_TIMEOUT = 5  # seconds — allows clean shutdown polling


class RuntimeErrorConsumer:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._consume_loop(), name="redis_error_consumer")
        logger.info("RuntimeErrorConsumer started.")

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

        record = RuntimeErrorRecord(
            error_code=error_code,
            message=message,
            project_id=project_id,
            level=payload.get("level", "error"),
            error_timestamp=error_timestamp,
            metadata_=payload.get("metadata") or {},
        )

        saved = await runtime_error_repository.add(record)
        logger.info("Runtime error saved: %s [%s] %s", saved.id, saved.error_code, saved.project_id)

        ws_payload = {
            "type": "runtime_error",
            "data": {
                "id": saved.id,
                "error_code": saved.error_code,
                "message": saved.message,
                "project_id": saved.project_id,
                "level": saved.level,
                "error_timestamp": saved.error_timestamp.isoformat() if saved.error_timestamp else None,
                "metadata": saved.metadata_,
                "created_at": saved.created_at.isoformat(),
            },
        }
        await ws_manager.broadcast(project_id, ws_payload)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


error_consumer = RuntimeErrorConsumer()
