"""Realtime module — v1.3.0.

Provides:
- An in-process pub/sub broker (`broker`) for broadcasting KPI updates
  to connected WebSocket clients. Redis pub/sub is used in production
  when `REDIS_URL` is set, enabling multi-worker fan-out.
- A WebSocket endpoint `WS /api/v1/realtime/ws` that authenticates via
  JWT (passed as query param `?token=...`) and streams events to the
  client. Events are JSON-encoded dicts with `{type, payload, ts}`.
- A publisher helper (`publish_kpi_update`) that modules call after
  mutations that should refresh the dashboard (admission, discharge,
  invoice payment, lab result validation, etc.).

Design choices:
- In-memory broker for dev/test (no Redis dependency). Redis is opt-in.
- Each connection is tied to a `facility_id` (extracted from the JWT),
  so events are filtered server-side — clients only receive updates
  relevant to their facility. SUPER_ADMIN receives all.
- Heartbeat: the broker sends `{type: "ping"}` every 25s to keep the
  connection alive through nginx proxies (default 60s timeout).
"""
from app.modules.realtime.broker import broker, publish_event, publish_kpi_update
from app.modules.realtime.routes import router

__all__ = ["broker", "publish_event", "publish_kpi_update", "router"]
