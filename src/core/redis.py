import json
import logging
from typing import Any, cast

import redis.asyncio as aioredis

from src.core.config import settings

logger = logging.getLogger(__name__)

# Redis global pool
redis_client: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.async_redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Connected to Redis at %s", settings.REDIS_HOST)
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
        logger.info("Closed Redis connection pool.")


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        await init_redis()
    assert redis_client is not None
    return redis_client


class RedisCacheService:
    """Helper service for caching and pub/sub message propagation."""

    def __init__(self, client: aioredis.Redis) -> None:
        self.client = client

    async def get_json(self, key: str) -> dict[str, Any] | None:
        try:
            data = await self.client.get(key)
            if data:
                return cast(dict[str, Any], json.loads(data))
            return None
        except Exception as e:
            logger.warning("Error reading from Redis key %s: %s", key, e)
            return None

    async def set_json(self, key: str, value: Any, ttl: int = 60) -> bool:
        try:
            payload = json.dumps(value, default=str)
            await self.client.set(key, payload, ex=ttl)
            return True
        except Exception as e:
            logger.warning("Error writing to Redis key %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning("Error deleting Redis key %s: %s", key, e)
            return False

    async def publish(self, channel: str, message: dict[str, Any]) -> int:
        try:
            payload = json.dumps(message, default=str)
            result = await self.client.publish(channel, payload)
            return int(result)
        except Exception as e:
            logger.warning("Error publishing to Redis channel %s: %s", channel, e)
            return 0
