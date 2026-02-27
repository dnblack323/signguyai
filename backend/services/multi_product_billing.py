"""
Multi-Product Billing Service

Handles Stripe checkout, subscriptions, and processing fees for all 3 product lines.

RULES:
- Founder pricing ONLY for OS plans when tenant.is_founder=true AND founder_spots < 100
- Annual pricing ONLY for OS Business (standard and founder)
- Processing fees vary by plan and transaction type
"""

import os
import stripe
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException

from models.product_tiers import (
    ProductLine, PlanType, ProcessingFees, FOUNDER_SPOTS_TOTAL
)
from services.plan_configs import get_plan_config
from services.multi_product_gate import get_multi_product_feature_gate


# ============== STRIPE PRICE ID MAPPING ==============

def get_stripe_price_id(
    plan_type: PlanType,
    billing_interval: str = "monthly",
    is_founder: bool = False
) -> str:
    """
    Get the Stripe Price ID for a plan.
    
    Rules:
    - Founder pricing ONLY for OS plans
    - Annual pricing ONLY for OS Business
    """
    
    # OS Plans
    if plan_type == PlanType.OS_STARTER:
        if is_founder:
            return os.environ.get("STRIPE_PRICE_OS_STARTER_FOUNDER_MONTHLY")
        return os.environ.get("STRIPE_PRICE_OS_STARTER_MONTHLY")
    
    elif plan_type == PlanType.OS_PRO:
        if is_founder:
            return os.environ.get("STRIPE_PRICE_OS_PRO_FOUNDER_MONTHLY")
        return os.environ.get("STRIPE_PRICE_OS_PRO_MONTHLY")
    
    elif plan_type == PlanType.OS_BUSINESS:
        if is_founder:
            if billing_interval == "annual":
                return os.environ.get("STRIPE_PRICE_OS_BUSINESS_FOUNDER_ANNUAL")
            return os.environ.get("STRIPE_PRICE_OS_BUSINESS_FOUNDER_MONTHLY")
        else:
            if billing_interval == "annual":
                return os.environ.get("STRIPE_PRICE_OS_BUSINESS_ANNUAL")
            return os.environ.get("STRIPE_PRICE_OS_BUSINESS_MONTHLY")
    
    # Webstore Plans (no founder, no annual)
    elif plan_type == PlanType.WS_LAUNCH:
        return os.environ.get("STRIPE_PRICE_WS_LAUNCH_MONTHLY")
    elif plan_type == PlanType.WS_GROWTH:
        return os.environ.get("STRIPE_PRICE_WS_GROWTH_MONTHLY")
    elif plan_type == PlanType.WS_SCALE:
        return os.environ.get("STRIPE_PRICE_WS_SCALE_MONTHLY")
    
    # AI Studio Plans (no founder, no annual)
    elif plan_type == PlanType.AI_BASIC:
        return os.environ.get("STRIPE_PRICE_AI_BASIC_MONTHLY")
    elif plan_type == PlanType.AI_PRO:
        return os.environ.get("STRIPE_PRICE_AI_PRO_MONTHLY")
    elif plan_type == PlanType.AI_MAX:
        return os.environ.get("STRIPE_PRICE_AI_MAX_MONTHLY")
    
    return None


# ============== PROCESSING FEE CALCULATION ==============

def get_processing_fee_percent(
    plan_type: PlanType,
    transaction_type: str,  # "invoice" or "webstore"
    is_founder: bool = False,
    billing_interval: str = "monthly"
) -> float:
    """
    Get the platform processing fee percentage.
    
    Invoice fees (online invoice payments):
    - OS Starter: 0% (no online payments)
    - OS Pro: 1%
    - OS Business: 1% (0.5% for founder annual)
    - Webstore plans: N/A (no invoices)
    - AI Studio: N/A (no invoices)
    
    Webstore fees:
    - OS Starter: 0% (no webstores)
    - OS Pro: 3%
    - OS Business: 2% (1.5% for founder annual)
    - WS Launch: 3%
    - WS Growth: 2.5%
    - WS Scale: 2%
    - AI Studio: N/A (no webstores)
    """
    
    if transaction_type == "invoice":
        # Only OS Pro and Business have online invoice payments
        if plan_type == PlanType.OS_PRO:
            return 1.0
        elif plan_type == PlanType.OS_BUSINESS:
            if is_founder and billing_interval == "annual":
                return 0.5
            return 1.0
        return 0.0  # No invoice fees for other plans
    
    elif transaction_type == "webstore":
        # OS Plans
        if plan_type == PlanType.OS_STARTER:
            return 0.0  # No webstores on Starter
        elif plan_type == PlanType.OS_PRO:
            return 3.0
        elif plan_type == PlanType.OS_BUSINESS:
            if is_founder and billing_interval == "annual":
                return 1.5
            return 2.0
        
        # Webstore Plans
        elif plan_type == PlanType.WS_LAUNCH:
            return 3.0
        elif plan_type == PlanType.WS_GROWTH:
            return 2.5
        elif plan_type == PlanType.WS_SCALE:
            return 2.0
        
        return 0.0  # AI Studio has no webstores
    
    return 0.0


def calculate_platform_fee(
    amount: float,
    plan_type: PlanType,
    transaction_type: str,
    is_founder: bool = False,
    billing_interval: str = "monthly"
) -> Tuple[float, float]:
    """
    Calculate platform fee for a transaction.
    Returns (fee_amount, fee_percent)
    """
    fee_percent = get_processing_fee_percent(
        plan_type, transaction_type, is_founder, billing_interval
    )
    fee_amount = round(amount * (fee_percent / 100), 2)
    return fee_amount, fee_percent


# ============== FOUNDER ELIGIBILITY ==============

async def check_founder_eligibility(db, tenant_id: str, plan_type: PlanType) -> Tuple[bool, str]:
    """
    Check if a tenant can use founder pricing.
    
    Rules:
    - Must be an OS plan
    - Either already a founder OR spots remaining
    - tenant.is_founder must be true OR will be set on checkout
    
    Returns (eligible, reason)
    """
    config = get_plan_config(plan_type)
    
    # Only OS plans have founder pricing
    if config.product_line != ProductLine.OS:
        return False, "Founder pricing only available for OS plans"
    
    # Check if already a founder
    tenant = await db.tenants.find_one(
        {"id": tenant_id},
        {"_id": 0, "is_founder": 1, "founder_number": 1}
    )
    
    if tenant and tenant.get("is_founder"):
        return True, f"Founder #{tenant.get('founder_number', 'N/A')}"
    
    # Check if spots remaining
    founder_count = await db.tenants.count_documents({"is_founder": True})
    if founder_count >= FOUNDER_SPOTS_TOTAL:
        return False, "No founder spots remaining"
    
    return True, f"Founder spot available ({FOUNDER_SPOTS_TOTAL - founder_count} remaining)"


async def assign_founder_status(db, tenant_id: str) -> Optional[int]:
    """
    Assign founder status to a tenant.
    Returns founder number if successful, None if no spots left.
    """
    # Double-check spots available
    founder_count = await db.tenants.count_documents({"is_founder": True})
    if founder_count >= FOUNDER_SPOTS_TOTAL:
        return None
    
    founder_number = founder_count + 1
    
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {
            "is_founder": True,
            "founder_number": founder_number,
            "founder_locked_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return founder_number


# ============== CHECKOUT SESSION CREATION ==============

async def create_multi_product_checkout(
    db,
    tenant_id: str,
    user_id: str,
    email: str,
    plan_type: PlanType,
    billing_interval: str = "monthly",
    use_founder_pricing: bool = False,
    origin_url: str = ""
) -> Dict[str, Any]:
    """
    Create a Stripe Checkout session for any plan across all product lines.
    """
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe.api_key = api_key
    config = get_plan_config(plan_type)
    
    # Validate annual billing (only OS Business)
    if billing_interval == "annual" and plan_type != PlanType.OS_BUSINESS:
        raise HTTPException(
            status_code=400, 
            detail="Annual billing only available for OS Business plan"
        )
    
    # Validate founder pricing eligibility
    is_founder = False
    if use_founder_pricing:
        eligible, reason = await check_founder_eligibility(db, tenant_id, plan_type)
        if not eligible:
            raise HTTPException(status_code=400, detail=reason)
        is_founder = True
    
    # Get Stripe Price ID
    price_id = get_stripe_price_id(plan_type, billing_interval, is_founder)
    if not price_id:
        raise HTTPException(
            status_code=500, 
            detail=f"Price ID not configured for {plan_type.value}"
        )
    
    # Build URLs
    origin = origin_url.rstrip('/')
    success_url = f"{origin}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/billing/cancel"
    
    # Metadata for webhook processing
    metadata = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "email": email,
        "plan_type": plan_type.value,
        "product_line": config.product_line.value,
        "billing_interval": billing_interval,
        "is_founder": str(is_founder).lower(),
        "price_id": price_id,
    }
    
    # Create subscription checkout session
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            customer_email=email,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            subscription_data={
                "metadata": metadata,
            },
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    
    # Record transaction
    transaction = {
        "id": str(__import__("uuid").uuid4()),
        "tenant_id": tenant_id,
        "user_id": user_id,
        "email": email,
        "stripe_session_id": session.id,
        "plan_type": plan_type.value,
        "product_line": config.product_line.value,
        "billing_interval": billing_interval,
        "is_founder": is_founder,
        "amount": config.pricing.founder_monthly if is_founder else config.pricing.monthly,
        "currency": "usd",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {
        "url": session.url,
        "session_id": session.id,
        "plan_type": plan_type.value,
        "product_line": config.product_line.value,
        "is_founder": is_founder,
    }


# ============== WEBHOOK HANDLERS ==============

async def handle_checkout_completed(db, event_data: Any) -> None:
    """
    Handle checkout.session.completed webhook.
    Creates/updates subscription and tenant records.
    """
    session_id = event_data.id
    metadata = event_data.metadata or {}
    payment_status = event_data.payment_status
    
    tenant_id = metadata.get("tenant_id")
    if not tenant_id:
        return
    
    # Update transaction
    await db.payment_transactions.update_one(
        {"stripe_session_id": session_id},
        {"$set": {
            "payment_status": "paid" if payment_status == "paid" else "pending",
            "paid_at": datetime.now(timezone.utc).isoformat() if payment_status == "paid" else None,
            "stripe_customer_id": event_data.customer,
            "stripe_subscription_id": event_data.subscription,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    
    if payment_status == "paid":
        # Fetch subscription details from Stripe
        current_period_end = None
        if event_data.subscription:
            try:
                stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
                stripe_sub = stripe.Subscription.retrieve(event_data.subscription)
                current_period_end = datetime.fromtimestamp(
                    stripe_sub.current_period_end, tz=timezone.utc
                ).isoformat()
            except:
                pass
        
        # Activate subscription
        await activate_multi_product_subscription(
            db,
            tenant_id=tenant_id,
            metadata=metadata,
            stripe_customer_id=event_data.customer,
            stripe_subscription_id=event_data.subscription,
            current_period_end=current_period_end,
        )


async def handle_subscription_created(db, event_data: Any) -> None:
    """Handle customer.subscription.created webhook"""
    subscription_id = event_data.id
    status = event_data.status
    current_period_end = datetime.fromtimestamp(
        event_data.current_period_end, tz=timezone.utc
    ).isoformat()
    
    await db.subscriptions.update_one(
        {"stripe_subscription_id": subscription_id},
        {"$set": {
            "stripe_customer_id": event_data.customer,
            "status": map_stripe_status(status),
            "current_period_end": current_period_end,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )


async def handle_subscription_updated(db, event_data: Any) -> None:
    """Handle customer.subscription.updated webhook"""
    subscription_id = event_data.id
    status = event_data.status
    current_period_end = datetime.fromtimestamp(
        event_data.current_period_end, tz=timezone.utc
    ).isoformat()
    
    # Get metadata for plan info
    metadata = event_data.metadata or {}
    
    update_data = {
        "status": map_stripe_status(status),
        "current_period_end": current_period_end,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # If plan changed via Stripe dashboard, update plan info
    if metadata.get("plan_type"):
        update_data["plan"] = metadata.get("plan_type")
        update_data["product_line"] = metadata.get("product_line")
    
    await db.subscriptions.update_one(
        {"stripe_subscription_id": subscription_id},
        {"$set": update_data}
    )
    
    # Update tenant status
    sub = await db.subscriptions.find_one(
        {"stripe_subscription_id": subscription_id},
        {"_id": 0, "tenant_id": 1}
    )
    if sub:
        await db.tenants.update_one(
            {"id": sub["tenant_id"]},
            {"$set": {
                "subscription_status": map_stripe_status(status),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }}
        )


async def handle_subscription_deleted(db, event_data: Any) -> None:
    """Handle customer.subscription.deleted webhook"""
    subscription_id = event_data.id
    
    await db.subscriptions.update_one(
        {"stripe_subscription_id": subscription_id},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    
    # Update tenant
    sub = await db.subscriptions.find_one(
        {"stripe_subscription_id": subscription_id},
        {"_id": 0, "tenant_id": 1}
    )
    if sub:
        # Downgrade to free tier (OS Starter)
        await db.tenants.update_one(
            {"id": sub["tenant_id"]},
            {"$set": {
                "plan": "os_starter",
                "product_line": "os",
                "subscription_status": "cancelled",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }}
        )


async def handle_invoice_payment_succeeded(db, event_data: Any) -> None:
    """Handle invoice.payment_succeeded webhook"""
    subscription_id = event_data.subscription
    
    if subscription_id:
        # Fetch updated subscription data
        update_data = {
            "status": "active",
            "last_payment_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        try:
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            update_data["current_period_end"] = datetime.fromtimestamp(
                stripe_sub.current_period_end, tz=timezone.utc
            ).isoformat()
            update_data["current_period_start"] = datetime.fromtimestamp(
                stripe_sub.current_period_start, tz=timezone.utc
            ).isoformat()
        except:
            pass
        
        await db.subscriptions.update_one(
            {"stripe_subscription_id": subscription_id},
            {"$set": update_data}
        )
        
        # Update tenant status
        sub = await db.subscriptions.find_one(
            {"stripe_subscription_id": subscription_id},
            {"_id": 0, "tenant_id": 1}
        )
        if sub:
            await db.tenants.update_one(
                {"id": sub["tenant_id"]},
                {"$set": {
                    "subscription_status": "active",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }}
            )
        
        # Record transaction
        await db.payment_transactions.insert_one({
            "id": str(__import__("uuid").uuid4()),
            "tenant_id": sub.get("tenant_id") if sub else None,
            "stripe_invoice_id": event_data.id,
            "stripe_subscription_id": subscription_id,
            "amount": event_data.amount_paid / 100,
            "currency": event_data.currency,
            "payment_status": "paid",
            "paid_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"event_type": "invoice.payment_succeeded"}
        })


async def handle_invoice_payment_failed(db, event_data: Any) -> None:
    """Handle invoice.payment_failed webhook"""
    subscription_id = event_data.subscription
    
    if subscription_id:
        await db.subscriptions.update_one(
            {"stripe_subscription_id": subscription_id},
            {"$set": {
                "status": "past_due",
                "payment_failed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }}
        )
        
        # Update tenant status
        sub = await db.subscriptions.find_one(
            {"stripe_subscription_id": subscription_id},
            {"_id": 0, "tenant_id": 1}
        )
        if sub:
            await db.tenants.update_one(
                {"id": sub["tenant_id"]},
                {"$set": {
                    "subscription_status": "past_due",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }}
            )


# ============== SUBSCRIPTION ACTIVATION ==============

async def activate_multi_product_subscription(
    db,
    tenant_id: str,
    metadata: Dict[str, Any],
    stripe_customer_id: str = None,
    stripe_subscription_id: str = None,
    current_period_end: str = None,
) -> None:
    """
    Activate a subscription after successful checkout.
    Updates both subscription and tenant records.
    """
    plan_type_str = metadata.get("plan_type", "os_starter")
    product_line = metadata.get("product_line", "os")
    billing_interval = metadata.get("billing_interval", "monthly")
    is_founder = metadata.get("is_founder", "false") == "true"
    
    try:
        plan_type = PlanType(plan_type_str)
    except ValueError:
        plan_type = PlanType.OS_STARTER
    
    config = get_plan_config(plan_type)
    now = datetime.now(timezone.utc)
    
    # Handle founder assignment
    founder_number = None
    if is_founder and config.founder_eligible:
        # Check if already a founder
        tenant = await db.tenants.find_one(
            {"id": tenant_id},
            {"_id": 0, "is_founder": 1, "founder_number": 1}
        )
        if tenant and tenant.get("is_founder"):
            founder_number = tenant.get("founder_number")
        else:
            founder_number = await assign_founder_status(db, tenant_id)
    
    # Build subscription data
    subscription_data = {
        "tenant_id": tenant_id,
        "plan": plan_type.value,
        "product_line": product_line,
        "status": "active",
        "billing_interval": billing_interval,
        "is_founder": is_founder and founder_number is not None,
        "founder_number": founder_number,
        "stripe_customer_id": stripe_customer_id,
        "stripe_subscription_id": stripe_subscription_id,
        "current_period_start": now.isoformat(),
        "current_period_end": current_period_end,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    # Upsert subscription
    await db.subscriptions.update_one(
        {"tenant_id": tenant_id},
        {"$set": subscription_data},
        upsert=True
    )
    
    # Update tenant
    tenant_update = {
        "plan": plan_type.value,
        "product_line": product_line,
        "subscription_status": "active",
        "updated_at": now.isoformat(),
    }
    
    if is_founder and founder_number:
        tenant_update["is_founder"] = True
        tenant_update["founder_number"] = founder_number
        tenant_update["founder_locked_at"] = now.isoformat()
    
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": tenant_update}
    )
    
    # Update feature usage limits
    gate = get_multi_product_feature_gate(db)
    await gate._update_usage_limits(tenant_id, config)


# ============== HELPERS ==============

def map_stripe_status(stripe_status: str) -> str:
    """Map Stripe subscription status to internal status"""
    status_map = {
        "active": "active",
        "trialing": "trialing",
        "past_due": "past_due",
        "canceled": "cancelled",
        "unpaid": "past_due",
        "incomplete": "pending",
        "incomplete_expired": "expired",
    }
    return status_map.get(stripe_status, "active")
