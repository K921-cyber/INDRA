"""
TRINETRA — Payment API Routes

Endpoints for Cashfree payment integration:
- POST /api/payment/create-order — Create a payment order
- POST /api/payment/webhook — Cashfree webhook (no auth)
- GET  /api/payment/credits — Get user's credit balance
- GET  /api/payment/plans — List available plans
- GET  /api/payment/history — Payment history
- POST /api/payment/verify — Manual order verification
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Header

from app.core.api_key_auth import require_api_key, get_user_credits, get_username_for_token
from app.services.payment_service import payment_service
from app.core.config import settings

logger = logging.getLogger("trinetra.payment_routes")

router = APIRouter(prefix="/api/payment", tags=["payment"])


@router.get("/plans")
async def list_plans():
    """List available payment plans. Public endpoint."""
    return {
        "plans": payment_service.get_plans(),
        "configured": payment_service.is_configured,
        "env": settings.cashfree_env or "sandbox",
    }


@router.post("/create-order")
async def create_order(body: dict, _key: str = Depends(require_api_key)):
    """Create a Cashfree payment order for the authenticated user.

    Accepts: {"plan_id": "starter" | "pro" | "elite"}
    Returns order details for frontend checkout.
    """
    username = get_username_for_token(_key)
    if not username:
        raise HTTPException(401, detail={"error": "Invalid session"})

    plan_id = body.get("plan_id", "")
    if not plan_id:
        raise HTTPException(400, detail={"error": "plan_id is required"})

    result = await payment_service.create_order(username, plan_id)

    if result["success"]:
        return result
    else:
        raise HTTPException(400, detail={"error": result["error"]})


@router.get("/credits")
async def get_credits(_key: str = Depends(require_api_key)):
    """Get the authenticated user's credit balance."""
    username = get_username_for_token(_key)
    if not username:
        raise HTTPException(401, detail={"error": "Invalid session"})

    credits = get_user_credits(username)
    return {
        "username": username,
        "credits": credits,
    }


@router.post("/verify")
async def verify_order(body: dict, _key: str = Depends(require_api_key)):
    """Manually verify a payment order's status.

    Accepts: {"order_id": "..."}
    """
    username = get_username_for_token(_key)
    if not username:
        raise HTTPException(401, detail={"error": "Invalid session"})

    order_id = body.get("order_id", "")
    if not order_id:
        raise HTTPException(400, detail={"error": "order_id is required"})

    result = await payment_service.verify_order(order_id)
    return result


@router.get("/history")
async def payment_history(_key: str = Depends(require_api_key)):
    """Get the authenticated user's payment history."""
    from app.core.api_key_auth import get_user_payment_history

    username = get_username_for_token(_key)
    if not username:
        raise HTTPException(401, detail={"error": "Invalid session"})

    history = get_user_payment_history(username)
    return {
        "username": username,
        "payments": history,
        "total": len(history),
    }


@router.post("/webhook")
async def cashfree_webhook(request: Request):
    """Cashfree webhook endpoint.

    This endpoint is intentionally unauthenticated — Cashfree calls it directly.
    We verify the webhook signature for security.
    """
    raw_body = await request.body()
    x_webhook_signature = request.headers.get("x-webhook-signature", "")
    x_webhook_timestamp = request.headers.get("x-webhook-timestamp", "")

    # Verify webhook signature if secret key is configured
    if settings.cashfree_secret_key:
        if not x_webhook_signature or not x_webhook_timestamp:
            logger.warning("Webhook signature missing — rejecting")
            raise HTTPException(400, detail={"error": "Missing webhook signature"})
        is_valid = payment_service.verify_webhook_signature(
            raw_body=raw_body,
            signature=x_webhook_signature,
            timestamp=x_webhook_timestamp,
            secret_key=settings.cashfree_secret_key,
        )
        if not is_valid:
            logger.warning("Invalid webhook signature — rejecting")
            raise HTTPException(400, detail={"error": "Invalid signature"})

    # Parse and process the event
    try:
        event_data = await request.json()
    except Exception:
        raise HTTPException(400, detail={"error": "Invalid JSON"})

    result = await payment_service.process_webhook(event_data)
    return result
