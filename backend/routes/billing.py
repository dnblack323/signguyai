"""
Billing & Subscription Routes

Handles:
- Checkout sessions for trials and subscriptions
- Subscription management
- Stripe webhooks
- Pricing page data
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import os

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CheckoutStatusResponse
)

from models.billing import (
    SubscriptionPlan, SubscriptionStatus, PaymentStatus,
    FOUNDER_PRICING, TIER_FEATURES,
    Subscription, PaymentTransaction,
    CheckoutRequest, CheckoutResponse, SubscriptionResponse,
    PricingPlan, TrialStatus
)
from models import UserInDB

router = APIRouter(prefix="/billing", tags=["Billing & Subscriptions"])
webhook_router = APIRouter(tags=["Webhooks"])


# ============== DEPENDENCY INJECTION ==============

async def get_db():
    from server import db
    return db


async def get_stripe():
    """Get Stripe API key"""
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    return api_key


# Import the user dependency directly
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

async def get_current_user_billing(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    """Get current user for billing routes"""
    from server import db, SECRET_KEY, ALGORITHM
    import jwt
    
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


# ============== PRICING PAGE (PUBLIC) ==============

@router.get("/pricing")
async def get_pricing_plans():
    """Get all available pricing plans for the pricing page (public)"""
    plans = []
    
    # Paid Trial
    trial = FOUNDER_PRICING[SubscriptionPlan.PAID_TRIAL]
    plans.append(PricingPlan(
        id=SubscriptionPlan.PAID_TRIAL.value,
        name=trial["name"],
        amount=trial["amount"],
        regular_price=trial["regular_price"],
        description=trial["description"],
        tier=trial["tier"],
        features=TIER_FEATURES["pro"][:5],  # First 5 features
        is_popular=False
    ))
    
    # Pro Monthly
    pro_m = FOUNDER_PRICING[SubscriptionPlan.PRO_MONTHLY]
    plans.append(PricingPlan(
        id=SubscriptionPlan.PRO_MONTHLY.value,
        name=pro_m["name"],
        amount=pro_m["amount"],
        regular_price=pro_m["regular_price"],
        description=pro_m["description"],
        interval="month",
        tier=pro_m["tier"],
        features=TIER_FEATURES["pro"],
        is_popular=True
    ))
    
    # Pro Yearly
    pro_y = FOUNDER_PRICING[SubscriptionPlan.PRO_YEARLY]
    plans.append(PricingPlan(
        id=SubscriptionPlan.PRO_YEARLY.value,
        name=pro_y["name"],
        amount=pro_y["amount"],
        regular_price=pro_y["regular_price"],
        savings=pro_y["savings"],
        description=pro_y["description"],
        interval="year",
        tier=pro_y["tier"],
        features=TIER_FEATURES["pro"],
        monthly_equivalent=pro_y["monthly_equivalent"],
        is_popular=False
    ))
    
    # Business Monthly
    biz_m = FOUNDER_PRICING[SubscriptionPlan.BUSINESS_MONTHLY]
    plans.append(PricingPlan(
        id=SubscriptionPlan.BUSINESS_MONTHLY.value,
        name=biz_m["name"],
        amount=biz_m["amount"],
        regular_price=biz_m["regular_price"],
        description=biz_m["description"],
        interval="month",
        tier=biz_m["tier"],
        features=TIER_FEATURES["business"],
        is_popular=False
    ))
    
    # Business Yearly
    biz_y = FOUNDER_PRICING[SubscriptionPlan.BUSINESS_YEARLY]
    plans.append(PricingPlan(
        id=SubscriptionPlan.BUSINESS_YEARLY.value,
        name=biz_y["name"],
        amount=biz_y["amount"],
        regular_price=biz_y["regular_price"],
        savings=biz_y["savings"],
        description=biz_y["description"],
        interval="year",
        tier=biz_y["tier"],
        features=TIER_FEATURES["business"],
        monthly_equivalent=biz_y["monthly_equivalent"],
        is_popular=False
    ))
    
    return {
        "plans": [p.model_dump() for p in plans],
        "founder_pricing": True,
        "founder_message": "🎉 Founder Member Pricing - Lock in these rates forever!"
    }


# ============== TRIAL STATUS ==============

@router.get("/trial-status")
async def get_trial_status(
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """Get current trial status for the user"""
    # Get subscription
    subscription = await db.subscriptions.find_one(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not subscription:
        # Check tenant creation time for 24hr free trial
        tenant = await db.tenants.find_one(
            {"id": current_user.tenant_id},
            {"_id": 0, "created_at": 1}
        )
        
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
                trial_type=sub.plan.value,
                days_remaining=round(remaining.days + remaining.seconds / 86400, 1),
                is_locked=False,
                can_upgrade=True
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
    api_key = await get_stripe()
    
    # Validate plan
    if request.plan not in FOUNDER_PRICING:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan_info = FOUNDER_PRICING[request.plan]
    amount = float(plan_info["amount"])
    
    # Build URLs
    origin = request.origin_url.rstrip('/')
    success_url = f"{origin}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/billing/cancel"
    
    # Initialize Stripe
    webhook_url = f"{str(http_request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    # Create checkout session
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
            "is_founder": "true"
        }
    )
    
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
    
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
        metadata={
            "plan_name": plan_info["name"],
            "tier": plan_info["tier"]
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
    api_key = await get_stripe()
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    
    status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction if paid
    if status.payment_status == "paid":
        # Check if already processed
        existing = await db.payment_transactions.find_one({
            "stripe_session_id": session_id,
            "payment_status": PaymentStatus.PAID.value
        })
        
        if not existing:
            # Update transaction
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
            
            # Process subscription activation
            await _activate_subscription(db, session_id, status.metadata)
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount": status.amount_total / 100,  # Convert cents to dollars
        "currency": status.currency
    }


async def _activate_subscription(db, session_id: str, metadata: dict):
    """Activate subscription after successful payment"""
    tenant_id = metadata.get("tenant_id")
    plan_str = metadata.get("plan")
    tier = metadata.get("tier", "pro")
    
    if not tenant_id or not plan_str:
        return
    
    try:
        plan = SubscriptionPlan(plan_str)
    except ValueError:
        return
    
    plan_info = FOUNDER_PRICING.get(plan, {})
    
    # Calculate trial/subscription period
    now = datetime.now(timezone.utc)
    
    if plan == SubscriptionPlan.PAID_TRIAL:
        # 14-day trial
        trial_end = now + timedelta(days=14)
        subscription_data = {
            "tenant_id": tenant_id,
            "plan": plan.value,
            "status": SubscriptionStatus.TRIALING.value,
            "tier": tier,
            "is_founder": True,
            "founder_locked_at": now.isoformat(),
            "trial_start": now.isoformat(),
            "trial_end": trial_end.isoformat(),
            "trial_credits_applied": plan_info.get("amount", 0),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
    else:
        # Regular subscription
        if "yearly" in plan.value:
            period_end = now + timedelta(days=365)
        else:
            period_end = now + timedelta(days=30)
        
        subscription_data = {
            "tenant_id": tenant_id,
            "plan": plan.value,
            "status": SubscriptionStatus.ACTIVE.value,
            "tier": tier,
            "is_founder": True,
            "founder_locked_at": now.isoformat(),
            "current_period_start": now.isoformat(),
            "current_period_end": period_end.isoformat(),
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
            status=status,
            tier="pro",  # Full access during 24hr trial
            is_founder=True,
            trial_end=trial_end,
            features=TIER_FEATURES["pro"]
        )
    
    sub = Subscription(**subscription)
    tier_features = TIER_FEATURES.get(sub.tier, [])
    
    return SubscriptionResponse(
        plan=sub.plan.value if isinstance(sub.plan, SubscriptionPlan) else sub.plan,
        status=sub.status.value if isinstance(sub.status, SubscriptionStatus) else sub.status,
        tier=sub.tier,
        is_founder=sub.is_founder,
        trial_end=sub.trial_end,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        trial_credits=sub.trial_credits_applied,
        features=tier_features
    )


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
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    
    try:
        event = await stripe_checkout.handle_webhook(body, signature)
        
        # Handle checkout.session.completed
        if event.event_type == "checkout.session.completed":
            if event.payment_status == "paid":
                # Update transaction
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
                
                # Activate subscription
                await _activate_subscription(db, event.session_id, event.metadata)
        
        # Handle payment_intent.payment_failed
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
