"""
Billing & Subscription Routes - Updated Pricing

Pricing Structure:
- 24-Hour Free Trial (no payment)
- 14-Day Extended Trial ($19.99)
- Founder Pricing (first 100): Tier 1 $79, Tier 2 $129, Tier 3 $199, AI Add-on $49
- Standard Pricing (after 100): $129, $229, $379, $89
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import os
import jwt

from models.billing import (
    SubscriptionPlan, SubscriptionStatus, PaymentStatus, BillingInterval,
    FOUNDER_PRICING, STANDARD_PRICING, MAX_FOUNDER_ACCOUNTS,
    TIER_FEATURES, FOUNDER_BENEFITS,
    Subscription, FounderCounter, PaymentTransaction,
    CheckoutRequest, CheckoutResponse, SubscriptionResponse,
    PricingPlan, PricingResponse, TrialStatus
)
from models import UserInDB

router = APIRouter(prefix="/billing", tags=["Billing & Subscriptions"])
webhook_router = APIRouter(tags=["Webhooks"])


# ============== DEPENDENCY INJECTION ==============

async def get_db():
    from server import db
    return db


async def get_current_user_billing(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    """Get current user for billing routes"""
    from server import db, SECRET_KEY, ALGORITHM
    
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return UserInDB(**user)


# ============== HELPER FUNCTIONS ==============

async def get_founder_count(db) -> int:
    """Get current number of founder accounts"""
    counter = await db.founder_counter.find_one({"id": "founder_counter"})
    return counter["count"] if counter else 0


async def increment_founder_count(db) -> int:
    """Increment founder count and return new number"""
    result = await db.founder_counter.find_one_and_update(
        {"id": "founder_counter"},
        {
            "$inc": {"count": 1},
            "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True,
        return_document=True
    )
    return result["count"]


async def is_founder_pricing_available(db) -> bool:
    """Check if founder pricing is still available"""
    count = await get_founder_count(db)
    return count < MAX_FOUNDER_ACCOUNTS


def get_pricing_config(is_founder: bool):
    """Get the appropriate pricing configuration"""
    return FOUNDER_PRICING if is_founder else STANDARD_PRICING


# ============== PRICING PAGE (PUBLIC) ==============

@router.get("/pricing", response_model=PricingResponse)
async def get_pricing_plans(db = Depends(get_db)):
    """Get all available pricing plans for the pricing page"""
    founder_count = await get_founder_count(db)
    is_founder = founder_count < MAX_FOUNDER_ACCOUNTS
    pricing = get_pricing_config(is_founder)
    
    plans = []
    
    # Tier 1
    t1 = pricing[SubscriptionPlan.TIER_1]
    plans.append(PricingPlan(
        id=SubscriptionPlan.TIER_1.value,
        name=t1["name"],
        display_name=t1.get("display_name", "Starter Shop"),
        amount=t1["amount"],
        standard_price=t1.get("standard_price"),
        savings=t1.get("standard_price", 0) - t1["amount"] if t1.get("standard_price") else None,
        description=t1["description"],
        interval=t1.get("interval", "month"),
        tier=t1["tier"],
        features=TIER_FEATURES["starter"],
        onboarding_fee=t1.get("onboarding_fee", 0),
        is_popular=False
    ))
    
    # Tier 2
    t2 = pricing[SubscriptionPlan.TIER_2]
    plans.append(PricingPlan(
        id=SubscriptionPlan.TIER_2.value,
        name=t2["name"],
        display_name=t2.get("display_name", "Growth Shop"),
        amount=t2["amount"],
        standard_price=t2.get("standard_price"),
        savings=t2.get("standard_price", 0) - t2["amount"] if t2.get("standard_price") else None,
        description=t2["description"],
        interval=t2.get("interval", "month"),
        tier=t2["tier"],
        features=TIER_FEATURES["pro"],
        onboarding_fee=t2.get("onboarding_fee", 0),
        is_popular=True
    ))
    
    # Tier 3
    t3 = pricing[SubscriptionPlan.TIER_3]
    plans.append(PricingPlan(
        id=SubscriptionPlan.TIER_3.value,
        name=t3["name"],
        display_name=t3.get("display_name", "Pro Shop"),
        amount=t3["amount"],
        standard_price=t3.get("standard_price"),
        savings=t3.get("standard_price", 0) - t3["amount"] if t3.get("standard_price") else None,
        description=t3["description"],
        interval=t3.get("interval", "month"),
        tier=t3["tier"],
        features=TIER_FEATURES["business"],
        onboarding_fee=t3.get("onboarding_fee", 0),
        is_popular=False
    ))
    
    # AI Add-on
    ai = pricing[SubscriptionPlan.AI_ADDON]
    addon = PricingPlan(
        id=SubscriptionPlan.AI_ADDON.value,
        name=ai["name"],
        display_name=ai.get("display_name", "AI Tools Pack"),
        amount=ai["amount"],
        standard_price=ai.get("standard_price"),
        savings=ai.get("standard_price", 0) - ai["amount"] if ai.get("standard_price") else None,
        description=ai["description"],
        interval=ai.get("interval", "month"),
        tier=ai["tier"],
        features=TIER_FEATURES["ai_addon"],
        is_addon=True
    )
    
    # Extended Trial
    trial_info = pricing[SubscriptionPlan.EXTENDED_TRIAL]
    trial = PricingPlan(
        id=SubscriptionPlan.EXTENDED_TRIAL.value,
        name=trial_info["name"],
        display_name="Extended Trial",
        amount=trial_info["amount"],
        description=trial_info["description"],
        tier=trial_info["tier"],
        features=[
            "Full platform access",
            "All features unlocked",
            "Live support access",
            "Onboarding assistance",
            "$19.99 credits to Tier 3 subscription"
        ]
    )
    
    return PricingResponse(
        is_founder_pricing=is_founder,
        founders_remaining=max(0, MAX_FOUNDER_ACCOUNTS - founder_count),
        founders_claimed=founder_count,
        plans=plans,
        addon=addon,
        trial=trial,
        founder_benefits=FOUNDER_BENEFITS if is_founder else []
    )


# ============== TRIAL STATUS ==============

@router.get("/trial-status")
async def get_trial_status(
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """Get current trial status for the user"""
    
    # First check if user/tenant is a founder - founders are never locked
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if tenant:
        # Founders and active subscriptions are never locked
        if tenant.get("is_founder") or tenant.get("subscription_status") == "active":
            return TrialStatus(
                is_trial=False,
                is_locked=False,
                can_upgrade=False
            )
    
    # Get subscription
    subscription = await db.subscriptions.find_one(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not subscription:
        # Check tenant creation time for 24hr free trial
        if tenant and tenant.get("created_at"):
            created_at = datetime.fromisoformat(tenant["created_at"].replace("Z", "+00:00"))
            trial_end = created_at + timedelta(hours=24)
            now = datetime.now(timezone.utc)
            
            if now < trial_end:
                hours_remaining = (trial_end - now).total_seconds() / 3600
                return TrialStatus(
                    is_trial=True,
                    trial_type="free_trial",
                    hours_remaining=round(hours_remaining, 1),
                    is_locked=False,
                    can_upgrade=True
                )
            else:
                # 24hr trial expired - account locked
                return TrialStatus(
                    is_trial=False,
                    is_locked=True,
                    can_upgrade=True
                )
        
        return TrialStatus(is_trial=False, is_locked=True, can_upgrade=True)
    
    sub = Subscription(**subscription)
    
    if sub.status == SubscriptionStatus.LOCKED:
        return TrialStatus(is_trial=False, is_locked=True, can_upgrade=True)
    
    if sub.status == SubscriptionStatus.TRIALING and sub.trial_end:
        trial_end = datetime.fromisoformat(sub.trial_end.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        
        if now < trial_end:
            remaining = trial_end - now
            return TrialStatus(
                is_trial=True,
                trial_type="extended_trial" if sub.extended_trial_paid else "free_trial",
                days_remaining=round(remaining.days + remaining.seconds / 86400, 1),
                is_locked=False,
                can_upgrade=True,
                extended_trial_paid=sub.extended_trial_paid
            )
    
    return TrialStatus(
        is_trial=False,
        is_locked=sub.status == SubscriptionStatus.LOCKED,
        can_upgrade=sub.status not in [SubscriptionStatus.ACTIVE]
    )


# ============== CHECKOUT SESSIONS ==============

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    http_request: Request,
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """Create a Stripe checkout session for subscription"""
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionRequest
    )
    
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    # Check if founder pricing is available
    is_founder = await is_founder_pricing_available(db)
    pricing = get_pricing_config(is_founder)
    
    # Validate plan
    if request.plan not in pricing:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan_info = pricing[request.plan]
    amount = float(plan_info["amount"])
    
    # Add AI addon if requested
    if request.include_ai_addon and request.plan != SubscriptionPlan.AI_ADDON:
        ai_info = pricing[SubscriptionPlan.AI_ADDON]
        amount += float(ai_info["amount"])
    
    # Build URLs
    origin = request.origin_url.rstrip('/')
    success_url = f"{origin}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/billing/cancel"
    
    # Create checkout session
    webhook_url = f"{str(http_request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "email": current_user.email,
            "plan": request.plan.value,
            "tier": plan_info["tier"],
            "is_founder": str(is_founder).lower(),
            "include_ai_addon": str(request.include_ai_addon).lower()
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction = PaymentTransaction(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        email=current_user.email,
        stripe_session_id=session.session_id,
        amount=amount,
        currency="usd",
        plan=request.plan,
        payment_status=PaymentStatus.INITIATED,
        is_founder_purchase=is_founder,
        metadata={
            "plan_name": plan_info["name"],
            "tier": plan_info["tier"],
            "include_ai_addon": request.include_ai_addon
        }
    )
    
    await db.payment_transactions.insert_one(transaction.model_dump())
    
    return CheckoutResponse(url=session.url, session_id=session.session_id)


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """Get status of a checkout session"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction if paid
    if status.payment_status == "paid":
        existing = await db.payment_transactions.find_one({
            "stripe_session_id": session_id,
            "payment_status": PaymentStatus.PAID.value
        })
        
        if not existing:
            await db.payment_transactions.update_one(
                {"stripe_session_id": session_id},
                {
                    "$set": {
                        "payment_status": PaymentStatus.PAID.value,
                        "paid_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            await _activate_subscription(db, session_id, status.metadata)
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount": status.amount_total / 100,
        "currency": status.currency
    }


async def _activate_subscription(db, session_id: str, metadata: dict):
    """Activate subscription after successful payment"""
    tenant_id = metadata.get("tenant_id")
    plan_str = metadata.get("plan")
    tier = metadata.get("tier", "starter")
    is_founder = metadata.get("is_founder", "false") == "true"
    include_ai_addon = metadata.get("include_ai_addon", "false") == "true"
    
    if not tenant_id or not plan_str:
        return
    
    try:
        plan = SubscriptionPlan(plan_str)
    except ValueError:
        return
    
    now = datetime.now(timezone.utc)
    founder_number = None
    
    # Assign founder number if applicable
    if is_founder and plan != SubscriptionPlan.EXTENDED_TRIAL:
        founder_number = await increment_founder_count(db)
    
    # Get transaction for amount
    transaction = await db.payment_transactions.find_one({"stripe_session_id": session_id})
    amount_paid = transaction.get("amount", 0) if transaction else 0
    
    if plan == SubscriptionPlan.EXTENDED_TRIAL:
        # 14-day extended trial
        trial_end = now + timedelta(days=14)
        subscription_data = {
            "tenant_id": tenant_id,
            "plan": plan.value,
            "status": SubscriptionStatus.TRIALING.value,
            "tier": "business",  # Full access during trial
            "is_founder": is_founder,
            "has_ai_addon": True,  # Full access during trial
            "trial_start": now.isoformat(),
            "trial_end": trial_end.isoformat(),
            "trial_credits_applied": amount_paid,  # $19.99 credits toward Tier 3
            "extended_trial_paid": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
    else:
        # Regular subscription
        period_end = now + timedelta(days=30)
        
        # Check if user has trial credits to apply to Tier 3
        existing_sub = await db.subscriptions.find_one({"tenant_id": tenant_id})
        trial_credits = 0
        if existing_sub and plan == SubscriptionPlan.TIER_3:
            trial_credits = existing_sub.get("trial_credits_applied", 0)
        
        subscription_data = {
            "tenant_id": tenant_id,
            "plan": plan.value,
            "status": SubscriptionStatus.ACTIVE.value,
            "tier": tier,
            "is_founder": is_founder,
            "founder_number": founder_number,
            "founder_locked_at": now.isoformat() if is_founder else None,
            "has_ai_addon": include_ai_addon or plan == SubscriptionPlan.AI_ADDON,
            "current_period_start": now.isoformat(),
            "current_period_end": period_end.isoformat(),
            "trial_credits_applied": trial_credits,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
    
    # Upsert subscription
    await db.subscriptions.update_one(
        {"tenant_id": tenant_id},
        {"$set": subscription_data},
        upsert=True
    )
    
    # Update tenant tier
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {"plan": tier}}
    )


# ============== SUBSCRIPTION MANAGEMENT ==============

@router.get("/subscription")
async def get_subscription(
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """Get current subscription details"""
    subscription = await db.subscriptions.find_one(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not subscription:
        # Return default trial info
        tenant = await db.tenants.find_one(
            {"id": current_user.tenant_id},
            {"_id": 0, "created_at": 1}
        )
        
        trial_end = None
        status = "locked"
        
        if tenant and tenant.get("created_at"):
            created_at = datetime.fromisoformat(tenant["created_at"].replace("Z", "+00:00"))
            trial_end_dt = created_at + timedelta(hours=24)
            now = datetime.now(timezone.utc)
            
            if now < trial_end_dt:
                trial_end = trial_end_dt.isoformat()
                status = "trialing"
        
        return SubscriptionResponse(
            plan="free_trial",
            plan_name="24-Hour Free Trial",
            status=status,
            tier="business",  # Full access during trial
            is_founder=await is_founder_pricing_available(db),
            trial_end=trial_end,
            features=TIER_FEATURES["business"]
        )
    
    sub = Subscription(**subscription)
    tier_features = TIER_FEATURES.get(sub.tier, [])
    
    # Get plan name
    is_founder = sub.is_founder
    pricing = get_pricing_config(is_founder)
    plan_info = pricing.get(sub.plan, {})
    plan_name = plan_info.get("name", sub.plan)
    
    return SubscriptionResponse(
        plan=sub.plan.value if isinstance(sub.plan, SubscriptionPlan) else sub.plan,
        plan_name=plan_name,
        status=sub.status.value if isinstance(sub.status, SubscriptionStatus) else sub.status,
        tier=sub.tier,
        is_founder=sub.is_founder,
        founder_number=sub.founder_number,
        has_ai_addon=sub.has_ai_addon,
        trial_end=sub.trial_end,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        trial_credits=sub.trial_credits_applied,
        features=tier_features
    )


@router.get("/founder-status")
async def get_founder_status(db = Depends(get_db)):
    """Get current founder account availability (public)"""
    count = await get_founder_count(db)
    return {
        "founders_claimed": count,
        "founders_remaining": max(0, MAX_FOUNDER_ACCOUNTS - count),
        "is_founder_pricing_available": count < MAX_FOUNDER_ACCOUNTS,
        "max_founders": MAX_FOUNDER_ACCOUNTS
    }


@router.get("/payment-history")
async def get_payment_history(
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """Get payment history for the tenant"""
    transactions = await db.payment_transactions.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {
        "transactions": [
            {
                "id": t["id"],
                "amount": t["amount"],
                "currency": t["currency"],
                "plan": t["plan"],
                "status": t["payment_status"],
                "is_founder": t.get("is_founder_purchase", False),
                "created_at": t["created_at"],
                "paid_at": t.get("paid_at")
            }
            for t in transactions
        ]
    }


# ============== WEBHOOK HANDLER ==============

@webhook_router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db = Depends(get_db)):
    """Handle Stripe webhook events"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    
    try:
        event = await stripe_checkout.handle_webhook(body, signature)
        
        if event.event_type == "checkout.session.completed":
            if event.payment_status == "paid":
                await db.payment_transactions.update_one(
                    {"stripe_session_id": event.session_id},
                    {
                        "$set": {
                            "payment_status": PaymentStatus.PAID.value,
                            "paid_at": datetime.now(timezone.utc).isoformat(),
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                await _activate_subscription(db, event.session_id, event.metadata)
        
        elif event.event_type == "payment_intent.payment_failed":
            await db.payment_transactions.update_one(
                {"stripe_session_id": event.session_id},
                {
                    "$set": {
                        "payment_status": PaymentStatus.FAILED.value,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        return {"status": "success", "event_type": event.event_type}
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}
