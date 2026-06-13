import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.orchestrator import OrchestratorService
from app.core.detector import AutoDetect
from app.core.sanitizer import sanitize_target, InputValidationError
from app.core.api_key_auth import validate_ws_message_key
from app.core.config import settings

logger = logging.getLogger("trinetra.ws")

router = APIRouter(tags=["websocket"])
orchestrator = OrchestratorService()


async def _run_scan(websocket: WebSocket, target: str, target_type: str) -> None:
    """Stream scan results for a target over WebSocket."""
    async for message in orchestrator.run_all_stream(target, target_type):
        await websocket.send_json(message)


@router.websocket("/ws/search")
async def websocket_search(websocket: WebSocket):
    """Stream OSINT scan results in real-time over WebSocket.

    Protocol:
        1. Client sends:  {"target": "example.com", "type": "domain"}  (type is optional)
        2. Server sends:  {"type": "start", "total": 14, "plugins": [...]}
        3. Server sends:  {"type": "result", "result": {...}, "completed": 1, "total": 14}
                          ... for each plugin as it finishes
        4. Server sends:  {"type": "complete", "total": 14, "completed": 14}
    """
    await websocket.accept()
    try:
        # Always receive the first message (contains target + optional api_key)
        data = await websocket.receive_json()

        # Authenticate if API_KEY is configured
        if settings.api_key and not validate_ws_message_key(data):
            await websocket.send_json(
                {"type": "error", "message": "Unauthorized: valid API key required"}
            )
            await websocket.close(code=4001, reason="Unauthorized")
            return

        raw_target = data.get("target", "")

        # Sanitize input
        try:
            target = sanitize_target(raw_target)
        except InputValidationError as e:
            await websocket.send_json({"type": "error", "message": e.message})
            await websocket.close()
            return

        # Auto-detect target type
        target_type = data.get("type") or AutoDetect.detect(target)
        if target_type == "unknown":
            target_type = "domain"  # fallback

        # Stream results as they complete
        await _run_scan(websocket, target, target_type)

    except WebSocketDisconnect:
        # Client disconnected — no cleanup needed, tasks will be GC'd
        pass
    except Exception as e:
        logger.exception("WebSocket search error")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except WebSocketDisconnect:
            pass
