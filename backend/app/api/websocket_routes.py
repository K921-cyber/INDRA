import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.orchestrator import OrchestratorService
from app.core.detector import AutoDetect
from app.core.sanitizer import sanitize_target, InputValidationError
from app.core.api_key_auth import (
    validate_token, is_auth_enabled,
    get_username_for_token, get_user_credits, deduct_credits, add_credits,
)
from app.core.config import settings

logger = logging.getLogger("trinetra.ws")

router = APIRouter(tags=["websocket"])
orchestrator = OrchestratorService()


async def _run_scan(websocket: WebSocket, target: str, target_type: str) -> list[dict]:
    """Stream scan results for a target over WebSocket.
    
    Returns the list of result dicts so the caller can inspect
    status/credit_cost for post-scan refund logic.
    """
    results: list[dict] = []
    async for message in orchestrator.run_all_stream(target, target_type):
        await websocket.send_json(message)
        if message.get("type") == "result":
            results.append(message.get("result", {}))
    return results


@router.websocket("/ws/search")
async def websocket_search(websocket: WebSocket):
    """Stream OSINT scan results in real-time over WebSocket.

    Flat credit billing (mirrors POST /api/search logic):
      1. Deduct a flat CREDITS_PER_SEARCH (10) upfront
      2. Stream results, tracking completion
      3. Refund the full amount only if the scan fails or returns zero
         successful results
      4. Include credits_used / credits_refunded in the complete message

    Protocol:
        1. Client sends:  {"target": "example.com", "type": "domain"}  (type is optional)
        2. Server sends:  {"type": "start", "total": 14, "plugins": [...]}
        3. Server sends:  {"type": "result", "result": {...}, "completed": 1, "total": 14}
                          ... for each plugin as it finishes
        4. Server sends:  {"type": "complete", "total": 14, "completed": 14, "credits_used": N, "credits_refunded": M}
    """
    await websocket.accept()
    credits_used = 0
    credits_refunded = 0
    username = None
    payment_configured = False
    target = ""

    try:
        # Always receive the first message (contains target + optional api_key)
        data = await websocket.receive_json()

        # Authenticate: check query params for token (client sends via ?api_key=)
        token = websocket.query_params.get("api_key")
        if is_auth_enabled() and not validate_token(token):
            await websocket.send_json(
                {"type": "error", "message": "Unauthorized: valid session token required. Sign in first."}
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

        # ── Flat credit deduction ────────────────────────────────────
        payment_configured = bool(settings.cashfree_app_id and settings.cashfree_secret_key)

        if payment_configured and token:
            username = get_username_for_token(token)
            if username:
                from app.services.payment_service import CREDITS_PER_SEARCH
                total_cost = CREDITS_PER_SEARCH

                user_credits = get_user_credits(username)
                if user_credits < total_cost:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Insufficient credits: each search costs {total_cost}, have {user_credits}",
                        "credits": user_credits,
                        "credits_required": total_cost,
                    })
                    await websocket.close()
                    return

                success, _ = deduct_credits(username, total_cost)
                if success:
                    credits_used = total_cost
                else:
                    await websocket.send_json({"type": "error", "message": "Failed to deduct credits."})
                    await websocket.close()
                    return

        # Stream results as they complete, collecting them for refund logic
        results = await _run_scan(websocket, target, target_type)

        # ── Refund full amount if scan produced zero successful results ─
        if payment_configured and username and credits_used > 0:
            completed_count = sum(1 for r in results if r.get("status") == "completed")
            if completed_count == 0:
                refund_ok = add_credits(username, credits_used)
                if not refund_ok:
                    logger.error(
                        "WebSocket: failed to refund %d credits for user=%s target=%s",
                        credits_used, username, target,
                    )
                credits_refunded = credits_used
                logger.info(
                    "WebSocket: refunded %d credits — scan produced no successful results (target=%s user=%s)",
                    credits_used,
                    target,
                    username,
                )
            # Send credit summary so frontend can display remaining balance
            remaining = get_user_credits(username)
            await websocket.send_json({
                "type": "credits_summary",
                "credits_used": credits_used,
                "credits_refunded": credits_refunded,
                "credits_remaining": remaining,
            })

    except WebSocketDisconnect:
        # Client disconnected — refund all credits if any were deducted
        if payment_configured and username and credits_used > 0:
            refund_ok = add_credits(username, credits_used)
            if not refund_ok:
                logger.error("WebSocket disconnect: failed to refund %d credits for %s", credits_used, username)
            logger.info("Refunded %d credits for disconnected client %s", credits_used, username)
        return
    except Exception as e:
        logger.exception("WebSocket search error")
        # Full refund on error
        if payment_configured and username and credits_used > 0:
            refund_ok = add_credits(username, credits_used)
            if not refund_ok:
                logger.error("WebSocket error: failed to refund %d credits for %s", credits_used, username)
            logger.info("Refunded %d credits due to error for %s", credits_used, username)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except WebSocketDisconnect:
            pass
