"""In-process + Redis-backed pub/sub broker — v1.3.0.

The broker is a thin abstraction over `asyncio.Queue` for in-process
fan-out, with optional Redis pub/sub for multi-worker deployments.

Usage (publisher — synchronous, callable from any handler):

    from app.modules.realtime import publish_event
    publish_event(
        facility_id="fac-123",
        type="kpi.admissions.count",
        payload={"today": 47, "delta": 1},
    )

Usage (subscriber — async, runs in the WebSocket handler):

    async with broker.subscribe(facility_id="fac-123") as queue:
        while True:
            event = await queue.get()
            await websocket.send_json(event)

When `REDIS_URL` is set, the broker additionally subscribes to a Redis
channel `guineecare:realtime:{facility_id}` so that events published in
one worker are received by clients connected to any worker. The Redis
client is created lazily on first `publish_event` call.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, AsyncIterator

logger = logging.getLogger("guineecare.realtime")

# Redis is optional — only required for multi-worker fan-out
_REDIS_URL = os.environ.get("REDIS_URL", "")
_REDIS_CHANNEL_PREFIX = "guineecare:realtime:"


class InProcessBroker:
    """asyncio.Queue-based pub/sub broker.

    Maintains a dict of `facility_id → set[asyncio.Queue]`. `publish_event`
    pushes the event to every queue registered for the target facility
    (and to the special `"*"` channel for SUPER_ADMIN subscribers).

    Thread-safety: the broker is designed for single-process asyncio.
    `publish_event` is sync (safe to call from sync handlers); it uses
    `loop.call_soon` to schedule the `put_nowait` on the event loop.
    """

    def __init__(self) -> None:
        # facility_id → set of queues. The "*" key is the broadcast channel
        # (SUPER_ADMIN subscribers).
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._redis = None
        self._redis_task: asyncio.Task | None = None

    @contextlib.asynccontextmanager
    async def subscribe(self, facility_id: str) -> AsyncIterator[asyncio.Queue]:
        """Subscribe to events for `facility_id`. Returns an async context
        manager that yields a queue from which to consume events.

        Usage:
            async with broker.subscribe("fac-1") as queue:
                event = await queue.get()
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[facility_id].add(queue)
        logger.info("realtime.subscribe facility=%s subscribers=%d", facility_id, len(self._subscribers[facility_id]))
        try:
            yield queue
        finally:
            async with self._lock:
                self._subscribers[facility_id].discard(queue)
                if not self._subscribers[facility_id]:
                    del self._subscribers[facility_id]
            logger.info("realtime.unsubscribe facility=%s", facility_id)

    def publish_event(self, facility_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event to all subscribers of `facility_id` and to the
        `"*"` broadcast channel.

        Sync method — safe to call from sync handlers. If called from a
        different thread, schedules the put on the running event loop.
        """
        event = {
            "type": event_type,
            "payload": payload,
            "facility_id": facility_id,
            "ts": datetime.utcnow().isoformat() + "Z",
        }
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop — try to get any loop (sync context)
            loop = None

        # Local fan-out
        targets: list[asyncio.Queue] = []
        targets.extend(self._subscribers.get(facility_id, set()))
        targets.extend(self._subscribers.get("*", set()))

        for queue in targets:
            try:
                if loop is not None and loop.is_running():
                    loop.call_soon_threadsafe(self._put_nowait, queue, event)
                else:
                    self._put_nowait(queue, event)
            except Exception as e:
                logger.warning("realtime.publish_failed facility=%s type=%s err=%s", facility_id, event_type, e)

        # Redis fan-out (multi-worker)
        if self._redis is not None:
            self._publish_redis(facility_id, event)

    @staticmethod
    def _put_nowait(queue: asyncio.Queue, event: dict) -> None:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            # Drop the oldest event to make room — never block the publisher
            try:
                queue.get_nowait()
                queue.put_nowait(event)
            except asyncio.QueueEmpty:
                pass

    async def _ensure_redis(self) -> None:
        """Lazily create the Redis client and start the subscriber task."""
        if self._redis is not None or not _REDIS_URL:
            return
        try:
            import redis.asyncio as aioredis  # type: ignore
            self._redis = aioredis.from_url(_REDIS_URL, decode_responses=True)
            await self._redis.ping()
            self._redis_task = asyncio.create_task(self._redis_subscriber_loop())
            logger.info("realtime.redis_connected url=%s", _REDIS_URL)
        except Exception as e:
            logger.warning("realtime.redis_unavailable err=%s — falling back to in-process only", e)
            self._redis = None

    def _publish_redis(self, facility_id: str, event: dict) -> None:
        """Publish to Redis channel. Uses a fire-and-forget task."""
        channel = f"{_REDIS_CHANNEL_PREFIX}{facility_id}"
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._redis.publish(channel, json.dumps(event)))
        except RuntimeError:
            pass

    async def _redis_subscriber_loop(self) -> None:
        """Listen on Redis broadcast channels and forward to local subscribers."""
        if self._redis is None:
            return
        pubsub = self._redis.pubsub()
        # Subscribe to all facility channels via pattern
        await pubsub.psubscribe(f"{_REDIS_CHANNEL_PREFIX}*")
        try:
            async for message in pubsub.listen():
                if message["type"] != "pmessage":
                    continue
                try:
                    event = json.loads(message["data"])
                    facility_id = event.get("facility_id", "*")
                    # Local fan-out (skip Redis re-publish)
                    for queue in self._subscribers.get(facility_id, set()):
                        try:
                            queue.put_nowait(event)
                        except asyncio.QueueFull:
                            pass
                    # Also fan-out to SUPER_ADMIN subscribers
                    for queue in self._subscribers.get("*", set()):
                        try:
                            queue.put_nowait(event)
                        except asyncio.QueueFull:
                            pass
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("realtime.redis_message_parse_failed err=%s", e)
        except asyncio.CancelledError:
            pass
        finally:
            with contextlib.suppress(Exception):
                await pubsub.unsubscribe(f"{_REDIS_CHANNEL_PREFIX}*")
                await pubsub.close()

    def stats(self) -> dict[str, Any]:
        """Return a snapshot of broker state (for /metrics + health)."""
        return {
            "facilities": len(self._subscribers),
            "total_subscribers": sum(len(s) for s in self._subscribers.values()),
            "redis_enabled": self._redis is not None,
        }


# Singleton broker
broker = InProcessBroker()


def publish_event(facility_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """Convenience wrapper for `broker.publish_event`."""
    broker.publish_event(facility_id, event_type, payload)


def publish_kpi_update(
    facility_id: str,
    kpi: str,
    value: Any,
    delta: Any = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Publish a KPI update event.

    Args:
        facility_id: Target facility. Use "*" for broadcast (SUPER_ADMIN).
        kpi: Dotted KPI identifier (e.g. `admissions.today.count`).
        value: New value of the KPI.
        delta: Optional delta (e.g. +1 when a new admission is created).
        extra: Optional extra metadata.
    """
    payload = {"kpi": kpi, "value": value}
    if delta is not None:
        payload["delta"] = delta
    if extra:
        payload.update(extra)
    publish_event(facility_id, f"kpi.{kpi}", payload)
