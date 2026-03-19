"""Redis module — exposes the application-level redis_client singleton."""

from app.config import get_settings
from app.redis.client import RedisClient

redis_client = RedisClient(url=get_settings().redis_url)

__all__ = ["redis_client"]
