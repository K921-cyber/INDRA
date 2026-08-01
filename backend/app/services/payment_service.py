"""
TRINETRA — Cashfree Payment Service

Handles order creation, payment verification, and webhook processing
for the credits-based payment system via Cashfree Payment Gateway.

Usage:
    from app.services.payment_service import payment_service

    # Create an order
    result = await payment_service.create_order(username, plan_id)

    # Process webhook
    success = await payment_service.process_webhook(event_data)
"""

import hashlib
import hmac
import base64
import logging
from datetime import datetime, timezone

from cashfree_pg.api_client import Cashfree
from cashfree_pg.models.create_order_request import CreateOrderRequest
from cashfree_pg.models.customer_details import CustomerDetails
from cashfree_pg.models.order_meta import OrderMeta

from app.core.config import settings
from app.core.api_key_auth import (
    get_user,
    add_credits,
    record_payment,
    update_payment_status,
    get_payment_by_order,
)

logger = logging.getLogger("trinetra.payment")


# ── Flat credit pricing ───────────────────────────────────
# Every OSINT search costs a flat CREDITS_PER_SEARCH credits, regardless
# of how many (or which) plugins match the target. The full amount is
# refunded only if the entire scan fails or returns zero successful
# results.
CREDITS_PER_SEARCH = 10


# ── Pricing plans ────────────────────────────────────────

PLANS = {
    "starter": {
        "id": "starter",
        "name": "Starter",
        "amount": 99.00,
        "credits": 10,
        "description": "Try it out — 10 OSINT scans",
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "amount": 499.00,
        "credits": 100,
        "description": "Regular use — 100 OSINT scans",
    },
    "elite": {
        "id": "elite",
        "name": "Elite",
        "amount": 1499.00,
        "credits": 500,
        "description": "Power user — 500 OSINT scans",
    },
}


class PaymentService:
    """Manages Cashfree payment integration for TRINETRA."""

    def __init__(self):
        self._initialized = False
        self._client: Cashfree | None = None

    def _ensure_initialized(self):
        """Lazily initialize the Cashfree SDK with credentials."""
        if self._initialized:
            return

        if not settings.cashfree_app_id or not settings.cashfree_secret_key:
            logger.warning(
                "Cashfree not configured — payment features disabled. "
                "Set CASHFREE_APP_ID and CASHFREE_SECRET_KEY to enable."
            )
            return

        env = Cashfree.PRODUCTION if settings.cashfree_env == "production" else Cashfree.SANDBOX
        self._client = Cashfree(
            XEnvironment=env,
            XClientId=settings.cashfree_app_id,
            XClientSecret=settings.cashfree_secret_key,
        )

        self._initialized = True
        logger.info(
            "Cashfree SDK initialized (env=%s)",
            settings.cashfree_env,
        )

    @property
    def client(self) -> Cashfree:
        """Get the initialized Cashfree client instance."""
        self._ensure_initialized()
        return self._client

    @property
    def is_configured(self) -> bool:
        """Whether Cashfree credentials are available."""
        return bool(settings.cashfree_app_id and settings.cashfree_secret_key)

    def get_plans(self) -> list[dict]:
        """Return available payment plans."""
        return list(PLANS.values())

    def get_plan(self, plan_id: str) -> dict | None:
        """Get a specific plan by ID."""
        return PLANS.get(plan_id)

    async def create_order(self, username: str, plan_id: str) -> dict:
        """Create a Cashfree payment order.

        Returns:
            {
                "success": True,
                "order_id": "...",
                "payment_session_id": "...",
                "amount": 99.0,
                "currency": "INR",
                "plan": {...}
            }
        """
        self._ensure_initialized()

        if not self.is_configured:
            return {
                "success": False,
                "error": "Payment gateway not configured. Set CASHFREE_APP_ID and CASHFREE_SECRET_KEY.",
            }

        plan = PLANS.get(plan_id)
        if not plan:
            return {"success": False, "error": f"Invalid plan: {plan_id}"}

        user = get_user(username)
        if not user:
            return {"success": False, "error": "User not found"}

        try:
            customer_details = CustomerDetails(
                customer_id=f"trinetra_{username}",
                customer_phone="9999999999",  # Placeholder — Cashfree requires this
                customer_email=user.get("email", f"{username}@trinetra.local"),
            )

            order_meta = OrderMeta(
                return_url=f"{settings.cors_origins[0]}/payment/verify?order_id={{order_id}}",
                notify_url=settings.cashfree_webhook_url,
            )

            order_request = CreateOrderRequest(
                order_amount=plan["amount"],
                order_currency="INR",
                customer_details=customer_details,
                order_meta=order_meta,
            )

            response = self.client.PGCreateOrder(create_order_request=order_request)

            if response.data:
                order_id = response.data.order_id
                payment_session_id = response.data.payment_session_id

                # Record the payment in our DB
                record_payment(
                    order_id=order_id,
                    username=username,
                    amount=plan["amount"],
                    credits=plan["credits"],
                    status="pending",
                )

                logger.info(
                    "Order created: %s (user=%s, plan=%s, ₹%.0f)",
                    order_id,
                    username,
                    plan_id,
                    plan["amount"],
                )

                return {
                    "success": True,
                    "order_id": order_id,
                    "payment_session_id": payment_session_id,
                    "amount": plan["amount"],
                    "currency": "INR",
                    "env": settings.cashfree_env or "sandbox",
                    "plan": plan,
                }
            else:
                return {"success": False, "error": "Failed to create order with Cashfree"}

        except Exception as e:
            logger.error("Cashfree order creation failed: %s", e)
            return {"success": False, "error": f"Payment gateway error: {str(e)}"}

    async def verify_order(self, order_id: str) -> dict:
        """Verify an order's status via Cashfree API.

        Returns:
            {"success": True, "status": "PAID", "credits_added": 100}
        """
        self._ensure_initialized()

        if not self.is_configured:
            return {"success": False, "error": "Payment gateway not configured"}

        try:
            response = self.client.PGFetchOrder(order_id=order_id)

            if response.data:
                cf_order = response.data[0] if isinstance(response.data, list) else response.data
                order_status = cf_order.order_status

                if order_status == "PAID":
                    # Check if already processed (idempotent)
                    existing = get_payment_by_order(order_id)
                    if existing and existing["status"] == "completed":
                        return {
                            "success": True,
                            "status": "PAID",
                            "already_processed": True,
                            "credits_added": existing["credits"],
                        }

                    # Process successful payment
                    return await self._process_successful_payment(
                        order_id=order_id,
                        payment_method=getattr(cf_order, "payment_method", None),
                        cf_payment_id=getattr(cf_order, "cf_payment_id", None),
                    )
                else:
                    return {"success": False, "status": order_status, "detail": f"Order is {order_status} — payment not completed yet."}
            else:
                return {"success": False, "error": "Order not found"}

        except Exception as e:
            logger.error("Cashfree order verification failed: %s", e)
            return {"success": False, "error": str(e)}

    async def process_webhook(self, event_data: dict) -> dict:
        """Process a Cashfree webhook event.

        Handles PAYMENT_SUCCESS_WEBHOOK and other events.
        """
        event_type = event_data.get("type", "")
        order_data = event_data.get("data", {}).get("order", {})

        logger.info("Webhook received: type=%s", event_type)

        if event_type == "PAYMENT_SUCCESS_WEBHOOK":
            order_id = order_data.get("order_id")
            if not order_id:
                return {"success": False, "error": "Missing order_id"}

            # Check if already processed (idempotent)
            existing = get_payment_by_order(order_id)
            if existing and existing["status"] == "completed":
                return {"success": True, "message": "Already processed"}

            return await self._process_successful_payment(
                order_id=order_id,
                payment_method=event_data.get("data", {}).get("payment", {}).get("payment_method"),
                cf_payment_id=event_data.get("data", {}).get("payment", {}).get("cf_payment_id"),
            )

        elif event_type in ("PAYMENT_FAILED_WEBHOOK", "PAYMENT_USER_DROPPED_WEBHOOK"):
            order_id = order_data.get("order_id")
            if order_id:
                update_payment_status(order_id, "failed")
            return {"success": True, "message": "Payment failure recorded"}

        return {"success": True, "message": f"Ignored event: {event_type}"}

    async def _process_successful_payment(
        self,
        order_id: str,
        payment_method: str | None = None,
        cf_payment_id: str | None = None,
    ) -> dict:
        """Process a successful payment: record it and add credits."""
        # Get the payment record
        payment = get_payment_by_order(order_id)
        if not payment:
            logger.error("Payment record not found for order_id: %s", order_id)
            return {"success": False, "error": "Payment record not found"}

        if payment["status"] == "completed":
            return {"success": True, "already_processed": True, "credits_added": payment["credits"]}

        # Get username from the payment record (joined from users table)
        username = payment["username"]
        credits_to_add = payment["credits"]

        # Update payment status
        update_payment_status(
            order_id=order_id,
            status="completed",
            payment_method=payment_method,
            cf_payment_id=cf_payment_id,
        )

        # Add credits to user
        success = add_credits(username, credits_to_add)
        if success:
            logger.info(
                "Payment completed: order=%s user=%s credits=+%d",
                order_id,
                username,
                credits_to_add,
            )
            return {"success": True, "credits_added": credits_to_add}
        else:
            logger.error("Failed to add credits for order %s user %s", order_id, username)
            return {"success": False, "error": "Failed to add credits"}

    @staticmethod
    def verify_webhook_signature(
        raw_body: bytes,
        signature: str,
        timestamp: str,
        secret_key: str,
    ) -> bool:
        """Verify a Cashfree webhook signature (HMAC-SHA256)."""
        try:
            msg = timestamp.encode("utf-8") + raw_body
            computed = base64.b64encode(
                hmac.new(
                    secret_key.encode("utf-8"),
                    msg,
                    hashlib.sha256,
                ).digest()
            ).decode("utf-8")
            return hmac.compare_digest(computed, signature)
        except Exception as e:
            logger.error("Webhook signature verification failed: %s", e)
            return False


# Singleton instance
payment_service = PaymentService()
