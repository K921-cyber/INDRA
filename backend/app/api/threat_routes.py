"""
TRINETRA — Threat Feed WebSocket Endpoint

Streams real-time threat events (attack vectors, cyber incidents, news)
to connected clients for the interactive map and ticker.
"""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.threat_feed import threat_feed
from app.core.api_key_auth import validate_token, is_auth_enabled
from app.core.config import settings

router = APIRouter(tags=["threat-feed"])


@router.websocket("/ws/threats")
async def websocket_threat_feed(websocket: WebSocket):
    """Stream real-time threat events over WebSocket.

    Protocol:
        1. On connect, server sends: {"type": "initial_state", "events": [...], "cities": [...]}
        2. Server then continuously sends:
           {"type": "attack_vector", ...}   — new attack vector for the map
           {"type": "threat_event", ...}     — threat ticker event
           {"type": "news_event", ...}       — cyber news headline
        3. Client can send: {"action": "pause"} or {"action": "resume"} to control feed
    """
    await websocket.accept()

    # Auth: check query param for session token
    if is_auth_enabled() and not validate_token(websocket.query_params.get("api_key")):
        try:
            await websocket.close(code=4001, reason="Unauthorized")
        except Exception:
            pass
        return

    # Subscribe to the threat feed
    queue = threat_feed.subscribe()

    try:
        # Send initial state
        initial = threat_feed.get_initial_state()
        await websocket.send_json(initial)

        # Create a task to forward events from queue to WebSocket
        forward_task: asyncio.Task | None = None

        async def forward_events():
            try:
                while True:
                    event = await queue.get()
                    await websocket.send_json(event)
            except (WebSocketDisconnect, asyncio.CancelledError, Exception):
                pass

        forward_task = asyncio.create_task(forward_events())

        # Listen for client messages (pause/resume/stop)
        try:
            while True:
                data = await websocket.receive_json()
                action = data.get("action")
                if action == "pause" and forward_task:
                    forward_task.cancel()
                    try:
                        await forward_task
                    except asyncio.CancelledError:
                        pass
                    forward_task = None
                elif action == "resume" and forward_task is None:
                    forward_task = asyncio.create_task(forward_events())
                elif action == "stop":
                    break
        except WebSocketDisconnect:
            pass
        finally:
            if forward_task:
                forward_task.cancel()
                try:
                    await forward_task
                except asyncio.CancelledError:
                    pass

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        threat_feed.unsubscribe(queue)
