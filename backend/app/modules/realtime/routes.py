"""Realtime WebSocket routes — v1.3.0.

- `WS /api/v1/realtime/ws?token=<JWT>` — authenticated WebSocket that
  streams realtime events to the client. The JWT is decoded to extract
  `facility_id` and `role`; SUPER_ADMIN subscribes to the broadcast
  channel (all facilities), other roles only receive their facility's
  events.
- `GET /api/v1/realtime/stats` — broker stats (subscriber count, Redis
  status). Requires `metrics.read` permission (or SUPER_ADMIN).

Authentication via query param is the WebSocket convention (browsers
cannot set Authorization header on WebSocket handshake). The token is
the same JWT used for REST endpoints.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer

from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.realtime.broker import broker, publish_event
from app.modules.users.models import User

logger = logging.getLogger("guineecare.realtime")

router = APIRouter(prefix="/realtime", tags=["realtime"])
security = HTTPBearer(auto_error=False)

HEARTBEAT_INTERVAL_SECONDS = 25


def _authenticate_ws_token(token: str) -> dict:
    """Decode and validate a JWT for WebSocket authentication.

    Returns the claims dict. Raises HTTPException(401) on invalid token.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        claims = decode_access_token(token)
    except Exception as e:
        logger.info("realtime.ws_auth_failed err=%s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return claims


@router.websocket("/ws")
async def realtime_ws(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """WebSocket endpoint for realtime event streaming.

    Authentication: JWT passed as `?token=<JWT>` query parameter.

    After authentication, the client receives a `connected` event with
    its `facility_id` and `role`. Then it receives KPI update events
    for its facility (or all facilities for SUPER_ADMIN).

    Heartbeat: the server sends a `{type: "ping"}` event every 25s.
    The client can respond with `{type: "pong"}` (optional).
    """
    # Authenticate before accepting the connection
    try:
        claims = _authenticate_ws_token(token)
    except HTTPException:
        await websocket.close(code=4401)  # custom close code
        return

    facility_id = claims.get("facility_id") or "*"
    role = claims.get("role", "")
    # SUPER_ADMIN subscribes to the broadcast channel
    channel = "*" if role == "SUPER_ADMIN" else facility_id

    await websocket.accept()
    await websocket.send_json({
        "type": "connected",
        "payload": {"facility_id": facility_id, "role": role, "channel": channel},
    })

    logger.info("realtime.ws_connect user=%s facility=%s role=%s", claims.get("sub"), facility_id, role)

    # Start the subscriber loop
    async with broker.subscribe(channel) as queue:
        # Start heartbeat task
        async def heartbeat():
            while True:
                try:
                    await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
                    await websocket.send_json({"type": "ping"})
                except asyncio.CancelledError:
                    break
                except Exception:
                    break

        heartbeat_task = asyncio.create_task(heartbeat())

        try:
            # Two concurrent tasks: receive from client, send from queue
            async def receive_loop():
                while True:
                    try:
                        msg = await websocket.receive_text()
                        # Ignore client messages (could handle pong/subscribe here)
                    except WebSocketDisconnect:
                        raise
                    except Exception:
                        raise

            async def send_loop():
                while True:
                    event = await queue.get()
                    try:
                        await websocket.send_json(event)
                    except Exception:
                        raise

            done, pending = await asyncio.wait(
                [asyncio.create_task(receive_loop()), asyncio.create_task(send_loop())],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
        except WebSocketDisconnect:
            logger.info("realtime.ws_disconnect user=%s", claims.get("sub"))
        except Exception as e:
            logger.warning("realtime.ws_error user=%s err=%s", claims.get("sub"), e)
        finally:
            heartbeat_task.cancel()
            with __import__("contextlib").suppress(Exception):
                await heartbeat_task


@router.get(
    "/stats",
    summary="Statistiques du broker realtime",
    description=(
        "Retourne le nombre d'abonnés par canal, le nombre total de "
        "connexions WebSocket actives, et l'état de la connexion Redis "
        "(si configurée). Nécessite la permission `metrics.read`."
    ),
)
def realtime_stats(
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("SUPER_ADMIN", "ADMIN"):
        raise HTTPException(status_code=403, detail="Permission insuffisante : metrics.read requis")
    return broker.stats()


@router.post(
    "/test-broadcast",
    summary="Diffuser un événement de test (ADMIN+)",
    description=(
        "Publie un événement `test.broadcast` sur le canal de l'établissement "
        "courant. Utile pour vérifier qu'un client WebSocket connecté reçoit "
        "bien les messages. Nécessite la permission `metrics.read`."
    ),
)
def test_broadcast(
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("SUPER_ADMIN", "ADMIN"):
        raise HTTPException(status_code=403, detail="Permission insuffisante : metrics.read requis")
    publish_event(
        facility_id=current_user.facility_id or "*",
        event_type="test.broadcast",
        payload={"from": current_user.email, "msg": "Test broadcast from admin"},
    )
    return {"status": "broadcast", "channel": current_user.facility_id or "*"}
