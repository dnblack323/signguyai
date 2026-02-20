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
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

# Get auth and database from server (same as other routes)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import get_current_active_user, UserInDB, db

router = APIRouter(prefix="/stripe-connect", tags=["Stripe Connect"])

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY') or os.environ.get('STRIPE_API_KEY')

# Platform fee percentages by tier
PLATFORM_FEES = {
    "starter": 0.03,    # 3% for Tier 1
    "pro": 0.02,        # 2% for Tier 2
    "business": 0.01,   # 1% for Tier 3
}


class ConnectAccountResponse(BaseModel):
    """Response for connect account status"""
    connected: bool = False
    account_id: Optional[str] = None
    charges_enabled: bool = False
    payouts_enabled: bool = False
    onboarding_complete: bool = False
    platform_fee_percent: float = 3.0


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


def get_platform_fee_percent(tier: str) -> float:
    """Get platform fee percentage for a tier"""
    return PLATFORM_FEES.get(tier, 0.03)  # Default to 3%


async def get_tenant_tier(tenant_id: str) -> str:
    """Get tenant's subscription tier"""
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
            platform_fee_percent=get_platform_fee_percent(tier) * 100
        )
    
    account_id = tenant["stripe_connect_account_id"]
    
    try:
        account = stripe.Account.retrieve(account_id)
        tier = await get_tenant_tier(current_user.tenant_id)
        
        return ConnectAccountResponse(
            connected=True,
            account_id=account_id,
            charges_enabled=account.charges_enabled,
            payouts_enabled=account.payouts_enabled,
            onboarding_complete=account.details_submitted,
            platform_fee_percent=get_platform_fee_percent(tier) * 100
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
                account_id = existing_account_id
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
    request: Request,
    origin_url: str,
    items: list,  # List of {product_id, variant_id, quantity, price}
    customer_info: dict  # {name, email, phone, shipping_address}
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
    
    # Calculate total from server-side prices (don't trust frontend prices)
    line_items = []
    total_amount = 0
    
    for item in items:
        # Get actual product price from database
        product = await db.products.find_one(
            {"id": item.get("product_id")},
            {"_id": 0}
        )
        if not product:
            continue
        
        price = float(product.get("retail_price", 0))
        quantity = int(item.get("quantity", 1))
        total_amount += price * quantity
        
        product_name = product.get("name", "Product")
        if item.get("variant_name"):
            product_name += f" - {item.get('variant_name')}"
        
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": int(price * 100),
                "product_data": {
                    "name": product_name
                }
            },
            "quantity": quantity
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
            customer_email=customer_info.get("email"),
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
                "customer_name": customer_info.get("name", ""),
                "customer_email": customer_info.get("email", ""),
                "customer_phone": customer_info.get("phone", ""),
                "shipping_address": customer_info.get("shipping_address", ""),
                "platform_fee_percent": str(fee_percent * 100)
            }
        )
        
        # Record the payment attempt
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
            "customer_info": customer_info,
            "items": items,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return PaymentResponse(url=session.url, session_id=session.id)
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payment-status/{session_id}")
async def get_payment_status(session_id: str):
    """Get status of a payment session (public endpoint)"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Update our record
        if session.payment_status == "paid":
            transaction = await db.payment_transactions.find_one(
                {"stripe_session_id": session_id},
                {"_id": 0}
            )
            
            if transaction and transaction.get("status") != "completed":
                await db.payment_transactions.update_one(
                    {"stripe_session_id": session_id},
                    {
                        "$set": {
                            "status": "completed",
                            "paid_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                # Handle post-payment actions
                if transaction.get("type") == "invoice":
                    await db.invoices.update_one(
                        {"id": transaction.get("reference_id")},
                        {
                            "$set": {
                                "status": "paid",
                                "paid_at": datetime.now(timezone.utc).isoformat(),
                                "payment_method": "stripe",
                                "stripe_session_id": session_id
                            }
                        }
                    )
                elif transaction.get("type") == "webstore_order":
                    # Create the order
                    order_data = {
                        "id": f"ORD-{session_id[:8]}",
                        "webstore_id": transaction.get("reference_id"),
                        "tenant_id": transaction.get("tenant_id"),
                        "customer_name": transaction.get("customer_info", {}).get("name"),
                        "customer_email": transaction.get("customer_info", {}).get("email"),
                        "customer_phone": transaction.get("customer_info", {}).get("phone"),
                        "shipping_address": transaction.get("customer_info", {}).get("shipping_address"),
                        "items": transaction.get("items", []),
                        "total": transaction.get("amount"),
                        "status": "paid",
                        "payment_status": "paid",
                        "payment_method": "stripe",
                        "stripe_session_id": session_id,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.webstore_orders.insert_one(order_data)
        
        return {
            "status": session.status,
            "payment_status": session.payment_status,
            "amount_total": session.amount_total / 100 if session.amount_total else 0,
            "currency": session.currency
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== PAYMENTS WEBHOOK ==============

@router.post("/webhook")
async def stripe_connect_webhook(request: Request):
    """Handle Stripe Connect webhooks"""
    payload = await request.body()
    # Note: In production, verify webhook signature with stripe-signature header
    
    # For testing without webhook secret, just parse the event
    try:
        event = stripe.Event.construct_from(
            stripe.util.json.loads(payload), stripe.api_key
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    # Handle the event
    if event.type == "checkout.session.completed":
        session = event.data.object
        
        # Update transaction
        await db.payment_transactions.update_one(
            {"stripe_session_id": session.id},
            {
                "$set": {
                    "status": "completed" if session.payment_status == "paid" else "pending",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Get transaction details
        transaction = await db.payment_transactions.find_one(
            {"stripe_session_id": session.id},
            {"_id": 0}
        )
        
        if transaction and session.payment_status == "paid":
            if transaction.get("type") == "invoice":
                await db.invoices.update_one(
                    {"id": transaction.get("reference_id")},
                    {
                        "$set": {
                            "status": "paid",
                            "paid_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
    
    elif event.type == "account.updated":
        # Connected account was updated
        account = event.data.object
        await db.tenants.update_one(
            {"stripe_connect_account_id": account.id},
            {
                "$set": {
                    "stripe_connect_charges_enabled": account.charges_enabled,
                    "stripe_connect_payouts_enabled": account.payouts_enabled,
                    "stripe_connect_updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    return {"received": True}
