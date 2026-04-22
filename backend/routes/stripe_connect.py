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
    
    try:
        account = stripe.Account.retrieve(account_id)
        tier = await get_tenant_tier(current_user.tenant_id)
        stripe_mode = get_stripe_mode()
        account_mode = "live" if getattr(account, "livemode", False) else "test"
        
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
    
    try:
        if existing_account_id:
            # Check if account exists and is valid
            try:
                account = stripe.Account.retrieve(existing_account_id)
                stripe_mode = get_stripe_mode()
                account_mode = "live" if getattr(account, "livemode", False) else "test"
                account_id = existing_account_id if stripe_mode == account_mode else None
            except stripe.error.InvalidRequestError:
                # Account doesn't exist, create new one
                account_id = None
        else:
            account_id = None
        
        if not account_id:
            # Create new Standard Connect account
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

    if session.payment_status == "paid":
        # Update our ledger row idempotently.
        await db.payment_transactions.update_one(
            {"stripe_session_id": session_id, "status": {"$ne": "paid"}},
            {"$set": {
                "status": "paid",
                "paid_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        transaction = await db.payment_transactions.find_one(
            {"stripe_session_id": session_id}, {"_id": 0}
        )
        if transaction:
            if transaction.get("type") == "invoice":
                await db.invoices.update_one(
                    {"id": transaction.get("reference_id")},
                    {"$set": {
                        "status": "paid",
                        "paid_at": datetime.now(timezone.utc).isoformat(),
                        "payment_method": "stripe",
                        "stripe_session_id": session_id,
                    }},
                )
            elif transaction.get("type") == "webstore_order":
                # Fixes Flow-B bugs #1–#4: finalize into webstore_orders_v2
                # via the canonical path (job creation, commission calc,
                # payout credit all flow through).
                from routes.webstores import finalize_webstore_stripe_checkout
                try:
                    await finalize_webstore_stripe_checkout(session_id)
                except Exception as exc:
                    logger.exception(f"finalize_webstore_stripe_checkout failed for {session_id}: {exc}")

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
        await db.payment_transactions.update_one(
            {"stripe_session_id": session.id},
            {"$set": {
                "status": "paid" if session.payment_status == "paid" else "pending",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )

        transaction = await db.payment_transactions.find_one(
            {"stripe_session_id": session.id}, {"_id": 0}
        )

        if transaction and session.payment_status == "paid":
            if transaction.get("type") == "invoice":
                await db.invoices.update_one(
                    {"id": transaction.get("reference_id")},
                    {"$set": {
                        "status": "paid",
                        "paid_at": datetime.now(timezone.utc).isoformat(),
                    }},
                )
            elif transaction.get("type") == "webstore_order":
                # Fixes Flow-B bugs #1–#5: finalize into the canonical
                # webstore_orders_v2 collection via the webstores helper.
                from routes.webstores import finalize_webstore_stripe_checkout
                try:
                    await finalize_webstore_stripe_checkout(session.id)
                except Exception as exc:
                    logger.exception(f"webhook finalize failed for {session.id}: {exc}")

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

    return {"received": True}
