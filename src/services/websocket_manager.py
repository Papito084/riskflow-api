import asyncio
import json
import logging
import uuid
from typing import Any

import redis.asyncio as aioredis
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages multiplexed WebSocket connections grouped by trading account."""

    def __init__(self) -> None:
        self.active_connections: dict[uuid.UUID, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, account_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            if account_id not in self.active_connections:
                self.active_connections[account_id] = set()
            self.active_connections[account_id].add(websocket)
        logger.info(
            "WebSocket connected for account %s. Total for account: %d",
            account_id,
            len(self.active_connections[account_id]),
        )

    async def disconnect(self, account_id: uuid.UUID, websocket: WebSocket) -> None:
        async with self._lock:
            if account_id in self.active_connections:
                self.active_connections[account_id].discard(websocket)
                if not self.active_connections[account_id]:
                    del self.active_connections[account_id]
        logger.info("WebSocket disconnected for account %s", account_id)

    async def broadcast_to_account(self, account_id: uuid.UUID, message: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self.active_connections.get(account_id, []))

        if not sockets:
            return

        dead_sockets: set[WebSocket] = set()
        payload = json.dumps(message, default=str)

        for socket in sockets:
            try:
                await socket.send_text(payload)
            except Exception as e:
                logger.warning(
                    "Error sending message to websocket client for account %s: %s",
                    account_id,
                    e,
                )
                dead_sockets.add(socket)

        if dead_sockets:
            async with self._lock:
                if account_id in self.active_connections:
                    for dead in dead_sockets:
                        self.active_connections[account_id].discard(dead)
                    if not self.active_connections[account_id]:
                        del self.active_connections[account_id]


# Singleton instance
ws_manager = ConnectionManager()


async def start_redis_pubsub_listener(
    redis_client: aioredis.Redis, manager: ConnectionManager
) -> None:
    """Background task to consume Redis Pub/Sub events and route to local WebSockets."""
    pubsub = redis_client.pubsub()
    channel_pattern = "account:*:events"
    await pubsub.psubscribe(channel_pattern)
    logger.info("Subscribed to Redis pattern %s for WebSocket propagation", channel_pattern)

    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                channel = str(message["channel"])
                data = message["data"]
                try:
                    parts = channel.split(":")
                    if len(parts) >= 2:
                        acc_id = uuid.UUID(parts[1])
                        event_payload = json.loads(data) if isinstance(data, str) else data
                        await manager.broadcast_to_account(acc_id, event_payload)
                except Exception as ex:
                    logger.warning(
                        "Failed to forward Redis PubSub message from %s: %s", channel, ex
                    )
    except asyncio.CancelledError:
        logger.info("Redis PubSub listener task cancelled")
    except Exception as e:
        logger.error("Unexpected error in Redis PubSub listener: %s", e)
    finally:
        await pubsub.punsubscribe(channel_pattern)
        await pubsub.aclose()  # type: ignore[no-untyped-call]
