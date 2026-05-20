"""
Stripe Payment Service

Centralised Stripe business logic reusable across invoices, webstores, and any
future payment flows. All direct Stripe API calls and payment helpers live here.
Route modules (stripe_connect.py, webstores.py) import from this service instead
of duplicating logic.

Handles:
- Platform fee schedule
- Connect account status caching
- Tenant tier lookups
- Invoice/webstore finalization helpers
- Stripe event auditing
"""

import os
import logging
import stripe
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorClient

# Standalone DB connection — avoids a circular import through server.py
# (server.py → webstores.py → stripe_service.py → server.py).
# Uses the same env-var names as server.py; falls back to development defaults
# so the module can be tested outside the full app context.
_MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
_DB_NAME = os.environ.get("DB_NAME", "signguy_ai")
_client = AsyncIOMotorClient(_MONGO_URL)
db = _client[_DB_NAME]
logger = logging.getLogger(__name__)

# ── Stripe initialisation ─────────────────────────────────────────────────────
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY")


# ── Platform fee schedule ─────────────────────────────────────────────────────
# Per landing-page promise: 2.2% + $0.20 on every transaction. Webstore orders
# get an additional +2.0% surcharge on top (covers hosted storefront infra +
# secure checkout) → 4.2% + $0.20 total. The fee is taken as a Stripe
# `application_fee_amount` on the destination charge.
PLATFORM_FEES: Dict[str, Dict[str, float]] = {
    "starter":          {"percent": 0.022, "flat_cents": 20},
    "pro":              {"percent": 0.022, "flat_cents": 20},
    "business":         {"percent": 0.022, "flat_cents": 20},
    "founders_edition": {"percent": 0.022, "flat_cents": 20},
}

# Extra surcharge layered on top of the base percent for webstore orders only.
# (Invoices stay at the base 2.2% + $0.20.)
WEBSTORE_SURCHARGE_PERCENT: float = 0.020


def get_platform_fee_config(tier: str) -> Dict[str, float]:
    """Return {percent, flat_cents} for the given tier."""
    return PLATFORM_FEES.get(tier, PLATFORM_FEES["founders_edition"])


def get_platform_fee_percent(tier: str) -> float:
    """Back-compat: return the *base* percent (without webstore surcharge).
    Prefer ``calculate_platform_fee_cents`` going forward.
    """
    return get_platform_fee_config(tier)["percent"]


def calculate_platform_fee_cents(
    tier: str,
    amount_cents: int,
    *,
    is_webstore: bool = False,
) -> int:
    """Compute the total platform fee in CENTS for a given transaction.

    For invoices:          amount * tier_percent + tier_flat_cents
    For webstore orders:   amount * (tier_percent + 2%) + tier_flat_cents

    Floors to non-negative and never exceeds the amount itself (so a $0.30
    invoice never produces a fee greater than the charge — Stripe rejects that).
    """
    cfg = get_platform_fee_config(tier)
    percent = cfg["percent"] + (WEBSTORE_SURCHARGE_PERCENT if is_webstore else 0.0)
    # Round-half-up to avoid float-precision drift (e.g. 0.022+0.020 stored as
    # 0.04199999…99 produces 209c instead of 210c on a $50 charge).
    fee = int(round(amount_cents * percent)) + int(cfg["flat_cents"])
    if fee < 0:
        fee = 0
    if amount_cents > 0 and fee >= amount_cents:
        # Don't let a tiny micro-payment produce a fee equal to the whole
        # charge. Cap at amount - 1 cent so the destination at least nets a cent.
        fee = max(amount_cents - 1, 0)
    return fee


def get_stripe_mode() -> str:
    """Return 'live' or 'test' based on the active Stripe API key."""
    api_key = stripe.api_key or ""
    return "live" if api_key.startswith("sk_live_") else "test"


# ── Connect account checkout-status cache ─────────────────────────────────────
# Caches the (enabled, status, message) triple per account for 5 min so public
# storefront reads don't pay a round-trip to Stripe on every page load.
_STRIPE_ACCOUNT_CACHE: Dict[str, Dict[str, Any]] = {}
_STRIPE_ACCOUNT_TTL_SECONDS = 300


def get_stripe_account_checkout_status(account_id: Optional[str]) -> Dict[str, Any]:
    """Return cached checkout availability for a Stripe Connect account.

    Not async — stripe.Account.retrieve is synchronous. A cache miss on the
    first call pays the Stripe latency; all subsequent calls within the TTL
    are free.
    """
    if not account_id:
        return {
            "enabled": False,
            "status": "inactive",
            "message": "Checkout is inactive until this shop connects Stripe through SignGuy AI.",
        }

    now_ts = datetime.now(timezone.utc).timestamp()
    cached = _STRIPE_ACCOUNT_CACHE.get(account_id)
    if cached and (now_ts - cached["fetched_at"]) < _STRIPE_ACCOUNT_TTL_SECONDS:
        return cached["value"]

    try:
        account = stripe.Account.retrieve(account_id)
        if account.charges_enabled:
            value = {"enabled": True, "status": "active", "message": "Checkout is active"}
        else:
            value = {
                "enabled": False,
                "status": "setup_incomplete",
                "message": "Checkout is inactive until Stripe Connect onboarding is fully completed.",
            }
    except stripe.error.StripeError:
        # Do not cache failures — a transient Stripe blip shouldn't persist.
        return {
            "enabled": False,
            "status": "unavailable",
            "message": "Checkout is temporarily unavailable while payment setup is being verified.",
        }

    _STRIPE_ACCOUNT_CACHE[account_id] = {"fetched_at": now_ts, "value": value}
    return value


# ── Tenant helpers ────────────────────────────────────────────────────────────
async def get_tenant_tier(tenant_id: str) -> str:
    """Return the subscription tier key ('starter' | 'pro' | 'business') for a tenant."""
    tenant = await db.tenants.find_one(
        {"id": tenant_id},
        {"_id": 0, "plan": 1, "is_founder": 1},
    )
    if not tenant:
        return "starter"

    plan = tenant.get("plan", "")
    is_founder = tenant.get("is_founder", False)

    if plan in ("os_business", "founders_edition") or (is_founder and plan == "founders_edition"):
        return "business"
    elif plan in ("os_pro",):
        return "pro"
    elif plan in ("business", "tier_3"):
        return "business"
    elif plan in ("pro", "tier_2"):
        return "pro"

    subscription = await db.subscriptions.find_one(
        {"tenant_id": tenant_id},
        {"_id": 0, "tier": 1},
    )
    if subscription:
        return subscription.get("tier", "starter")
    return "starter"


# ── Stripe account helpers ────────────────────────────────────────────────────
def is_wrong_mode_error(err: Exception) -> bool:
    """Detect Stripe's cross-mode error (test account used on live platform)."""
    msg = str(err or "").lower()
    return (
        ("testmode" in msg and "live" in msg)
        or ("test account" in msg and "testmode keys" in msg)
        or ("livemode" in msg and "test" in msg)
    )


async def scrub_stale_connect_account(tenant_id: str, account_id: str, reason: str) -> None:
    """Remove a stored Connect account ID that is no longer usable.

    Keeps a breadcrumb on the tenant document so support can trace why the
    record was cleared.
    """
    await db.tenants.update_one(
        {"id": tenant_id},
        {
            "$unset": {
                "stripe_connect_account_id": "",
                "stripe_connect_created_at": "",
            },
            "$set": {
                "stripe_connect_scrubbed_at": datetime.now(timezone.utc).isoformat(),
                "stripe_connect_scrubbed_reason": reason,
                "stripe_connect_scrubbed_account_id": account_id,
            },
        },
    )


# ── Stripe metadata + event helpers ──────────────────────────────────────────
def extract_metadata(stripe_obj: Any) -> Dict[str, Any]:
    """Safely extract metadata dict from any Stripe object."""
    if isinstance(stripe_obj, dict):
        return stripe_obj.get("metadata") or {}
    return getattr(stripe_obj, "metadata", {}) or {}


async def find_invoice_document(
    reference_id: str,
    tenant_id: Optional[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[Any]]:
    """Locate an invoice in either the invoices or legacy order_quotes collection."""
    if tenant_id:
        invoice = await db.invoices.find_one(
            {"id": reference_id, "tenant_id": tenant_id}, {"_id": 0}
        )
        if invoice:
            return invoice, db.invoices

        legacy = await db.order_quotes.find_one(
            {"id": reference_id, "tenant_id": tenant_id, "type": "invoice"},
            {"_id": 0},
        )
        if legacy:
            return legacy, db.order_quotes

    invoice = await db.invoices.find_one({"id": reference_id}, {"_id": 0})
    if invoice:
        return invoice, db.invoices

    legacy = await db.order_quotes.find_one({"id": reference_id, "type": "invoice"}, {"_id": 0})
    if legacy:
        return legacy, db.order_quotes

    return None, None


async def record_stripe_event(
    tenant_id: Optional[str],
    event_type: str,
    status: str,
    session_id: Optional[str] = None,
    reference_id: Optional[str] = None,
    amount: Optional[float] = None,
    currency: Optional[str] = None,
    message: Optional[str] = None,
    raw: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist a Stripe event to the audit log collection."""
    if not tenant_id:
        return
    doc = {
        "tenant_id": tenant_id,
        "event_type": event_type,
        "status": status,
        "session_id": session_id,
        "reference_id": reference_id,
        "amount": amount,
        "currency": currency,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if raw:
        doc["raw"] = raw
    await db.stripe_connect_events.insert_one(doc)


async def mark_invoice_paid(
    reference_id: str,
    tenant_id: Optional[str],
    session_id: str,
    amount: Optional[float],
    currency: Optional[str],
) -> None:
    """Mark an invoice as paid after a successful Stripe checkout session."""
    invoice, collection = await find_invoice_document(reference_id, tenant_id)
    if not invoice or collection is None:
        return

    grand_total = float(invoice.get("grand_total", invoice.get("total", 0)) or 0)
    current_paid = float(invoice.get("amount_paid", 0) or 0)
    paid_value = max(current_paid, grand_total, float(amount or 0))
    now_iso = datetime.now(timezone.utc).isoformat()

    await collection.update_one(
        {"id": reference_id, **({"tenant_id": tenant_id} if tenant_id else {})},
        {
            "$set": {
                "status": "paid",
                "paid_at": now_iso,
                "paid_date": now_iso,
                "payment_method": "stripe",
                "stripe_session_id": session_id,
                "amount_paid": paid_value,
                "updated_at": now_iso,
            }
        },
    )

    payment_exists = await db.payments.find_one(
        {"stripe_session_id": session_id, "invoice_id": reference_id},
        {"_id": 0, "stripe_session_id": 1},
    )
    if not payment_exists:
        await db.payments.insert_one(
            {
                "invoice_id": reference_id,
                "tenant_id": tenant_id,
                "amount": float(amount or grand_total or 0),
                "platform_fee": None,
                "payment_method": "stripe",
                "payment_type": "stripe_connect_checkout",
                "currency": currency or "usd",
                "stripe_session_id": session_id,
                "created_at": now_iso,
            }
        )


# ── Webstore order finalization ───────────────────────────────────────────────
async def finalize_webstore_stripe_checkout(session_id: str) -> Optional[dict]:
    """Idempotently convert a paid Stripe Checkout session into a webstore order.

    Called from both the Stripe webhook (checkout.session.completed) and the
    payment-status fallback endpoint for browsers that return to the success URL
    before the webhook lands. A second invocation for the same session returns
    the existing order unchanged.

    Uses lazy imports for webstore-specific types to avoid circular dependencies.
    """
    # Lazy imports to avoid circular dependency with routes.webstores
    from routes.webstores import (
        create_webstore_order,
        WebstoreOrderCreate,
        WebstoreOrderStatus,
        _apply_order_status_transition,
    )
    from pydantic import ValidationError

    ptx = await db.payment_transactions.find_one(
        {"stripe_session_id": session_id, "type": "webstore_order"},
        {"_id": 0},
    )
    if not ptx:
        logger.warning(f"finalize_webstore_stripe_checkout: no payment_transaction for {session_id}")
        return None

    tenant_id = ptx.get("tenant_id")
    webstore_id = ptx.get("reference_id")
    idempotency_key = f"stripe:{session_id}"

    # Idempotency guard — return the existing order if already created.
    existing = await db.webstore_orders_v2.find_one(
        {"idempotency_key": idempotency_key},
        {"_id": 0},
    )
    if existing:
        if existing.get("status") != WebstoreOrderStatus.COMPLETED.value:
            await _apply_order_status_transition(
                order=existing,
                new_status=WebstoreOrderStatus.COMPLETED.value,
                tenant_id=tenant_id,
            )
        return existing

    customer_info = ptx.get("customer_info") or {}
    validated_items = ptx.get("items") or []
    if not validated_items:
        logger.error(f"finalize_webstore_stripe_checkout: empty items for {session_id}")
        return None

    try:
        create_payload = WebstoreOrderCreate(
            webstore_id=webstore_id,
            customer_name=customer_info.get("name") or customer_info.get("customer_name") or "Customer",
            customer_email=customer_info.get("email") or customer_info.get("customer_email") or "no-email@webstore.local",
            customer_phone=customer_info.get("phone") or customer_info.get("customer_phone"),
            items=[
                {
                    "product_id": it["product_id"],
                    "variant_id": it.get("variant_id"),
                    "variant_name": it.get("variant_name"),
                    "quantity": it.get("quantity", 1),
                    "price": it.get("price"),
                }
                for it in validated_items
            ],
            notes=f"Paid via Stripe session {session_id}",
            idempotency_key=idempotency_key,
            donation_amount=float(ptx.get("donation_amount") or 0),
            profit_allocation_amount=float(ptx.get("profit_allocation_amount") or 0),
            shipping_handling_amount=float(ptx.get("shipping_handling_amount") or 0),
            donor_consent=bool(ptx.get("donor_consent")),
        )
    except ValidationError as exc:
        logger.error(f"finalize_webstore_stripe_checkout: invalid payload {exc}")
        return None

    try:
        order = await create_webstore_order(create_payload)
    except Exception as exc:
        logger.error(
            f"finalize_webstore_stripe_checkout: create_webstore_order rejected session "
            f"{session_id}: {getattr(exc, 'detail', str(exc))}"
        )
        return None

    order_doc = order if isinstance(order, dict) else order.model_dump()

    # Stamp Stripe metadata on the order and transition it to completed.
    await db.webstore_orders_v2.update_one(
        {"id": order_doc["id"]},
        {
            "$set": {
                "stripe_session_id": session_id,
                "stripe_customer_id": ptx.get("customer_info", {}).get("stripe_customer_id"),
                "payment_amount": ptx.get("amount"),
                "payment_platform_fee": ptx.get("platform_fee"),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    refreshed = await db.webstore_orders_v2.find_one({"id": order_doc["id"]}, {"_id": 0})
    await _apply_order_status_transition(
        order=refreshed,
        new_status=WebstoreOrderStatus.COMPLETED.value,
        tenant_id=tenant_id,
    )

    # Flip payment_transaction to paid so repeated webhook deliveries bail early.
    await db.payment_transactions.update_one(
        {"stripe_session_id": session_id},
        {
            "$set": {
                "status": "paid",
                "webstore_order_id": order_doc["id"],
                "paid_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    logger.info(f"Stripe session {session_id} → webstore order {order_doc['id']} (completed)")
    return await db.webstore_orders_v2.find_one({"id": order_doc["id"]}, {"_id": 0})
