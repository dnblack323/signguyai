"""
Stripe Connect Routes

Enables tenants to connect their own Stripe accounts to accept payments
for invoices and webstore orders.

Platform fee structure:
- Tier 1 (Starter): 3%
- Tier 2 (Growth): 2%
- Tier 3 (Pro/Business): 1%
"""

import os
import stripe
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'signage_erp')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Import auth dependencies
from models import UserInDB
from core.auth_deps import get_current_active_user

router = APIRouter(prefix="/stripe-connect", tags=["Stripe Connect"])
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY') or os.environ.get('STRIPE_API_KEY')

# Platform fee percentages by tier
PLATFORM_FEES = {
    "starter": 0.022,    # All Founders: 2.2% platform processing
    "pro": 0.022,        # All Founders: 2.2% platform processing
    "business": 0.022,   # All Founders: 2.2% platform processing
    "founders_edition": 0.022,  # 2.2% platform processing
}


class ConnectAccountResponse(BaseModel):
    """Response for connect account status"""
    connected: bool = False
    account_id: Optional[str] = None
    charges_enabled: bool = False
    payouts_enabled: bool = False
    onboarding_complete: bool = False
    platform_fee_percent: float = 3.0
    stripe_mode: str = "test"
    account_mode: Optional[str] = None
    mode_mismatch: bool = False


class OnboardingLinkRequest(BaseModel):
    """Request to create onboarding link"""
    return_url: str
    refresh_url: str


class OnboardingLinkResponse(BaseModel):
    """Response with onboarding URL"""
    url: str
    account_id: str


class PaymentRequest(BaseModel):
    """Request to create a payment"""
    amount: float = Field(..., gt=0, description="Amount in dollars")
    description: str
    metadata: dict = {}


class PaymentResponse(BaseModel):
    """Response with payment session URL"""
    url: str
    session_id: str


def _extract_metadata(stripe_obj: Any) -> Dict[str, Any]:
    if isinstance(stripe_obj, dict):
        return stripe_obj.get("metadata") or {}
    return getattr(stripe_obj, "metadata", {}) or {}


async def _find_invoice_document(reference_id: str, tenant_id: Optional[str]) -> tuple[Optional[Dict[str, Any]], Optional[Any]]:
    if tenant_id:
        invoice = await db.invoices.find_one({"id": reference_id, "tenant_id": tenant_id}, {"_id": 0})
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


async def _record_stripe_event(
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


async def _mark_invoice_paid(
    reference_id: str,
    tenant_id: Optional[str],
    session_id: str,
    amount: Optional[float],
    currency: Optional[str],
) -> None:
    invoice, collection = await _find_invoice_document(reference_id, tenant_id)
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


class WebstoreCheckoutItem(BaseModel):
    """Item in webstore checkout"""
    product_id: str
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    quantity: int = 1
    price: float = 0


class WebstoreCustomerInfo(BaseModel):
    """Customer info for webstore checkout"""
    name: str
    email: str
    phone: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class WebstoreCheckoutRequest(BaseModel):
    """Request body for webstore checkout"""
    items: list[WebstoreCheckoutItem]
    customer_info: WebstoreCustomerInfo


def get_platform_fee_percent(tier: str) -> float:
    """Get platform fee percentage for a tier"""
    return PLATFORM_FEES.get(tier, 0.022)  # Default to 2.2% (Founders)


def get_stripe_mode() -> str:
    api_key = stripe.api_key or ""
    return "live" if api_key.startswith("sk_live_") else "test"


async def _scrub_stale_connect_account(tenant_id: str, account_id: str, reason: str) -> None:
    """Remove a stored Connect account ID that is no longer usable.

    Used when Stripe reports the account was created in a different mode
    (e.g., test-mode account lingering on a live-mode platform), or the
    account has been deleted. Keeps a breadcrumb on the tenant doc so
    support can trace why the record was cleared.
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


def _is_wrong_mode_error(err: Exception) -> bool:
    """Detect Stripe's cross-mode error ('test account...testmode keys')."""
    msg = str(err or "").lower()
    return ("testmode" in msg and "live" in msg) or (
        "test account" in msg and "testmode keys" in msg
    ) or ("livemode" in msg and "test" in msg)


async def get_tenant_tier(tenant_id: str) -> str:
    """Get tenant's subscription tier from the plan system"""
    tenant = await db.tenants.find_one(
        {"id": tenant_id},
        {"_id": 0, "plan": 1, "is_founder": 1}
    )
    if not tenant:
        return "starter"
    
    plan = tenant.get("plan", "")
    is_founder = tenant.get("is_founder", False)
    
    # Map plan to tier for fee calculation
    if plan in ("os_business", "founders_edition") or (is_founder and plan == "founders_edition"):
        return "business"
    elif plan in ("os_pro",):
        return "pro"
    elif plan in ("business", "tier_3"):
        return "business"
    elif plan in ("pro", "tier_2"):
        return "pro"
    
    # Check subscriptions collection as fallback
    subscription = await db.subscriptions.find_one(
        {"tenant_id": tenant_id},
        {"_id": 0, "tier": 1}
    )
    if subscription:
        return subscription.get("tier", "starter")
    return "starter"


@router.get("/status", response_model=ConnectAccountResponse)
async def get_connect_status(current_user: UserInDB = Depends(get_current_active_user)):
    """Get the Stripe Connect status for the current tenant"""
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0, "stripe_connect_account_id": 1}
    )
    
    if not tenant or not tenant.get("stripe_connect_account_id"):
        tier = await get_tenant_tier(current_user.tenant_id)
        return ConnectAccountResponse(
            connected=False,
            platform_fee_percent=get_platform_fee_percent(tier) * 100,
            stripe_mode=get_stripe_mode(),
        )
    
    account_id = tenant["stripe_connect_account_id"]
    stripe_mode = get_stripe_mode()

    try:
        account = stripe.Account.retrieve(account_id)
        tier = await get_tenant_tier(current_user.tenant_id)

        # `livemode` is True only once Stripe activates the account. Before
        # activation it's None (unknown), and for actual test accounts it's
        # False. We must distinguish those two cases, otherwise freshly-created
        # but unactivated live accounts look like test accounts.
        livemode_flag = getattr(account, "livemode", None)
        if livemode_flag is True:
            account_mode = "live"
        elif livemode_flag is False:
            account_mode = "test"
        else:
            # Unactivated — assume it matches the platform's key mode.
            account_mode = stripe_mode

        # Hard guard: a test-mode account must never linger on a live platform.
        if stripe_mode == "live" and livemode_flag is False:
            await _scrub_stale_connect_account(
                current_user.tenant_id,
                account_id,
                "status_check_detected_test_account_on_live_platform",
            )
            return ConnectAccountResponse(
                connected=False,
                platform_fee_percent=get_platform_fee_percent(tier) * 100,
                stripe_mode=stripe_mode,
            )

        return ConnectAccountResponse(
            connected=True,
            account_id=account_id,
            charges_enabled=account.charges_enabled,
            payouts_enabled=account.payouts_enabled,
            onboarding_complete=account.details_submitted,
            platform_fee_percent=get_platform_fee_percent(tier) * 100,
            stripe_mode=stripe_mode,
            account_mode=account_mode,
            mode_mismatch=stripe_mode != account_mode,
        )
    except stripe.error.InvalidRequestError as e:
        # Stripe rejects the account: either it was deleted or it belongs to
        # the other mode (classic "ghost test account on live platform" case).
        # Either way, drop it and show the tenant an unconnected state so they
        # can restart cleanly.
        if _is_wrong_mode_error(e) or "No such account" in str(e):
            await _scrub_stale_connect_account(
                current_user.tenant_id,
                account_id,
                f"status_check_stripe_rejected: {str(e)[:200]}",
            )
            tier = await get_tenant_tier(current_user.tenant_id)
            return ConnectAccountResponse(
                connected=False,
                platform_fee_percent=get_platform_fee_percent(tier) * 100,
                stripe_mode=stripe_mode,
            )
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-account", response_model=OnboardingLinkResponse)
async def create_connect_account(
    request: OnboardingLinkRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a Stripe Connect account and return onboarding link"""
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if already has an account
    existing_account_id = tenant.get("stripe_connect_account_id")
    stripe_mode = get_stripe_mode()

    try:
        if existing_account_id:
            # Check if account exists and is valid for the current mode.
            try:
                account = stripe.Account.retrieve(existing_account_id)
                livemode_flag = getattr(account, "livemode", None)
                # Scrub test-mode accounts when we're on a live platform.
                if stripe_mode == "live" and livemode_flag is False:
                    await _scrub_stale_connect_account(
                        current_user.tenant_id,
                        existing_account_id,
                        "create_account_detected_test_account_on_live_platform",
                    )
                    account_id = None
                else:
                    account_id = existing_account_id
            except stripe.error.InvalidRequestError as e:
                # Either deleted, or the classic cross-mode ghost account.
                if _is_wrong_mode_error(e) or "No such account" in str(e):
                    await _scrub_stale_connect_account(
                        current_user.tenant_id,
                        existing_account_id,
                        f"create_account_stripe_rejected: {str(e)[:200]}",
                    )
                account_id = None
        else:
            account_id = None

        if not account_id:
            # Create new Standard Connect account (bound to the current key's mode).
            account = stripe.Account.create(
                type="standard",
                country="US",
                email=current_user.email,
                metadata={
                    "tenant_id": current_user.tenant_id,
                    "company_name": tenant.get("company_name", "")
                }
            )
            account_id = account.id

            # Defense in depth: if somehow Stripe returned a test account while
            # we're on a live key, refuse to save it. This should never happen
            # (Stripe binds the created account to the key's mode), but the
            # safety check is cheap and catches mis-wired environments.
            created_livemode = getattr(account, "livemode", None)
            if stripe_mode == "live" and created_livemode is False:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Stripe returned a test-mode account while the platform "
                        "is running in live mode. Please contact support."
                    ),
                )

            # Save to tenant
            await db.tenants.update_one(
                {"id": current_user.tenant_id},
                {
                    "$set": {
                        "stripe_connect_account_id": account_id,
                        "stripe_connect_created_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )

        # Create account link for onboarding
        account_link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=request.refresh_url,
            return_url=request.return_url,
            type="account_onboarding"
        )

        return OnboardingLinkResponse(url=account_link.url, account_id=account_id)

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh-link", response_model=OnboardingLinkResponse)
async def refresh_onboarding_link(
    request: OnboardingLinkRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Refresh the onboarding link for incomplete accounts"""
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0, "stripe_connect_account_id": 1}
    )
    
    if not tenant or not tenant.get("stripe_connect_account_id"):
        raise HTTPException(status_code=400, detail="No Stripe account found")
    
    account_id = tenant["stripe_connect_account_id"]
    stripe_mode = get_stripe_mode()

    # Verify the stored account is still usable with the current key mode.
    try:
        account = stripe.Account.retrieve(account_id)
    except stripe.error.InvalidRequestError as e:
        if _is_wrong_mode_error(e) or "No such account" in str(e):
            await _scrub_stale_connect_account(
                current_user.tenant_id,
                account_id,
                f"refresh_link_stripe_rejected: {str(e)[:200]}",
            )
            raise HTTPException(
                status_code=409,
                detail=(
                    "Your previously linked Stripe account is no longer valid. "
                    "Please click Connect Stripe again to start fresh."
                ),
            )
        raise HTTPException(status_code=400, detail=str(e))

    livemode_flag = getattr(account, "livemode", None)
    if stripe_mode == "live" and livemode_flag is False:
        await _scrub_stale_connect_account(
            current_user.tenant_id,
            account_id,
            "refresh_link_detected_test_account_on_live_platform",
        )
        raise HTTPException(
            status_code=409,
            detail=(
                "The Stripe account on file is a test-mode account and cannot "
                "be used on the live platform. Please click Connect Stripe "
                "again to create a live account."
            ),
        )

    try:
        account_link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=request.refresh_url,
            return_url=request.return_url,
            type="account_onboarding"
        )

        return OnboardingLinkResponse(url=account_link.url, account_id=account_id)

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/disconnect")
async def disconnect_stripe_account(current_user: UserInDB = Depends(get_current_active_user)):
    """Disconnect Stripe account from tenant"""
    result = await db.tenants.update_one(
        {"id": current_user.tenant_id},
        {
            "$unset": {
                "stripe_connect_account_id": "",
                "stripe_connect_created_at": ""
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {"message": "Stripe account disconnected"}


@router.get("/dashboard-link")
async def get_stripe_dashboard_link(current_user: UserInDB = Depends(get_current_active_user)):
    """Get link to Stripe Express dashboard for the connected account"""
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0, "stripe_connect_account_id": 1}
    )
    
    if not tenant or not tenant.get("stripe_connect_account_id"):
        raise HTTPException(status_code=400, detail="No Stripe account connected")
    
    # For Standard accounts, they access their own dashboard
    # Return the Stripe login URL
    return {
        "url": "https://dashboard.stripe.com/",
        "message": "Log in to your Stripe Dashboard to manage payments"
    }


# ============== INVOICE PAYMENTS ==============

@router.post("/invoice/{invoice_id}/pay", response_model=PaymentResponse)
async def create_invoice_payment(
    invoice_id: str,
    origin_url: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a payment session for an invoice"""
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Invoice already paid")
    
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not tenant or not tenant.get("stripe_connect_account_id"):
        raise HTTPException(status_code=400, detail="Stripe account not connected")
    
    account_id = tenant["stripe_connect_account_id"]
    
    # Get platform fee
    tier = await get_tenant_tier(current_user.tenant_id)
    fee_percent = get_platform_fee_percent(tier)
    
    amount = float(invoice.get("total", 0))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid invoice amount")
    
    # Calculate platform fee (in cents)
    amount_cents = int(amount * 100)
    platform_fee_cents = int(amount_cents * fee_percent)
    
    try:
        # Create checkout session with connected account
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": f"Invoice #{invoice.get('invoice_number', invoice_id[:8])}",
                        "description": "Payment for services"
                    }
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"{origin_url}/invoices?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin_url}/invoices?payment=cancelled",
            payment_intent_data={
                "application_fee_amount": platform_fee_cents,
                "transfer_data": {
                    "destination": account_id
                }
            },
            metadata={
                "type": "invoice",
                "invoice_id": invoice_id,
                "tenant_id": current_user.tenant_id,
                "platform_fee_percent": str(fee_percent * 100)
            }
        )
        
        # Record the payment attempt
        await db.payment_transactions.insert_one({
            "id": session.id,
            "tenant_id": current_user.tenant_id,
            "type": "invoice",
            "reference_id": invoice_id,
            "amount": amount,
            "platform_fee": platform_fee_cents / 100,
            "currency": "usd",
            "status": "pending",
            "stripe_session_id": session.id,
            "connected_account_id": account_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return PaymentResponse(url=session.url, session_id=session.id)
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== WEBSTORE PAYMENTS ==============

@router.post("/webstore/{webstore_id}/checkout", response_model=PaymentResponse)
async def create_webstore_checkout(
    webstore_id: str,
    checkout_data: WebstoreCheckoutRequest,
    origin_url: str
):
    """Create a payment session for webstore checkout (public endpoint)"""
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "status": "active"},
        {"_id": 0}
    )
    
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    tenant_id = webstore.get("tenant_id")
    tenant = await db.tenants.find_one(
        {"id": tenant_id},
        {"_id": 0}
    )
    
    if not tenant or not tenant.get("stripe_connect_account_id"):
        raise HTTPException(status_code=400, detail="Store cannot accept payments at this time")
    
    account_id = tenant["stripe_connect_account_id"]
    
    # Verify account can accept payments
    try:
        account = stripe.Account.retrieve(account_id)
        if not account.charges_enabled:
            raise HTTPException(status_code=400, detail="Store payment setup incomplete")
    except stripe.error.StripeError:
        raise HTTPException(status_code=400, detail="Payment system unavailable")
    
    # Get platform fee
    tier = await get_tenant_tier(tenant_id)
    fee_percent = get_platform_fee_percent(tier)
    
    # Extract items and customer_info from request body
    items = checkout_data.items
    customer_info = checkout_data.customer_info
    
    # Calculate total from server-side prices using the authoritative
    # webstore_products assignment (honors price_override + enabled flag +
    # tenant scoping). Any invalid/missing/disabled product ⇒ hard-fail;
    # previously the loop silently dropped unknown products, causing the
    # customer to pay less than their cart showed (and the attacker to
    # checkout arbitrary product_ids).
    line_items = []
    total_amount = 0.0
    validated_items: List[Dict[str, Any]] = []

    for item in items:
        # Product must belong to this tenant AND be active.
        product = await db.products.find_one(
            {"id": item.product_id, "tenant_id": tenant_id},
            {"_id": 0},
        )
        if not product or not product.get("is_active", True):
            raise HTTPException(
                status_code=400,
                detail=f"Product not available: {item.product_id}",
            )

        # And the product must be assigned + enabled on THIS webstore.
        assignment = await db.webstore_products.find_one(
            {
                "webstore_id": webstore_id,
                "product_id": item.product_id,
                "is_enabled": True,
            },
            {"_id": 0},
        )
        if not assignment:
            raise HTTPException(
                status_code=400,
                detail=f"'{product.get('name')}' is not available on this store",
            )

        # Variant check mirrors the manual-order path: variant_id only valid
        # if product has variants, and it must be an available variant.
        variant_additional_cost = 0.0
        variant_name = item.variant_name
        if item.variant_id:
            variants = product.get("variants") or []
            if not variants:
                raise HTTPException(
                    status_code=400,
                    detail=f"'{product.get('name')}' has no variants — variant_id invalid",
                )
            matched = next((v for v in variants if v.get("id") == item.variant_id), None)
            if not matched or not matched.get("is_available", True):
                raise HTTPException(
                    status_code=400,
                    detail=f"Variant unavailable for '{product.get('name')}'",
                )
            variant_additional_cost = float(matched.get("additional_cost", 0) or 0)
            variant_name = variant_name or matched.get("name")

        quantity = max(int(item.quantity or 1), 1)
        base_price = float(assignment.get("price_override") or product.get("retail_price", 0) or 0)
        effective_price = round(base_price + variant_additional_cost, 2)
        if effective_price <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid price for '{product.get('name')}'",
            )

        total_amount += effective_price * quantity

        product_name = product.get("name", "Product")
        if variant_name:
            product_name = f"{product_name} - {variant_name}"

        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": int(round(effective_price * 100)),
                "product_data": {"name": product_name},
            },
            "quantity": quantity,
        })
        validated_items.append({
            "product_id": item.product_id,
            "variant_id": item.variant_id,
            "variant_name": variant_name,
            "quantity": quantity,
            "price": effective_price,
        })
    
    if not line_items or total_amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid order items")
    
    # Calculate platform fee
    total_cents = int(total_amount * 100)
    platform_fee_cents = int(total_cents * fee_percent)
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=f"{origin_url}/store/{webstore_id}?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin_url}/store/{webstore_id}?payment=cancelled",
            customer_email=customer_info.email,
            payment_intent_data={
                "application_fee_amount": platform_fee_cents,
                "transfer_data": {
                    "destination": account_id
                }
            },
            metadata={
                "type": "webstore_order",
                "webstore_id": webstore_id,
                "tenant_id": tenant_id,
                "customer_name": customer_info.name or "",
                "customer_email": customer_info.email or "",
                "customer_phone": customer_info.phone or "",
                "shipping_address": customer_info.shipping_address or "",
                "platform_fee_percent": str(fee_percent * 100)
            }
        )
        
        # Record the payment attempt. Store the server-validated items so the
        # webhook uses the authoritative prices (never re-compute from the
        # raw client cart, which can be tampered with after submit).
        await db.payment_transactions.insert_one({
            "id": session.id,
            "tenant_id": tenant_id,
            "type": "webstore_order",
            "reference_id": webstore_id,
            "amount": total_amount,
            "platform_fee": platform_fee_cents / 100,
            "currency": "usd",
            "status": "pending",
            "stripe_session_id": session.id,
            "connected_account_id": account_id,
            "customer_info": customer_info.model_dump(),
            "items": validated_items,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return PaymentResponse(url=session.url, session_id=session.id)
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment-status/{session_id}")
async def get_payment_status(session_id: str):
    """Return the payment status for a Stripe Checkout session (public).

    If the session is `paid` and came from a webstore checkout, this also
    idempotently finalizes the webstore order (fallback for the case where
    the browser returns to the success URL before the webhook lands).
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    metadata = _extract_metadata(session)
    tenant_id_from_session = metadata.get("tenant_id")
    invoice_id_from_session = metadata.get("invoice_id")

    if session.payment_status == "paid":
        now_iso = datetime.now(timezone.utc).isoformat()
        # Update our ledger row idempotently.
        await db.payment_transactions.update_one(
            {"stripe_session_id": session_id, "status": {"$ne": "paid"}},
            {"$set": {
                "status": "paid",
                "paid_at": now_iso,
                "updated_at": now_iso,
                "stripe_payment_intent": getattr(session, "payment_intent", None),
            }},
        )
        transaction = await db.payment_transactions.find_one(
            {"stripe_session_id": session_id}, {"_id": 0}
        )
        tenant_id = (transaction or {}).get("tenant_id") or tenant_id_from_session
        reference_id = (transaction or {}).get("reference_id") or invoice_id_from_session

        if reference_id and ((transaction or {}).get("type") == "invoice" or metadata.get("type") == "invoice"):
            await _mark_invoice_paid(
                reference_id=reference_id,
                tenant_id=tenant_id,
                session_id=session_id,
                amount=(session.amount_total / 100 if getattr(session, "amount_total", None) else None),
                currency=getattr(session, "currency", None),
            )

        await _record_stripe_event(
            tenant_id=tenant_id,
            event_type="payment_status_check",
            status="paid",
            session_id=session_id,
            reference_id=reference_id,
            amount=(session.amount_total / 100 if getattr(session, "amount_total", None) else None),
            currency=getattr(session, "currency", None),
            message="payment-status endpoint confirmed paid",
        )

        if transaction:
            if transaction.get("type") == "webstore_order":
                # Fixes Flow-B bugs #1–#4: finalize into webstore_orders_v2
                # via the canonical path (job creation, commission calc,
                # payout credit all flow through).
                from routes.webstores import finalize_webstore_stripe_checkout
                try:
                    await finalize_webstore_stripe_checkout(session_id)
                except Exception as exc:
                    logger.exception(f"finalize_webstore_stripe_checkout failed for {session_id}: {exc}")
    elif session.status in ["expired", "canceled"] or session.payment_status in ["unpaid", "no_payment_required"]:
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.payment_transactions.update_one(
            {"stripe_session_id": session_id, "status": {"$nin": ["paid", "failed", "expired", "cancelled"]}},
            {
                "$set": {
                    "status": "expired" if session.status == "expired" else "cancelled",
                    "updated_at": now_iso,
                }
            },
        )
        await _record_stripe_event(
            tenant_id=tenant_id_from_session,
            event_type="payment_status_check",
            status="expired" if session.status == "expired" else "cancelled",
            session_id=session_id,
            reference_id=invoice_id_from_session,
            amount=(session.amount_total / 100 if getattr(session, "amount_total", None) else None),
            currency=getattr(session, "currency", None),
            message="payment-status endpoint found non-paid checkout session",
        )

    return {
        "status": session.status,
        "payment_status": session.payment_status,
        "amount_total": session.amount_total / 100 if session.amount_total else 0,
        "currency": session.currency,
    }


# ============== PAYMENTS WEBHOOK ==============

STRIPE_CONNECT_WEBHOOK_SECRET = os.environ.get("STRIPE_CONNECT_WEBHOOK_SECRET") or os.environ.get("STRIPE_WEBHOOK_SECRET")


@router.post("/webhook")
async def stripe_connect_webhook(request: Request):
    """Handle Stripe Connect webhooks.

    Verifies the stripe-signature header when STRIPE_CONNECT_WEBHOOK_SECRET
    (or STRIPE_WEBHOOK_SECRET) is set. In local/dev without a secret we fall
    back to parsing without verification — but logs a warning so it's visible
    in production.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        if STRIPE_CONNECT_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_CONNECT_WEBHOOK_SECRET
            )
        else:
            logger.warning("Stripe Connect webhook received without signature verification — set STRIPE_CONNECT_WEBHOOK_SECRET")
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        logger.warning(f"Rejected webhook payload: {exc}")
        raise HTTPException(status_code=400, detail="Invalid payload or signature")

    if event.type == "checkout.session.completed":
        session = event.data.object
        metadata = _extract_metadata(session)
        tenant_id = metadata.get("tenant_id")
        reference_id = metadata.get("invoice_id")
        now_iso = datetime.now(timezone.utc).isoformat()

        await db.payment_transactions.update_one(
            {"stripe_session_id": session.id},
            {"$set": {
                "status": "paid" if session.payment_status == "paid" else "pending",
                "updated_at": now_iso,
                "paid_at": now_iso if session.payment_status == "paid" else None,
                "stripe_payment_intent": getattr(session, "payment_intent", None),
            }},
        )

        transaction = await db.payment_transactions.find_one(
            {"stripe_session_id": session.id}, {"_id": 0}
        )

        transaction_tenant = (transaction or {}).get("tenant_id") or tenant_id
        transaction_reference = (transaction or {}).get("reference_id") or reference_id

        if session.payment_status == "paid":
            if (transaction and transaction.get("type") == "invoice") or metadata.get("type") == "invoice":
                await _mark_invoice_paid(
                    reference_id=transaction_reference,
                    tenant_id=transaction_tenant,
                    session_id=session.id,
                    amount=(session.amount_total / 100 if getattr(session, "amount_total", None) else None),
                    currency=getattr(session, "currency", None),
                )
            elif transaction and transaction.get("type") == "webstore_order":
                # Fixes Flow-B bugs #1–#5: finalize into the canonical
                # webstore_orders_v2 collection via the webstores helper.
                from routes.webstores import finalize_webstore_stripe_checkout
                try:
                    await finalize_webstore_stripe_checkout(session.id)
                except Exception as exc:
                    logger.exception(f"webhook finalize failed for {session.id}: {exc}")

            await _record_stripe_event(
                tenant_id=transaction_tenant,
                event_type=event.type,
                status="paid",
                session_id=session.id,
                reference_id=transaction_reference,
                amount=(session.amount_total / 100 if getattr(session, "amount_total", None) else None),
                currency=getattr(session, "currency", None),
                message="checkout.session.completed processed",
            )

    elif event.type == "checkout.session.expired":
        session = event.data.object
        metadata = _extract_metadata(session)
        tenant_id = metadata.get("tenant_id")
        now_iso = datetime.now(timezone.utc).isoformat()

        await db.payment_transactions.update_one(
            {"stripe_session_id": session.id, "status": {"$ne": "paid"}},
            {"$set": {"status": "expired", "updated_at": now_iso}},
        )

        await _record_stripe_event(
            tenant_id=tenant_id,
            event_type=event.type,
            status="expired",
            session_id=session.id,
            reference_id=metadata.get("invoice_id"),
            amount=(session.amount_total / 100 if getattr(session, "amount_total", None) else None),
            currency=getattr(session, "currency", None),
            message="checkout.session.expired received",
        )

    elif event.type == "payment_intent.payment_failed":
        payment_intent = event.data.object
        metadata = _extract_metadata(payment_intent)
        tenant_id = metadata.get("tenant_id")
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.payment_transactions.update_many(
            {
                "$or": [
                    {"stripe_payment_intent": payment_intent.id},
                    {"stripe_session_id": metadata.get("session_id")},
                ]
            },
            {
                "$set": {
                    "status": "failed",
                    "updated_at": now_iso,
                    "failure_message": getattr(payment_intent, "last_payment_error", {}).get("message")
                    if isinstance(getattr(payment_intent, "last_payment_error", None), dict)
                    else None,
                }
            },
        )

        await _record_stripe_event(
            tenant_id=tenant_id,
            event_type=event.type,
            status="failed",
            session_id=metadata.get("session_id"),
            reference_id=metadata.get("invoice_id"),
            amount=(payment_intent.amount / 100 if getattr(payment_intent, "amount", None) else None),
            currency=getattr(payment_intent, "currency", None),
            message="payment_intent.payment_failed received",
        )

    elif event.type == "account.updated":
        account = event.data.object
        await db.tenants.update_one(
            {"stripe_connect_account_id": account.id},
            {"$set": {
                "stripe_connect_charges_enabled": account.charges_enabled,
                "stripe_connect_payouts_enabled": account.payouts_enabled,
                "stripe_connect_updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )

    elif event.type == "charge.dispute.created":
        dispute = event.data.object
        metadata = _extract_metadata(dispute)
        await _record_stripe_event(
            tenant_id=metadata.get("tenant_id"),
            event_type=event.type,
            status="open",
            session_id=metadata.get("session_id"),
            reference_id=metadata.get("invoice_id"),
            amount=(dispute.amount / 100 if getattr(dispute, "amount", None) else None),
            currency=getattr(dispute, "currency", None),
            message=f"Dispute opened: {getattr(dispute, 'reason', 'unknown')}",
        )

    return {"received": True}


@router.get("/tenant-dashboard")
async def get_tenant_stripe_dashboard(current_user: UserInDB = Depends(get_current_active_user)):
    """Tenant-visible Stripe operations dashboard.

    Includes transaction ledger, payouts, balances, disputes/failures, and
    recent webhook/status events for reconciliation.
    """
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0, "stripe_connect_account_id": 1},
    )
    account_id = (tenant or {}).get("stripe_connect_account_id")
    connect_status = await get_connect_status(current_user)

    if not account_id:
        return {
            "connected": False,
            "connect_status": connect_status.model_dump() if hasattr(connect_status, "model_dump") else connect_status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "payments_summary": {
                "paid_count": 0,
                "pending_count": 0,
                "failed_count": 0,
                "paid_total": 0,
                "pending_total": 0,
            },
            "recent_payments": [],
            "recent_failed_payments": [],
            "recent_payouts": [],
            "recent_disputes": [],
            "recent_events": [],
        }

    transactions = await db.payment_transactions.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(300)

    invoice_reference_ids = [
        tx.get("reference_id")
        for tx in transactions
        if tx.get("type") == "invoice" and tx.get("reference_id")
    ]
    invoice_status_map: Dict[str, str] = {}
    if invoice_reference_ids:
        invoices = await db.invoices.find(
            {"tenant_id": current_user.tenant_id, "id": {"$in": invoice_reference_ids}},
            {"_id": 0, "id": 1, "status": 1},
        ).to_list(500)
        invoice_status_map.update({doc["id"]: doc.get("status", "unknown") for doc in invoices})

        unresolved = [ref for ref in invoice_reference_ids if ref not in invoice_status_map]
        if unresolved:
            legacy_invoices = await db.order_quotes.find(
                {
                    "tenant_id": current_user.tenant_id,
                    "type": "invoice",
                    "id": {"$in": unresolved},
                },
                {"_id": 0, "id": 1, "status": 1},
            ).to_list(500)
            invoice_status_map.update({doc["id"]: doc.get("status", "unknown") for doc in legacy_invoices})

    paid_transactions = [tx for tx in transactions if tx.get("status") == "paid"]
    pending_transactions = [tx for tx in transactions if tx.get("status") == "pending"]
    failed_transactions = [tx for tx in transactions if tx.get("status") in ["failed", "expired", "cancelled"]]

    recent_payments = []
    for tx in transactions[:40]:
        item = {
            "session_id": tx.get("stripe_session_id") or tx.get("id"),
            "type": tx.get("type"),
            "reference_id": tx.get("reference_id"),
            "status": tx.get("status"),
            "amount": float(tx.get("amount", 0) or 0),
            "currency": tx.get("currency", "usd"),
            "platform_fee": tx.get("platform_fee"),
            "created_at": tx.get("created_at"),
            "paid_at": tx.get("paid_at"),
        }
        if tx.get("type") == "invoice":
            item["invoice_status"] = invoice_status_map.get(tx.get("reference_id"), "unknown")
        recent_payments.append(item)

    payouts: List[Dict[str, Any]] = []
    balances = {"available_usd": 0.0, "pending_usd": 0.0}
    disputes: List[Dict[str, Any]] = []
    stripe_errors: List[str] = []

    try:
        balance_obj = stripe.Balance.retrieve(stripe_account=account_id)
        balances["available_usd"] = sum((entry.amount or 0) for entry in (balance_obj.available or []) if entry.currency == "usd") / 100
        balances["pending_usd"] = sum((entry.amount or 0) for entry in (balance_obj.pending or []) if entry.currency == "usd") / 100
    except Exception as exc:
        stripe_errors.append(f"balance: {str(exc)}")

    try:
        payout_obj = stripe.Payout.list(stripe_account=account_id, limit=25)
        for payout in payout_obj.data:
            payouts.append(
                {
                    "id": payout.id,
                    "amount": (payout.amount or 0) / 100,
                    "currency": payout.currency,
                    "status": payout.status,
                    "arrival_date": datetime.fromtimestamp(payout.arrival_date, tz=timezone.utc).isoformat()
                    if getattr(payout, "arrival_date", None)
                    else None,
                    "created": datetime.fromtimestamp(payout.created, tz=timezone.utc).isoformat()
                    if getattr(payout, "created", None)
                    else None,
                    "method": payout.method,
                }
            )
    except Exception as exc:
        stripe_errors.append(f"payouts: {str(exc)}")

    try:
        dispute_obj = stripe.Dispute.list(limit=20)
        for dispute in dispute_obj.data:
            include = False
            transfer_destination = None
            if getattr(dispute, "charge", None):
                try:
                    charge = stripe.Charge.retrieve(dispute.charge)
                    transfer_destination = (charge.get("transfer_data") or {}).get("destination") if isinstance(charge, dict) else None
                    include = transfer_destination == account_id
                except Exception:
                    include = False

            if include:
                disputes.append(
                    {
                        "id": dispute.id,
                        "amount": (dispute.amount or 0) / 100,
                        "currency": dispute.currency,
                        "status": dispute.status,
                        "reason": dispute.reason,
                        "created": datetime.fromtimestamp(dispute.created, tz=timezone.utc).isoformat()
                        if getattr(dispute, "created", None)
                        else None,
                        "charge_id": dispute.charge,
                        "transfer_destination": transfer_destination,
                    }
                )
    except Exception as exc:
        stripe_errors.append(f"disputes: {str(exc)}")

    recent_events = await db.stripe_connect_events.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0, "raw": 0},
    ).sort("created_at", -1).to_list(60)

    payouts_total = sum(item.get("amount", 0) for item in payouts)
    payouts_paid_total = sum(item.get("amount", 0) for item in payouts if item.get("status") == "paid")

    return {
        "connected": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stripe_account_id": account_id,
        "connect_status": connect_status.model_dump() if hasattr(connect_status, "model_dump") else connect_status,
        "balances": balances,
        "payments_summary": {
            "paid_count": len(paid_transactions),
            "pending_count": len(pending_transactions),
            "failed_count": len(failed_transactions),
            "paid_total": round(sum(float(tx.get("amount", 0) or 0) for tx in paid_transactions), 2),
            "pending_total": round(sum(float(tx.get("amount", 0) or 0) for tx in pending_transactions), 2),
        },
        "payouts_summary": {
            "count": len(payouts),
            "total": round(payouts_total, 2),
            "paid_total": round(payouts_paid_total, 2),
            "in_transit_total": round(sum(item.get("amount", 0) for item in payouts if item.get("status") in ["pending", "in_transit"]), 2),
        },
        "recent_payments": recent_payments,
        "recent_failed_payments": [
            {
                "session_id": tx.get("stripe_session_id") or tx.get("id"),
                "type": tx.get("type"),
                "reference_id": tx.get("reference_id"),
                "status": tx.get("status"),
                "amount": float(tx.get("amount", 0) or 0),
                "created_at": tx.get("created_at"),
                "updated_at": tx.get("updated_at"),
                "failure_message": tx.get("failure_message"),
            }
            for tx in failed_transactions[:25]
        ],
        "recent_payouts": payouts,
        "recent_disputes": disputes,
        "recent_events": recent_events,
        "stripe_errors": stripe_errors,
    }


@router.post("/reconcile-invoices")
async def reconcile_invoice_payments(current_user: UserInDB = Depends(get_current_active_user)):
    """Best-effort reconciliation for paid Stripe invoice transactions.

    Use this when tenants open invoice views to recover from delayed/missed webhook
    deliveries. It only touches transactions already marked `paid` in our ledger.
    """
    transactions = await db.payment_transactions.find(
        {
            "tenant_id": current_user.tenant_id,
            "type": "invoice",
            "status": "paid",
        },
        {"_id": 0},
    ).sort("created_at", -1).to_list(200)

    fixed = 0
    checked = 0
    for tx in transactions:
        reference_id = tx.get("reference_id")
        session_id = tx.get("stripe_session_id")
        if not reference_id or not session_id:
            continue

        checked += 1
        invoice, _ = await _find_invoice_document(reference_id, current_user.tenant_id)
        if not invoice or invoice.get("status") == "paid":
            continue

        await _mark_invoice_paid(
            reference_id=reference_id,
            tenant_id=current_user.tenant_id,
            session_id=session_id,
            amount=float(tx.get("amount", 0) or 0),
            currency=tx.get("currency", "usd"),
        )
        fixed += 1

    await _record_stripe_event(
        tenant_id=current_user.tenant_id,
        event_type="manual_reconcile",
        status="completed",
        message=f"Checked {checked} paid invoice transactions; fixed {fixed} invoice rows",
    )

    return {
        "checked_paid_transactions": checked,
        "fixed_invoices": fixed,
    }
