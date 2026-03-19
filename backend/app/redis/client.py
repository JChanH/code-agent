"""Redis async client wrapper."""

import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self, url: str) -> None:
        self._url = url
        self._pool: aioredis.ConnectionPool | None = None
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        self._pool = aioredis.ConnectionPool.from_url(
            self._url, max_connections=10, decode_responses=True
        )
        self._client = aioredis.Redis(connection_pool=self._pool)
        logger.info("Redis connected: %s", self._url)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.aclose()
        logger.info("Redis connection closed.")

    @property
    def client(self) -> aioredis.Redis:
        if not self._client:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception:
            return False
