"""
Billing & Subscription Routes - Updated Pricing

Pricing Structure:
- 24-Hour Free Trial (no payment)
- 14-Day Extended Trial ($19.99, credits to Business subscription)
- Founder Pricing (first 100): Starter $79, Pro $129, Business $199, AI Add-on $49
- Standard Pricing (after 100): Starter $129, Pro $229, Business $379, AI $89

Tier Keys (canonical):
- starter
- pro
- business
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import os
import jwt
import uuid

from models.billing import (
    SubscriptionPlan, SubscriptionStatus, PaymentStatus, BillingInterval,
    FOUNDER_PRICING, STANDARD_PRICING, MAX_FOUNDER_ACCOUNTS,
    TIER_FEATURES, FOUNDER_BENEFITS,
    Subscription, FounderCounter, PaymentTransaction,
    CheckoutRequest, CheckoutResponse, SubscriptionResponse,
    PricingPlan, PricingResponse, TrialStatus
)
from models import UserInDB
from pydantic import BaseModel as PydanticBaseModel

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
    
    # Starter
    t1 = pricing[SubscriptionPlan.TIER_1]
    plans.append(PricingPlan(
        id=SubscriptionPlan.TIER_1.value,
        name=t1["name"],
        display_name=t1.get("display_name", "Starter Shop"),
        amount=t1["amount"],
        amount_annual=t1.get("amount_annual"),
        annual_savings=t1.get("annual_savings"),
        standard_price=t1.get("standard_price"),
        standard_price_annual=t1.get("standard_price_annual"),
        savings=t1.get("standard_price", 0) - t1["amount"] if t1.get("standard_price") else None,
        description=t1["description"],
        interval=t1.get("interval", "month"),
        tier=t1["tier"],
        features=TIER_FEATURES["starter"],
        onboarding_fee=t1.get("onboarding_fee", 0),
        is_popular=False
    ))
    
    # Pro
    t2 = pricing[SubscriptionPlan.TIER_2]
    plans.append(PricingPlan(
        id=SubscriptionPlan.TIER_2.value,
        name=t2["name"],
        display_name=t2.get("display_name", "Growth Shop"),
        amount=t2["amount"],
        amount_annual=t2.get("amount_annual"),
        annual_savings=t2.get("annual_savings"),
        standard_price=t2.get("standard_price"),
        standard_price_annual=t2.get("standard_price_annual"),
        savings=t2.get("standard_price", 0) - t2["amount"] if t2.get("standard_price") else None,
        description=t2["description"],
        interval=t2.get("interval", "month"),
        tier=t2["tier"],
        features=TIER_FEATURES["pro"],
        onboarding_fee=t2.get("onboarding_fee", 0),
        is_popular=True
    ))
    
    # Business
    t3 = pricing[SubscriptionPlan.TIER_3]
    plans.append(PricingPlan(
        id=SubscriptionPlan.TIER_3.value,
        name=t3["name"],
        display_name=t3.get("display_name", "Pro Shop"),
        amount=t3["amount"],
        amount_annual=t3.get("amount_annual"),
        annual_savings=t3.get("annual_savings"),
        standard_price=t3.get("standard_price"),
        standard_price_annual=t3.get("standard_price_annual"),
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
        amount_annual=ai.get("amount_annual"),
        annual_savings=ai.get("annual_savings"),
        standard_price=ai.get("standard_price"),
        standard_price_annual=ai.get("standard_price_annual"),
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
            "$19.99 credits to Business subscription"
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
    """Get current trial status for the user (48-hour free trial or subscription)"""
    from services.founders_config import FREE_TRIAL_HOURS
    
    # First check if user/tenant is a founder or has active subscription
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if tenant:
        # Founders Edition active subscribers are never locked
        if tenant.get("plan") == "founders_edition" and tenant.get("founder_lifetime_lock"):
            return TrialStatus(
                is_trial=False,
                is_locked=False,
                can_upgrade=False
            )
        
        # Check for 48-hour free trial
        if tenant.get("is_trial") or tenant.get("plan") == "free_trial":
            trial_ends_at = tenant.get("trial_ends_at")
            if trial_ends_at:
                trial_end = datetime.fromisoformat(trial_ends_at.replace("Z", "+00:00"))
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
                    # 48hr trial expired - account locked
                    return TrialStatus(
                        is_trial=False,
                        is_locked=True,
                        can_upgrade=True,
                        trial_expired=True
                    )
        
        # Legacy: Check tenant creation time for older accounts
        if tenant.get("created_at") and not tenant.get("trial_ends_at"):
            created_at = datetime.fromisoformat(tenant["created_at"].replace("Z", "+00:00"))
            trial_end = created_at + timedelta(hours=FREE_TRIAL_HOURS)
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
                # Trial expired - account locked
                return TrialStatus(
                    is_trial=False,
                    is_locked=True,
                    can_upgrade=True,
                    trial_expired=True
                )
    
    # Get subscription for users with subscription records
    subscription = await db.subscriptions.find_one(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not subscription:
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
    """
    Create a Stripe checkout session for subscription.
    
    For regular plans (tier_1, tier_2, tier_3, ai_addon):
        - Creates a Stripe SUBSCRIPTION checkout (mode=subscription)
        - Uses pre-created Stripe Price IDs from environment variables
        - Stripe manages billing cycles and renewal
        
    For extended_trial:
        - Creates a ONE-TIME PAYMENT checkout (mode=payment)
        - Grants 14-day full access
        - $19.99 credits toward future Business subscription
    """
    import stripe
    from models.billing import get_stripe_price_id
    
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe.api_key = api_key
    
    # Check if founder pricing is available
    is_founder = await is_founder_pricing_available(db)
    pricing = get_pricing_config(is_founder)
    
    # Validate plan
    if request.plan not in pricing:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan_info = pricing[request.plan]
    is_annual = request.billing_interval == "annual"
    billing_interval = "annual" if is_annual else "monthly"
    
    # Build URLs
    origin = request.origin_url.rstrip('/')
    success_url = f"{origin}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/billing/cancel"
    
    # Metadata for webhook processing
    metadata = {
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        "email": current_user.email,
        "plan": request.plan.value,
        "tier": plan_info["tier"],
        "is_founder": str(is_founder).lower(),
        "include_ai_addon": str(request.include_ai_addon).lower(),
        "billing_interval": billing_interval,
    }
    
    # ==================== EXTENDED TRIAL: ONE-TIME PAYMENT ====================
    if request.plan == SubscriptionPlan.EXTENDED_TRIAL:
        # Extended trial is a ONE-TIME payment, NOT a subscription
        amount = int(plan_info["amount"] * 100)  # Convert to cents
        
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount,
                        "product_data": {
                            "name": "14-Day Extended Trial",
                            "description": "Full platform access for 14 days. Credits toward Business subscription!",
                        },
                    },
                    "quantity": 1,
                }],
                customer_email=current_user.email,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        
        # Record transaction
        transaction = PaymentTransaction(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            email=current_user.email,
            stripe_session_id=session.id,
            amount=plan_info["amount"],
            currency="usd",
            plan=request.plan,
            payment_status=PaymentStatus.INITIATED,
            is_founder_purchase=is_founder,
            metadata={
                "plan_name": plan_info["name"],
                "tier": plan_info["tier"],
                "checkout_mode": "payment",  # One-time
            }
        )
        await db.payment_transactions.insert_one(transaction.model_dump())
        
        return CheckoutResponse(url=session.url, session_id=session.id)
    
    # ==================== REGULAR PLANS: SUBSCRIPTION ====================
    # Build line items using Stripe Price IDs
    line_items = []
    
    # Get the main plan price ID
    main_price_id = get_stripe_price_id(request.plan.value, billing_interval)
    
    if main_price_id:
        # Use pre-created Stripe Price
        line_items.append({
            "price": main_price_id,
            "quantity": 1,
        })
    else:
        # Fallback: Create price_data dynamically (for development/testing)
        if is_annual and plan_info.get("amount_annual"):
            amount = int(plan_info["amount_annual"] * 100)
            interval = "year"
        else:
            amount = int(plan_info["amount"] * 100)
            interval = "month"
        
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": amount,
                "recurring": {"interval": interval},
                "product_data": {
                    "name": plan_info["name"],
                    "description": plan_info.get("description", ""),
                },
            },
            "quantity": 1,
        })
    
    # Add AI addon if requested
    if request.include_ai_addon and request.plan != SubscriptionPlan.AI_ADDON:
        ai_info = pricing[SubscriptionPlan.AI_ADDON]
        ai_price_id = get_stripe_price_id("ai_addon", billing_interval)
        
        if ai_price_id:
            line_items.append({
                "price": ai_price_id,
                "quantity": 1,
            })
        else:
            # Fallback: dynamic price_data
            if is_annual and ai_info.get("amount_annual"):
                ai_amount = int(ai_info["amount_annual"] * 100)
                interval = "year"
            else:
                ai_amount = int(ai_info["amount"] * 100)
                interval = "month"
            
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "unit_amount": ai_amount,
                    "recurring": {"interval": interval},
                    "product_data": {
                        "name": ai_info["name"],
                        "description": ai_info.get("description", ""),
                    },
                },
                "quantity": 1,
            })
    
    # Check for trial credits (only for Business tier)
    trial_credits = 0
    if request.apply_trial_credits and request.plan == SubscriptionPlan.TIER_3:
        existing_sub = await db.subscriptions.find_one({
            "tenant_id": current_user.tenant_id,
            "extended_trial_paid": True,
            "trial_credits_used": {"$ne": True}
        })
        if existing_sub:
            trial_credits = existing_sub.get("trial_credits_applied", 0)
    
    metadata["trial_credits_applied"] = str(trial_credits)
    
    # Create subscription checkout session
    try:
        session_params = {
            "mode": "subscription",
            "payment_method_types": ["card"],
            "line_items": line_items,
            "customer_email": current_user.email,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata,
            "subscription_data": {
                "metadata": metadata,  # Also store on subscription for webhook access
            },
        }
        
        # Apply trial credits as a discount if available
        # Note: In production, you'd create a Stripe Coupon/Promotion Code
        # For now, we track credits separately and apply manually
        
        session = stripe.checkout.Session.create(**session_params)
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    
    # Calculate total amount for transaction record
    if is_annual and plan_info.get("amount_annual"):
        amount = float(plan_info["amount_annual"])
    else:
        amount = float(plan_info["amount"])
    
    if request.include_ai_addon and request.plan != SubscriptionPlan.AI_ADDON:
        ai_info = pricing[SubscriptionPlan.AI_ADDON]
        if is_annual and ai_info.get("amount_annual"):
            amount += float(ai_info["amount_annual"])
        else:
            amount += float(ai_info["amount"])
    
    # Record transaction
    transaction = PaymentTransaction(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        email=current_user.email,
        stripe_session_id=session.id,
        amount=amount,
        currency="usd",
        plan=request.plan,
        payment_status=PaymentStatus.INITIATED,
        is_founder_purchase=is_founder,
        metadata={
            "plan_name": plan_info["name"],
            "tier": plan_info["tier"],
            "include_ai_addon": request.include_ai_addon,
            "billing_interval": billing_interval,
            "trial_credits_applied": trial_credits,
            "checkout_mode": "subscription",
        }
    )
    
    await db.payment_transactions.insert_one(transaction.model_dump())
    
    return CheckoutResponse(url=session.url, session_id=session.id)


# ============== FOUNDERS EDITION CHECKOUT (v1) ==============

class FoundersCheckoutRequest(PydanticBaseModel):
    """Request for Founders Edition checkout"""
    billing_interval: str = "monthly"  # "monthly" or "annual"
    origin_url: str


class CreditPackCheckoutRequest(PydanticBaseModel):
    """Request for credit pack purchase"""
    pack_size: int  # 100, 300, or 1000
    origin_url: str


@router.post("/checkout/founders")
async def create_founders_checkout_session(
    request: FoundersCheckoutRequest,
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """
    Create Stripe checkout for Founders Edition subscription.
    
    Configuration: founder_pricing_v1
    
    Pricing:
    - Monthly: $99/month
    - Annual: $1188/year (or $594 with FOUNDERS promo code)
    
    Rules:
    - FOUNDERS promo: 50% off first annual payment, limited to 100 customers
    - All features included, no tiers
    - 150 AI credits/month included
    """
    import stripe
    from config.stripe_config import FounderPricingConfig
    
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    # Get subscription price ID
    price_id = FounderPricingConfig.get_subscription_price_id(request.billing_interval)
    
    if not price_id:
        raise HTTPException(
            status_code=400, 
            detail=f"Stripe Price ID not configured for {request.billing_interval}. Please contact support."
        )
    
    # Check founder availability
    founder_count = await db.tenants.count_documents({"founder_lifetime_lock": True})
    founders_remaining = max(0, 100 - founder_count)
    
    # Build URLs
    success_url = f"{request.origin_url}/settings/billing?success=true&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/settings/billing?canceled=true"
    
    # Build checkout params
    checkout_params = {
        "mode": "subscription",
        "payment_method_types": ["card"],
        "line_items": [{
            "price": price_id,
            "quantity": 1,
        }],
        "customer_email": current_user.email,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "plan": "founders_edition",
            "billing_interval": request.billing_interval,
            "configuration": "founder_pricing_v1",
        },
        "subscription_data": {
            "metadata": {
                "tenant_id": current_user.tenant_id,
                "plan": "founders_edition",
                "configuration": "founder_pricing_v1",
            },
        },
        "allow_promotion_codes": True,  # Customer can enter FOUNDERS code manually at checkout
    }
    
    try:
        session = stripe.checkout.Session.create(**checkout_params)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    
    # Record transaction (full price - discount applied at Stripe checkout)
    amount = 99.0 if request.billing_interval == "monthly" else 1188.0
    
    transaction = PaymentTransaction(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        email=current_user.email,
        stripe_session_id=session.id,
        amount=amount,
        currency="usd",
        plan=SubscriptionPlan.TIER_3,  # Map to highest tier for features
        payment_status=PaymentStatus.INITIATED,
        is_founder_purchase=True,
        metadata={
            "plan_name": "Founders Edition",
            "billing_interval": request.billing_interval,
            "promo_code": request.promo_code,
            "configuration": "founder_pricing_v1",
        }
    )
    
    await db.payment_transactions.insert_one(transaction.model_dump())
    
    return CheckoutResponse(url=session.url, session_id=session.id)


@router.post("/checkout/credits")
async def create_credit_pack_checkout_session(
    request: CreditPackCheckoutRequest,
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """
    Create Stripe checkout for AI credit pack purchase.
    
    Configuration: founder_pricing_v1
    
    Credit Packs:
    - 100 credits = $10 (one-time)
    - 300 credits = $25 (one-time)
    - 1000 credits = $60 (one-time)
    
    Rules:
    - Credits never expire during active subscription
    - Used after monthly credits are depleted
    """
    import stripe
    from config.stripe_config import FounderPricingConfig, CREDIT_PACK_MAPPING
    
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    # Validate pack size
    if request.pack_size not in CREDIT_PACK_MAPPING:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid pack size. Choose from: {list(CREDIT_PACK_MAPPING.keys())}"
        )
    
    pack_info = CREDIT_PACK_MAPPING[request.pack_size]
    price_id = FounderPricingConfig.get_credit_pack_price_id(request.pack_size)
    
    # Build URLs
    success_url = f"{request.origin_url}/settings/billing?credits_success=true&credits={request.pack_size}"
    cancel_url = f"{request.origin_url}/settings/billing?credits_canceled=true"
    
    # Build checkout params
    checkout_params = {
        "mode": "payment",  # One-time payment
        "payment_method_types": ["card"],
        "customer_email": current_user.email,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "purchase_type": "credit_pack",
            "credits": str(request.pack_size),
            "configuration": "founder_pricing_v1",
        },
    }
    
    if price_id:
        checkout_params["line_items"] = [{
            "price": price_id,
            "quantity": 1,
        }]
    else:
        # Fallback: dynamic price
        checkout_params["line_items"] = [{
            "price_data": {
                "currency": "usd",
                "unit_amount": int(pack_info["price"] * 100),
                "product_data": {
                    "name": f"AI Credits - {request.pack_size} Pack",
                    "description": f"{request.pack_size} AI credits - never expire during subscription",
                },
            },
            "quantity": 1,
        }]
    
    try:
        session = stripe.checkout.Session.create(**checkout_params)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    
    # Record transaction
    transaction = PaymentTransaction(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        email=current_user.email,
        stripe_session_id=session.id,
        amount=pack_info["price"],
        currency="usd",
        plan=SubscriptionPlan.AI_ADDON,  # Use AI addon enum for credit packs
        payment_status=PaymentStatus.INITIATED,
        is_founder_purchase=False,
        metadata={
            "purchase_type": "credit_pack",
            "credits": request.pack_size,
            "configuration": "founder_pricing_v1",
        }
    )
    
    await db.payment_transactions.insert_one(transaction.model_dump())
    
    return CheckoutResponse(url=session.url, session_id=session.id)


# ============== MULTI-PRODUCT CHECKOUT ==============


class MultiProductCheckoutRequest(PydanticBaseModel):
    """Request for multi-product checkout"""
    plan_type: str  # os_starter, os_pro, os_business, ws_launch, etc.
    billing_interval: str = "monthly"  # monthly or annual (annual only for os_business)
    use_founder_pricing: bool = False  # Only for OS plans
    origin_url: str


@router.post("/checkout/v2")
async def create_multi_product_checkout_session(
    request: MultiProductCheckoutRequest,
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """
    Create a Stripe checkout session for any plan across all 3 product lines.
    
    Product Lines:
    - OS: os_starter, os_pro, os_business (founder pricing available)
    - Webstores: ws_launch, ws_growth, ws_scale
    - AI Studio: ai_basic, ai_pro, ai_max
    
    Rules:
    - Founder pricing ONLY for OS plans
    - Annual billing ONLY for OS Business
    - Processing fees vary by plan and transaction type
    
    Stripe Price IDs configured in environment:
    - OS: STRIPE_PRICE_OS_STARTER_MONTHLY, STRIPE_PRICE_OS_PRO_MONTHLY, STRIPE_PRICE_OS_BUSINESS_MONTHLY/ANNUAL
    - Founder: STRIPE_PRICE_OS_*_FOUNDER_MONTHLY/ANNUAL
    - Webstores: STRIPE_PRICE_WS_LAUNCH/GROWTH/SCALE_MONTHLY
    - AI Studio: STRIPE_PRICE_AI_BASIC/PRO/MAX_MONTHLY
    """
    from models.product_tiers import PlanType
    from services.multi_product_billing import create_multi_product_checkout
    
    # Validate plan type
    try:
        plan_type = PlanType(request.plan_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid plan type: {request.plan_type}")
    
    result = await create_multi_product_checkout(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        email=current_user.email,
        plan_type=plan_type,
        billing_interval=request.billing_interval,
        use_founder_pricing=request.use_founder_pricing,
        origin_url=request.origin_url,
    )
    
    return result


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """Get status of a checkout session"""
    import stripe
    
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe.api_key = api_key
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    
    # Update transaction if paid
    if session.payment_status == "paid":
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
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "stripe_customer_id": session.customer,
                        "stripe_subscription_id": session.subscription,
                    }
                }
            )
            
            # Activate subscription (webhook should also handle this, but this is a fallback)
            await _activate_subscription_v2(
                db, 
                session_id=session_id,
                metadata=session.metadata or {},
                stripe_customer_id=session.customer,
                stripe_subscription_id=session.subscription
            )
    
    return {
        "status": session.status,
        "payment_status": session.payment_status,
        "amount": (session.amount_total or 0) / 100,
        "currency": session.currency,
        "mode": session.mode,  # "subscription" or "payment"
        "subscription_id": session.subscription,
        "customer_id": session.customer,
    }


async def _activate_subscription(db, session_id: str, metadata: dict):
    """Activate subscription after successful payment"""
    tenant_id = metadata.get("tenant_id")
    plan_str = metadata.get("plan")
    tier = metadata.get("tier", "starter")
    is_founder = metadata.get("is_founder", "false") == "true"
    include_ai_addon = metadata.get("include_ai_addon", "false") == "true"
    billing_interval = metadata.get("billing_interval", "monthly")
    trial_credits_applied = float(metadata.get("trial_credits_applied", "0"))
    
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
            "billing_interval": "monthly",
            "is_founder": is_founder,
            "has_ai_addon": True,  # Full access during trial
            "trial_start": now.isoformat(),
            "trial_end": trial_end.isoformat(),
            "trial_credits_applied": amount_paid,  # $19.99 credits toward Business subscription
            "trial_credits_used": False,  # Not yet used
            "extended_trial_paid": True,
            "amount_paid": amount_paid,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
    else:
        # Regular subscription - period depends on billing interval
        if billing_interval == "annual":
            period_end = now + timedelta(days=365)
        else:
            period_end = now + timedelta(days=30)
        
        # Mark trial credits as used if they were applied
        mark_credits_used = trial_credits_applied > 0
        
        subscription_data = {
            "tenant_id": tenant_id,
            "plan": plan.value,
            "status": SubscriptionStatus.ACTIVE.value,
            "tier": tier,
            "billing_interval": billing_interval,
            "is_founder": is_founder,
            "founder_number": founder_number,
            "founder_locked_at": now.isoformat() if is_founder else None,
            "has_ai_addon": include_ai_addon or plan == SubscriptionPlan.AI_ADDON,
            "current_period_start": now.isoformat(),
            "current_period_end": period_end.isoformat(),
            "amount_paid": amount_paid,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        # If trial credits were applied, mark them as used
        if mark_credits_used:
            subscription_data["trial_credits_used"] = True
    
    # Upsert subscription
    await db.subscriptions.update_one(
        {"tenant_id": tenant_id},
        {"$set": subscription_data},
        upsert=True
    )
    
    # Update tenant with tier and founder status
    tenant_update = {
        "plan": tier,
        "is_founder": is_founder,
        "subscription_status": "active" if plan != SubscriptionPlan.EXTENDED_TRIAL else "trialing",
        "updated_at": now.isoformat()
    }
    if founder_number:
        tenant_update["founder_number"] = founder_number
    
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": tenant_update}
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
            billing_interval="monthly",
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
    
    # Calculate next billing amount
    next_billing = None
    if sub.status == SubscriptionStatus.ACTIVE:
        billing_interval = getattr(sub, 'billing_interval', 'monthly')
        if billing_interval == "annual":
            next_billing = plan_info.get("amount_annual", plan_info.get("amount", 0))
        else:
            next_billing = plan_info.get("amount", 0)
    
    # Check if trial credits are available (paid but not used)
    trial_credits_available = (
        sub.extended_trial_paid and 
        sub.trial_credits_applied > 0 and 
        not getattr(sub, 'trial_credits_used', False)
    )
    
    return SubscriptionResponse(
        plan=sub.plan.value if isinstance(sub.plan, SubscriptionPlan) else sub.plan,
        plan_name=plan_name,
        status=sub.status.value if isinstance(sub.status, SubscriptionStatus) else sub.status,
        tier=sub.tier,
        billing_interval=getattr(sub, 'billing_interval', 'monthly'),
        is_founder=sub.is_founder,
        founder_number=sub.founder_number,
        has_ai_addon=sub.has_ai_addon,
        trial_end=sub.trial_end,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        trial_credits=sub.trial_credits_applied,
        trial_credits_available=trial_credits_available,
        amount_paid=getattr(sub, 'amount_paid', 0),
        next_billing_amount=next_billing,
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


@router.get("/trial-credits")
async def get_trial_credits(
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """Get available trial credits for the current user"""
    subscription = await db.subscriptions.find_one(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not subscription:
        return {
            "has_credits": False,
            "credits_amount": 0,
            "credits_used": False,
            "eligible_for_tier3": False
        }
    
    credits = subscription.get("trial_credits_applied", 0)
    credits_used = subscription.get("trial_credits_used", False)
    extended_paid = subscription.get("extended_trial_paid", False)
    
    return {
        "has_credits": credits > 0 and not credits_used,
        "credits_amount": credits,
        "credits_used": credits_used,
        "extended_trial_paid": extended_paid,
        "eligible_for_business": credits > 0 and not credits_used,
        "message": f"${credits:.2f} credit available towards Business subscription" if credits > 0 and not credits_used else None
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
                "plan": t.get("plan") or t.get("plan_type"),
                "status": t["payment_status"],
                "is_founder": t.get("is_founder_purchase") or t.get("is_founder", False),
                "created_at": t["created_at"],
                "paid_at": t.get("paid_at")
            }
            for t in transactions
        ]
    }


# ============== MULTI-PRODUCT SUBSCRIPTION V2 ==============

@router.get("/subscription/v2")
async def get_subscription_v2(
    db = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user_billing)
):
    """
    Get subscription details for the new multi-product system.
    Returns plan_type (os_starter, ws_launch, etc.) and product_line (os, webstores, ai_studio).
    """
    from services.plan_configs import get_plan_config
    from services.multi_product_gate import get_multi_product_feature_gate
    from models.product_tiers import PlanType, ProductLine
    
    subscription = await db.subscriptions.find_one(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0}
    )
    
    # Determine current plan
    plan_str = None
    product_line = None  # noqa: F841 - may be used in future
    is_founder = False
    
    if subscription:
        plan_str = subscription.get("plan")
        product_line = subscription.get("product_line")  # noqa: F841
        is_founder = subscription.get("is_founder", False)
    
    if not plan_str and tenant:
        plan_str = tenant.get("plan")
        product_line = tenant.get("product_line")  # noqa: F841
        is_founder = tenant.get("is_founder", False)
    
    # Default to OS Starter for new tenants
    if not plan_str:
        plan_str = "os_starter"
    
    # Try to parse as PlanType enum
    try:
        plan_type = PlanType(plan_str)
    except ValueError:
        # Handle legacy plan names
        legacy_map = {
            "starter": PlanType.OS_STARTER,
            "pro": PlanType.OS_PRO,
            "business": PlanType.OS_BUSINESS,
            "tier_1": PlanType.OS_STARTER,
            "tier_2": PlanType.OS_PRO,
            "tier_3": PlanType.OS_BUSINESS,
        }
        plan_type = legacy_map.get(plan_str.lower(), PlanType.OS_STARTER)
    
    config = get_plan_config(plan_type)
    
    # Get UI visibility from gate service
    gate = get_multi_product_feature_gate(db)
    ui_visibility = await gate.get_ui_visibility(current_user.tenant_id)
    
    return {
        # Plan info
        "plan_type": plan_type.value,
        "plan_display_name": config.display_name,
        "product_line": config.product_line.value,
        "product_line_display": {
            "os": "SignGuy AI OS",
            "webstores": "SignGuy Webstores",
            "ai_studio": "SignGuy AI Studio"
        }.get(config.product_line.value, config.product_line.value),
        
        # Status
        "status": subscription.get("status", "active") if subscription else "trialing",
        "is_founder": is_founder,
        "founder_number": subscription.get("founder_number") if subscription else tenant.get("founder_number") if tenant else None,
        
        # Billing
        "billing_interval": subscription.get("billing_interval", "monthly") if subscription else "monthly",
        "current_period_end": subscription.get("current_period_end") if subscription else None,
        
        # Pricing
        "pricing": {
            "monthly": config.pricing.monthly,
            "annual": config.pricing.annual,
            "founder_monthly": config.pricing.founder_monthly,
            "founder_annual": config.pricing.founder_annual,
        },
        
        # Processing fees
        "processing_fees": {
            "invoice": config.processing_fees.invoice_fee_percent,
            "webstore": config.processing_fees.webstore_fee_percent,
            "stripe_connect_enabled": config.processing_fees.stripe_connect_enabled,
            "online_payments_enabled": config.processing_fees.online_payments_enabled,
        },
        
        # UI visibility
        "ui_visibility": ui_visibility,
        
        # Available upgrades
        "upgrade_options": _get_upgrade_options(plan_type),
    }


def _get_upgrade_options(current_plan) -> list:
    """Get available upgrade options based on current plan"""
    from models.product_tiers import PlanType, ProductLine
    from services.plan_configs import get_plan_config
    
    config = get_plan_config(current_plan)
    product_line = config.product_line
    
    upgrades = []
    
    if product_line == ProductLine.OS:
        if current_plan == PlanType.OS_STARTER:
            upgrades = [
                {"plan_type": "os_pro", "display_name": "Pro", "monthly_price": 79},
                {"plan_type": "os_business", "display_name": "Business", "monthly_price": 149},
            ]
        elif current_plan == PlanType.OS_PRO:
            upgrades = [
                {"plan_type": "os_business", "display_name": "Business", "monthly_price": 149},
            ]
    elif product_line == ProductLine.WEBSTORES:
        if current_plan == PlanType.WS_LAUNCH:
            upgrades = [
                {"plan_type": "ws_growth", "display_name": "Growth", "monthly_price": 59},
                {"plan_type": "ws_scale", "display_name": "Scale", "monthly_price": 99},
            ]
        elif current_plan == PlanType.WS_GROWTH:
            upgrades = [
                {"plan_type": "ws_scale", "display_name": "Scale", "monthly_price": 99},
            ]
    elif product_line == ProductLine.AI_STUDIO:
        if current_plan == PlanType.AI_BASIC:
            upgrades = [
                {"plan_type": "ai_pro", "display_name": "AI Pro", "monthly_price": 59},
                {"plan_type": "ai_max", "display_name": "AI Max", "monthly_price": 99},
            ]
        elif current_plan == PlanType.AI_PRO:
            upgrades = [
                {"plan_type": "ai_max", "display_name": "AI Max", "monthly_price": 99},
            ]
    
    return upgrades


# ============== WEBHOOK HANDLER ==============

@webhook_router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db = Depends(get_db)):
    """
    Handle Stripe webhook events for BOTH legacy and multi-product billing systems.
    
    Routes to appropriate handler based on metadata:
    - If metadata contains 'plan_type' (os_starter, ws_launch, etc.) → multi_product_billing handlers
    - Otherwise → legacy billing handlers
    
    Supported events:
    - checkout.session.completed: Initial payment success
    - customer.subscription.created: New subscription created
    - customer.subscription.updated: Subscription modified (upgrade/downgrade/renewal)
    - customer.subscription.deleted: Subscription cancelled
    - invoice.payment_succeeded: Recurring payment success
    - invoice.payment_failed: Payment failed (card declined, etc.)
    """
    import stripe
    from services.multi_product_billing import (
        handle_checkout_completed,
        handle_subscription_created,
        handle_subscription_updated,
        handle_subscription_deleted,
        handle_invoice_payment_succeeded,
        handle_invoice_payment_failed,
    )
    
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe.api_key = api_key
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    try:
        # Verify webhook signature if secret is configured
        if webhook_secret:
            event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        else:
            # Fallback for development without webhook secret
            import json
            event = stripe.Event.construct_from(json.loads(body), api_key)
        
        event_type = event.type
        event_data = event.data.object
        metadata = getattr(event_data, 'metadata', {}) or {}
        
        # Check if this is a multi-product checkout (new system)
        is_multi_product = 'plan_type' in metadata and metadata.get('plan_type', '').startswith(('os_', 'ws_', 'ai_'))
        
        now = datetime.now(timezone.utc)
        
        # ==================== CHECKOUT SESSION COMPLETED ====================
        if event_type == "checkout.session.completed":
            if is_multi_product:
                # Use new multi-product handler
                await handle_checkout_completed(db, event_data)
            else:
                # Legacy handler for old-style checkouts
                session_id = event_data.id
                payment_status = event_data.payment_status
                checkout_mode = event_data.mode
                
                await db.payment_transactions.update_one(
                    {"stripe_session_id": session_id},
                    {"$set": {
                        "payment_status": PaymentStatus.PAID.value if payment_status == "paid" else PaymentStatus.PENDING.value,
                        "paid_at": now.isoformat() if payment_status == "paid" else None,
                        "updated_at": now.isoformat(),
                        "stripe_customer_id": event_data.customer,
                        "stripe_subscription_id": event_data.subscription
                    }}
                )
                
                if payment_status == "paid":
                    current_period_end = None
                    if checkout_mode == "subscription" and event_data.subscription:
                        try:
                            stripe_sub = stripe.Subscription.retrieve(event_data.subscription)
                            current_period_end = datetime.fromtimestamp(
                                stripe_sub.current_period_end, tz=timezone.utc
                            ).isoformat()
                        except stripe.error.StripeError:
                            pass
                    
                    await _activate_subscription_v2(
                        db, 
                        session_id=session_id,
                        metadata=metadata,
                        stripe_customer_id=event_data.customer,
                        stripe_subscription_id=event_data.subscription,
                        current_period_end=current_period_end
                    )
        
        # ==================== SUBSCRIPTION CREATED ====================
        elif event_type == "customer.subscription.created":
            # Multi-product handler works for both - it just updates by stripe_subscription_id
            await handle_subscription_created(db, event_data)
        
        # ==================== SUBSCRIPTION UPDATED ====================
        elif event_type == "customer.subscription.updated":
            # Multi-product handler works for both
            await handle_subscription_updated(db, event_data)
        
        # ==================== SUBSCRIPTION DELETED/CANCELLED ====================
        elif event_type == "customer.subscription.deleted":
            # Multi-product handler works for both
            await handle_subscription_deleted(db, event_data)
        
        # ==================== INVOICE PAYMENT SUCCEEDED ====================
        elif event_type == "invoice.payment_succeeded":
            # Multi-product handler works for both
            await handle_invoice_payment_succeeded(db, event_data)
        
        # ==================== INVOICE PAYMENT FAILED ====================
        elif event_type == "invoice.payment_failed":
            # Multi-product handler works for both
            await handle_invoice_payment_failed(db, event_data)
        
        return {"status": "success", "event_type": event_type}
    
    except stripe.error.SignatureVerificationError as e:
        print(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        print(f"Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def _map_stripe_status(stripe_status: str) -> str:
    """Map Stripe subscription status to our internal status"""
    status_map = {
        "active": SubscriptionStatus.ACTIVE.value,
        "past_due": SubscriptionStatus.PAST_DUE.value,
        "canceled": SubscriptionStatus.CANCELLED.value,
        "cancelled": SubscriptionStatus.CANCELLED.value,
        "unpaid": SubscriptionStatus.PAST_DUE.value,
        "trialing": SubscriptionStatus.TRIALING.value,
        "incomplete": SubscriptionStatus.PENDING.value,
        "incomplete_expired": SubscriptionStatus.EXPIRED.value,
    }
    return status_map.get(stripe_status, SubscriptionStatus.ACTIVE.value)


async def _activate_subscription_v2(
    db, 
    session_id: str, 
    metadata: dict,
    stripe_customer_id: str = None,
    stripe_subscription_id: str = None,
    current_period_end: str = None
):
    """
    Activate subscription after successful checkout.
    
    For real subscriptions: Stores Stripe IDs, period_end comes from Stripe.
    For extended trial: One-time payment, 14-day access, no Stripe subscription.
    """
    tenant_id = metadata.get("tenant_id")
    plan_str = metadata.get("plan")
    tier = metadata.get("tier", "starter")
    is_founder = metadata.get("is_founder", "false") == "true"
    include_ai_addon = metadata.get("include_ai_addon", "false") == "true"
    billing_interval = metadata.get("billing_interval", "monthly")
    trial_credits_applied = float(metadata.get("trial_credits_applied", "0"))
    
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
        # ==================== EXTENDED TRIAL: ONE-TIME PAYMENT ====================
        # NOT a recurring subscription - grants 14-day full access
        # $19.99 credits toward future Business subscription
        trial_end = now + timedelta(days=14)
        subscription_data = {
            "tenant_id": tenant_id,
            "plan": plan.value,
            "status": SubscriptionStatus.TRIALING.value,
            "tier": "business",  # Full access during trial
            "billing_interval": "monthly",
            "is_founder": is_founder,
            "has_ai_addon": True,  # Full access during trial
            "trial_start": now.isoformat(),
            "trial_end": trial_end.isoformat(),
            "trial_credits_applied": amount_paid,  # $19.99 credit
            "trial_credits_used": False,
            "extended_trial_paid": True,
            "amount_paid": amount_paid,
            "stripe_customer_id": stripe_customer_id,
            # No stripe_subscription_id for one-time payment
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
    else:
        # ==================== REAL SUBSCRIPTION ====================
        # Stripe is source of truth for billing cycle
        subscription_data = {
            "tenant_id": tenant_id,
            "plan": plan.value,
            "status": SubscriptionStatus.ACTIVE.value,
            "tier": tier,
            "billing_interval": billing_interval,
            "is_founder": is_founder,
            "founder_number": founder_number,
            "founder_locked_at": now.isoformat() if is_founder else None,
            "has_ai_addon": include_ai_addon or plan == SubscriptionPlan.AI_ADDON,
            "current_period_start": now.isoformat(),
            "amount_paid": amount_paid,
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        # Use Stripe's current_period_end if provided (source of truth)
        if current_period_end:
            subscription_data["current_period_end"] = current_period_end
        
        if trial_credits_applied > 0:
            subscription_data["trial_credits_used"] = True
    
    # Upsert subscription
    await db.subscriptions.update_one(
        {"tenant_id": tenant_id},
        {"$set": subscription_data},
        upsert=True
    )
    
    # Update tenant with tier and founder status
    tenant_update = {
        "plan": tier,
        "is_founder": is_founder,
        "subscription_status": "active" if plan != SubscriptionPlan.EXTENDED_TRIAL else "trialing",
        "updated_at": now.isoformat()
    }
    if founder_number:
        tenant_update["founder_number"] = founder_number
    
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": tenant_update}
    )


# Keep old function for backwards compatibility
async def _activate_subscription(db, session_id: str, metadata: dict):
    """Legacy activation function - redirects to v2"""
    await _activate_subscription_v2(db, session_id, metadata)
