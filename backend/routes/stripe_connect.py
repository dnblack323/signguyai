"""
Stripe Connect Routes — API Layer

Route handlers for Stripe Connect account management, invoice payments,
webstore payments, webhooks, and the tenant Stripe dashboard.

All Stripe business logic (platform fees, account caching, event helpers,
finalization) lives in services/stripe_service.py. This module is a thin
HTTP layer that delegates to that service.
"""

import os
import stripe
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

# Standalone DB connection (avoids circular import through server.py).
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "signguy_ai")
_client = AsyncIOMotorClient(MONGO_URL)
db = _client[DB_NAME]
logger = logging.getLogger(__name__)

from models import UserInDB
from core.auth_deps import get_current_active_user

# Stripe service — all business logic lives here
from services.stripe_service import (
    PLATFORM_FEES,
    get_platform_fee_percent,
    get_platform_fee_config,
    calculate_platform_fee_cents,
    WEBSTORE_SURCHARGE_PERCENT,
    get_stripe_mode,
    get_tenant_tier,
    is_wrong_mode_error,
    scrub_stale_connect_account,
    extract_metadata,
    find_invoice_document,
    record_stripe_event,
    mark_invoice_paid,
    finalize_webstore_stripe_checkout,
)

router = APIRouter(prefix="/stripe-connect", tags=["Stripe Connect"])

# Ensure Stripe key is set for any direct stripe.* calls in route handlers.
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY")


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


# Utility functions are imported from services.stripe_service above.


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
    # Part 4: Optional checkout donation (in dollars). Server validates against
    # the store's donation_amount_options + allow_custom_donation flags.
    donation_amount: Optional[float] = Field(default=0.0, ge=0)


class FeePreview(BaseModel):
    """Net-deposit preview shown to tenants before sending a payment link."""
    amount: float
    stripe_estimated_cents: int       # Stripe's processing fee estimate
    platform_fee_cents: int           # Our application_fee_amount
    platform_fee_label: str           # human-readable e.g. "2.2% + $0.20"
    is_webstore: bool
    tenant_receives_cents: int        # amount − stripe − platform
    note: str = "Stripe's actual processing fee is computed at settlement; this is an estimate (2.9% + $0.30)."


@router.get("/fee-preview", response_model=FeePreview)
async def fee_preview(
    amount: float,
    is_webstore: bool = False,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Compute the net-deposit breakdown for a given amount and tier.

    Used by the UI to show 'You'll receive ~$X' before sending a payment link
    or activating a webstore checkout. No Stripe API call — pure math.
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")

    tier = await get_tenant_tier(current_user.tenant_id)
    cfg = get_platform_fee_config(tier)
    amount_cents = int(round(amount * 100))
    platform_fee_cents = calculate_platform_fee_cents(tier, amount_cents, is_webstore=is_webstore)

    # Stripe's standard US-card fee: 2.9% + 30c — best public estimate.
    stripe_fee_cents = int(round(amount_cents * 0.029)) + 30

    tenant_receives = max(amount_cents - stripe_fee_cents - platform_fee_cents, 0)

    effective_percent = (cfg["percent"] + (WEBSTORE_SURCHARGE_PERCENT if is_webstore else 0.0)) * 100
    flat_dollars = cfg["flat_cents"] / 100
    label = f"{effective_percent:.1f}% + ${flat_dollars:.2f}"

    return FeePreview(
        amount=amount,
        stripe_estimated_cents=stripe_fee_cents,
        platform_fee_cents=platform_fee_cents,
        platform_fee_label=label,
        is_webstore=is_webstore,
        tenant_receives_cents=tenant_receives,
    )





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
            await scrub_stale_connect_account(
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
        if is_wrong_mode_error(e) or "No such account" in str(e):
            await scrub_stale_connect_account(
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
                    await scrub_stale_connect_account(
                        current_user.tenant_id,
                        existing_account_id,
                        "create_account_detected_test_account_on_live_platform",
                    )
                    account_id = None
                else:
                    account_id = existing_account_id
            except stripe.error.InvalidRequestError as e:
                # Either deleted, or the classic cross-mode ghost account.
                if is_wrong_mode_error(e) or "No such account" in str(e):
                    await scrub_stale_connect_account(
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
        if is_wrong_mode_error(e) or "No such account" in str(e):
            await scrub_stale_connect_account(
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
        await scrub_stale_connect_account(
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
    
    # Calculate platform fee (in cents): base percent + flat cents per landing page
    amount_cents = int(amount * 100)
    platform_fee_cents = calculate_platform_fee_cents(tier, amount_cents, is_webstore=False)
    
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


class SendPaymentLinkRequest(BaseModel):
    """Optional override email when sending a payment link"""
    customer_email: Optional[str] = None


@router.post("/invoice/{invoice_id}/send-payment-link")
async def send_invoice_payment_link(
    invoice_id: str,
    body: SendPaymentLinkRequest,
    origin_url: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Generate a Stripe Checkout link for an invoice and email it to the customer.

    Returns the checkout URL plus whether the email was successfully dispatched.
    The URL can also be copied and shared manually.
    """
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Invoice is already paid")

    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0},
    )
    if not tenant or not tenant.get("stripe_connect_account_id"):
        raise HTTPException(status_code=400, detail="Stripe account not connected")

    account_id = tenant["stripe_connect_account_id"]
    tier = await get_tenant_tier(current_user.tenant_id)
    fee_percent = get_platform_fee_percent(tier)

    amount = float(invoice.get("grand_total") or invoice.get("total") or 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid invoice amount")

    amount_cents = int(amount * 100)
    platform_fee_cents = calculate_platform_fee_cents(tier, amount_cents, is_webstore=False)

    # Determine destination email: use override → invoice customer → fallback
    customer_email = (body.customer_email or "").strip()
    customer_doc = None
    if not customer_email and invoice.get("customer_id"):
        customer_doc = await db.customers.find_one(
            {"id": invoice["customer_id"], "tenant_id": current_user.tenant_id},
            {"_id": 0, "email": 1, "name": 1},
        )
        if customer_doc:
            customer_email = customer_doc.get("email", "").strip()

    invoice_number = invoice.get("invoice_number") or invoice_id[:8].upper()
    company_name = tenant.get("company_name") or "Your Service Provider"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": f"Invoice #{invoice_number}",
                        "description": f"Payment to {company_name}",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{origin_url}/invoices?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin_url}/invoices?payment=cancelled",
            customer_email=customer_email or None,
            payment_intent_data={
                "application_fee_amount": platform_fee_cents,
                "transfer_data": {"destination": account_id},
            },
            metadata={
                "type": "invoice",
                "invoice_id": invoice_id,
                "tenant_id": current_user.tenant_id,
                "platform_fee_percent": str(fee_percent * 100),
            },
        )

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
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Send email if we have an address
    email_sent = False
    email_error = None
    if customer_email:
        from services.email_service import email_service
        customer_name = (
            invoice.get("customer_name")
            or (customer_doc.get("name") if customer_doc else None)
            or "Valued Customer"
        )
        html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:30px 0;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">
    <div style="background:#0D9488;padding:28px 32px;">
      <h1 style="color:#ffffff;margin:0;font-size:22px;">{company_name}</h1>
    </div>
    <div style="padding:32px;">
      <h2 style="margin:0 0 12px;font-size:20px;color:#111;">Invoice #{invoice_number} — Payment Request</h2>
      <p style="color:#555;margin:0 0 20px;">Hi {customer_name},</p>
      <p style="color:#555;margin:0 0 20px;">
        You have an invoice from <strong>{company_name}</strong> for
        <strong>${amount:,.2f}</strong> that is ready for payment.
      </p>
      <div style="text-align:center;margin:28px 0;">
        <a href="{session.url}"
           style="display:inline-block;background:#0D9488;color:#ffffff;text-decoration:none;
                  padding:14px 32px;border-radius:6px;font-weight:bold;font-size:16px;">
          Pay Invoice — ${amount:,.2f}
        </a>
      </div>
      <p style="color:#888;font-size:13px;margin:0 0 8px;">
        Or copy this link into your browser:
      </p>
      <p style="background:#f4f4f4;padding:10px 14px;border-radius:4px;font-size:12px;
                word-break:break-all;color:#333;margin:0 0 24px;">
        {session.url}
      </p>
      <p style="color:#aaa;font-size:12px;margin:0;">
        This payment link is secure and powered by Stripe. You do not need to create an account.
      </p>
    </div>
  </div>
</body>
</html>"""
        result = await email_service.send_email(
            to_email=customer_email,
            subject=f"Invoice #{invoice_number} — Payment of ${amount:,.2f} from {company_name}",
            html_content=html_body,
            plain_content=(
                f"Hi {customer_name},\n\n"
                f"Please pay Invoice #{invoice_number} (${amount:,.2f}) using the link below:\n\n"
                f"{session.url}\n\n"
                f"Powered by Stripe — no account required."
            ),
            tenant_id=current_user.tenant_id,
        )
        email_sent = result.get("success", False)
        if not email_sent:
            email_error = result.get("error")

    return {
        "url": session.url,
        "session_id": session.id,
        "customer_email": customer_email,
        "email_sent": email_sent,
        "email_error": email_error,
        "amount": amount,
        "invoice_number": invoice_number,
    }


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

    # ============== PART 4: Event Store fundraiser & shipping/handling =========
    # All values below are derived server-side from locked_settings + store
    # config — the frontend is never trusted with cost/fee math.
    locked = webstore.get("locked_settings") or {}

    # 1) Shipping/handling: pulled from locked_settings (or bundle when set).
    if locked.get("shipping_handling_enabled"):
        shipping_handling_amount = float(locked.get("shipping_handling_fee") or 0)
        shipping_handling_label = locked.get("shipping_handling_label") or "Shipping & Handling"
    else:
        ship = float(locked.get("shipping_fee") or 0)
        hand = float(locked.get("handling_fee") or 0)
        shipping_handling_amount = round(ship + hand, 2)
        shipping_handling_label = "Shipping & Handling"
    shipping_handling_amount = max(round(shipping_handling_amount, 2), 0.0)

    if shipping_handling_amount > 0:
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": int(round(shipping_handling_amount * 100)),
                "product_data": {"name": shipping_handling_label},
            },
            "quantity": 1,
        })

    # 2) Donation: only valid when allow_checkout_donations=true. Validated
    #    against the store's preset list + allow_custom_donation flag.
    donation_amount = round(float(checkout_data.donation_amount or 0), 2)
    donations_enabled = bool(webstore.get("allow_checkout_donations"))
    if donation_amount > 0:
        if not donations_enabled:
            raise HTTPException(
                status_code=400,
                detail="This store is not accepting donations at checkout",
            )
        # Parse presets from the store's donation_amount_options string.
        presets_raw = webstore.get("donation_amount_options") or ""
        import re as _re_d
        preset_vals: list[float] = []
        for tok in _re_d.split(r"[\s,;|]+", str(presets_raw)):
            cleaned = tok.replace("$", "").replace(",", "").strip()
            if not cleaned:
                continue
            try:
                v = float(cleaned)
                if v > 0:
                    preset_vals.append(round(v, 2))
            except ValueError:
                pass
        allow_custom = bool(webstore.get("allow_custom_donation"))
        matches_preset = any(abs(donation_amount - p) < 0.005 for p in preset_vals)
        if not matches_preset and not allow_custom:
            raise HTTPException(
                status_code=400,
                detail="Donation amount must match one of the allowed preset amounts",
            )
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": int(round(donation_amount * 100)),
                "product_data": {"name": "Donation"},
            },
            "quantity": 1,
        })

    # 3) Profit allocation: server-only computation. Stored on the payment
    #    transaction so the webhook/finalize step can roll it into
    #    total_profit_allocated without trusting any client-supplied value.
    profit_allocation_amount = 0.0
    if (webstore.get("store_type") == "event"
            and webstore.get("profit_allocation_enabled")):
        alloc_type = (webstore.get("profit_allocation_type") or "").lower()
        # Approximate profit ≈ sum((retail − base_cost) × qty) so the value
        # available at checkout matches what create_webstore_order will see.
        approx_profit = 0.0
        total_qty = 0
        for v in validated_items:
            prod = await db.products.find_one(
                {"id": v["product_id"], "tenant_id": tenant_id},
                {"_id": 0, "base_cost": 1, "variants": 1},
            )
            unit_cost = float((prod or {}).get("base_cost") or 0)
            if v.get("variant_id"):
                for variant in (prod or {}).get("variants") or []:
                    if variant.get("id") == v["variant_id"]:
                        unit_cost += float(variant.get("additional_cost") or 0)
                        break
            qty = int(v.get("quantity") or 1)
            total_qty += qty
            approx_profit += max(float(v["price"]) - unit_cost, 0.0) * qty
        if alloc_type == "percentage":
            pct = float(webstore.get("profit_allocation_percentage") or 0)
            if pct > 0 and approx_profit > 0:
                profit_allocation_amount = approx_profit * (pct / 100.0)
        elif alloc_type == "fixed_per_item":
            per_item = float(webstore.get("fixed_amount_per_item") or 0)
            if per_item > 0:
                profit_allocation_amount = per_item * total_qty
        cap = webstore.get("fundraiser_cap_amount")
        if cap is not None and float(cap) > 0:
            already = float(webstore.get("total_profit_allocated") or 0)
            remaining = max(float(cap) - already, 0.0)
            profit_allocation_amount = min(profit_allocation_amount, remaining)
        profit_allocation_amount = round(max(profit_allocation_amount, 0.0), 2)

    # Final grand total includes products + shipping/handling + donation.
    # Profit allocation is NOT added — it comes out of the shop's profit,
    # not the customer's wallet.
    total_amount = round(total_amount + shipping_handling_amount + donation_amount, 2)

    # Calculate platform fee: webstore tier gets +2% surcharge on top of base
    total_cents = int(total_amount * 100)
    platform_fee_cents = calculate_platform_fee_cents(tier, total_cents, is_webstore=True)
    
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
                "platform_fee_percent": str(fee_percent * 100),
                "donation_amount": f"{donation_amount:.2f}",
                "profit_allocation_amount": f"{profit_allocation_amount:.2f}",
                "shipping_handling_amount": f"{shipping_handling_amount:.2f}",
                "fundraiser_enabled": "true" if webstore.get("fundraiser_enabled") else "false",
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
            "donation_amount": donation_amount,
            "profit_allocation_amount": profit_allocation_amount,
            "shipping_handling_amount": shipping_handling_amount,
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

    metadata = extract_metadata(session)
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
            await mark_invoice_paid(
                reference_id=reference_id,
                tenant_id=tenant_id,
                session_id=session_id,
                amount=(session.amount_total / 100 if getattr(session, "amount_total", None) else None),
                currency=getattr(session, "currency", None),
            )

        await record_stripe_event(
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
        await record_stripe_event(
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
        metadata = extract_metadata(session)
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
                await mark_invoice_paid(
                    reference_id=transaction_reference,
                    tenant_id=transaction_tenant,
                    session_id=session.id,
                    amount=(session.amount_total / 100 if getattr(session, "amount_total", None) else None),
                    currency=getattr(session, "currency", None),
                )
            elif transaction and transaction.get("type") == "webstore_order":
                try:
                    await finalize_webstore_stripe_checkout(session.id)
                except Exception as exc:
                    logger.exception(f"webhook finalize failed for {session.id}: {exc}")

            await record_stripe_event(
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
        metadata = extract_metadata(session)
        tenant_id = metadata.get("tenant_id")
        now_iso = datetime.now(timezone.utc).isoformat()

        await db.payment_transactions.update_one(
            {"stripe_session_id": session.id, "status": {"$ne": "paid"}},
            {"$set": {"status": "expired", "updated_at": now_iso}},
        )

        await record_stripe_event(
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
        metadata = extract_metadata(payment_intent)
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

        await record_stripe_event(
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
        metadata = extract_metadata(dispute)
        await record_stripe_event(
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
        invoice, _ = await find_invoice_document(reference_id, current_user.tenant_id)
        if not invoice or invoice.get("status") == "paid":
            continue

        await mark_invoice_paid(
            reference_id=reference_id,
            tenant_id=current_user.tenant_id,
            session_id=session_id,
            amount=float(tx.get("amount", 0) or 0),
            currency=tx.get("currency", "usd"),
        )
        fixed += 1

    await record_stripe_event(
        tenant_id=current_user.tenant_id,
        event_type="manual_reconcile",
        status="completed",
        message=f"Checked {checked} paid invoice transactions; fixed {fixed} invoice rows",
    )

    return {
        "checked_paid_transactions": checked,
        "fixed_invoices": fixed,
    }
