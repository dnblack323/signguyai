"""
AI Credits Routes

Handles:
- Credit balance queries
- Credit usage (deduction)
- Credit pack purchases via Stripe
- Monthly credit refill
- Credit transaction history
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import os
import stripe

from server import db, get_current_active_user, logger
from models import UserInDB
from models.credits import (
    UserCredits, CreditTransaction, CreditTransactionType,
    CreditPackType,
    CreditUsageRequest, CreditUsageResponse,
    CreditBalanceResponse, PurchaseCreditPackRequest, PurchaseCreditPackResponse
)
from services.founders_config import (
    FOUNDERS_EDITION_MONTHLY_CREDITS, 
    get_ai_credit_cost, 
    get_credit_packs_for_api,
    LOW_CREDITS_THRESHOLD,
    CREDIT_PACKS
)

router = APIRouter(prefix="/credits", tags=["AI Credits"])

# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# ============== HELPER FUNCTIONS ==============

async def get_or_create_user_credits(tenant_id: str) -> dict:
    """Get user credits record or create one if it doesn't exist"""
    credits = await db.user_credits.find_one({"tenant_id": tenant_id}, {"_id": 0})
    
    if not credits:
        # Create new credits record for Founders Edition user
        now = datetime.now(timezone.utc)
        period_end = now + relativedelta(months=1)
        
        new_credits = UserCredits(
            tenant_id=tenant_id,
            monthly_credits=FOUNDERS_EDITION_MONTHLY_CREDITS,
            purchased_credits=0,
            monthly_credits_granted_at=now.isoformat(),
            monthly_credits_period_start=now.isoformat(),
            monthly_credits_period_end=period_end.isoformat(),
        )
        credits_doc = new_credits.model_dump()
        await db.user_credits.insert_one(credits_doc)
        
        # Record the initial grant transaction
        transaction = CreditTransaction(
            tenant_id=tenant_id,
            transaction_type=CreditTransactionType.MONTHLY_GRANT,
            amount=FOUNDERS_EDITION_MONTHLY_CREDITS,
            balance_after=FOUNDERS_EDITION_MONTHLY_CREDITS,
            monthly_balance_after=FOUNDERS_EDITION_MONTHLY_CREDITS,
            purchased_balance_after=0,
            description=f"Initial monthly credit grant: {FOUNDERS_EDITION_MONTHLY_CREDITS} credits"
        )
        await db.credit_transactions.insert_one(transaction.model_dump())
        
        credits = credits_doc
    
    return credits


async def check_and_refill_monthly_credits(tenant_id: str) -> dict:
    """Check if monthly credits need to be refilled and do so if needed"""
    credits = await get_or_create_user_credits(tenant_id)
    
    if not credits.get("monthly_credits_period_end"):
        return credits
    
    period_end = datetime.fromisoformat(credits["monthly_credits_period_end"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    
    if now >= period_end:
        # Time to refill! First expire remaining monthly credits
        old_monthly = credits.get("monthly_credits", 0)
        purchased = credits.get("purchased_credits", 0)
        
        # Record expiration if there were remaining credits
        if old_monthly > 0:
            expire_transaction = CreditTransaction(
                tenant_id=tenant_id,
                transaction_type=CreditTransactionType.MONTHLY_EXPIRE,
                amount=-old_monthly,
                balance_after=purchased + FOUNDERS_EDITION_MONTHLY_CREDITS,
                monthly_balance_after=0,
                purchased_balance_after=purchased,
                description=f"Monthly credits expired: {old_monthly} credits"
            )
            await db.credit_transactions.insert_one(expire_transaction.model_dump())
        
        # Set new period
        new_period_start = now
        new_period_end = now + relativedelta(months=1)
        
        # Grant new monthly credits
        await db.user_credits.update_one(
            {"tenant_id": tenant_id},
            {
                "$set": {
                    "monthly_credits": FOUNDERS_EDITION_MONTHLY_CREDITS,
                    "monthly_credits_granted_at": now.isoformat(),
                    "monthly_credits_period_start": new_period_start.isoformat(),
                    "monthly_credits_period_end": new_period_end.isoformat(),
                    "updated_at": now.isoformat()
                }
            }
        )
        
        # Record the grant transaction
        grant_transaction = CreditTransaction(
            tenant_id=tenant_id,
            transaction_type=CreditTransactionType.MONTHLY_GRANT,
            amount=FOUNDERS_EDITION_MONTHLY_CREDITS,
            balance_after=purchased + FOUNDERS_EDITION_MONTHLY_CREDITS,
            monthly_balance_after=FOUNDERS_EDITION_MONTHLY_CREDITS,
            purchased_balance_after=purchased,
            description=f"Monthly credit grant: {FOUNDERS_EDITION_MONTHLY_CREDITS} credits"
        )
        await db.credit_transactions.insert_one(grant_transaction.model_dump())
        
        # Return updated credits
        credits = await db.user_credits.find_one({"tenant_id": tenant_id}, {"_id": 0})
    
    return credits


# ============== ROUTES ==============

@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current credit balance for the user's tenant"""
    tenant_id = current_user.tenant_id
    
    # Check and refill if needed
    credits = await check_and_refill_monthly_credits(tenant_id)
    
    monthly = credits.get("monthly_credits", 0)
    purchased = credits.get("purchased_credits", 0)
    total = monthly + purchased
    threshold = credits.get("low_credits_threshold", 20)
    
    # Calculate days until refill
    days_until_refill = None
    if credits.get("monthly_credits_period_end"):
        period_end = datetime.fromisoformat(credits["monthly_credits_period_end"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = period_end - now
        days_until_refill = max(0, delta.days)
    
    return CreditBalanceResponse(
        monthly_credits=monthly,
        purchased_credits=purchased,
        total_credits=total,
        is_low_credits=total <= threshold,
        low_credits_threshold=threshold,
        monthly_credits_period_end=credits.get("monthly_credits_period_end"),
        days_until_refill=days_until_refill
    )


@router.post("/use", response_model=CreditUsageResponse)
async def use_credits(
    request: CreditUsageRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Use credits for an AI action.
    Monthly credits are used first, then purchased credits.
    """
    tenant_id = current_user.tenant_id
    
    # Check and refill if needed
    credits = await check_and_refill_monthly_credits(tenant_id)
    
    monthly = credits.get("monthly_credits", 0)
    purchased = credits.get("purchased_credits", 0)
    total = monthly + purchased
    threshold = credits.get("low_credits_threshold", 20)
    
    credits_needed = request.credits_required
    
    # Check if user has enough credits
    if total < credits_needed:
        return CreditUsageResponse(
            success=False,
            credits_used=0,
            monthly_credits_used=0,
            purchased_credits_used=0,
            remaining_monthly=monthly,
            remaining_purchased=purchased,
            remaining_total=total,
            is_low_credits=total <= threshold,
            message=f"Insufficient credits. Need {credits_needed}, have {total}."
        )
    
    # Use monthly credits first, then purchased
    monthly_used = min(monthly, credits_needed)
    purchased_used = credits_needed - monthly_used
    
    new_monthly = monthly - monthly_used
    new_purchased = purchased - purchased_used
    new_total = new_monthly + new_purchased
    
    # Update database
    await db.user_credits.update_one(
        {"tenant_id": tenant_id},
        {
            "$set": {
                "monthly_credits": new_monthly,
                "purchased_credits": new_purchased,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Record transaction
    transaction = CreditTransaction(
        tenant_id=tenant_id,
        transaction_type=CreditTransactionType.AI_USAGE,
        amount=-credits_needed,
        balance_after=new_total,
        monthly_balance_after=new_monthly,
        purchased_balance_after=new_purchased,
        description=f"AI action: {request.action_type}",
        metadata={
            "action_type": request.action_type,
            "monthly_used": monthly_used,
            "purchased_used": purchased_used,
            **request.metadata
        }
    )
    await db.credit_transactions.insert_one(transaction.model_dump())
    
    return CreditUsageResponse(
        success=True,
        credits_used=credits_needed,
        monthly_credits_used=monthly_used,
        purchased_credits_used=purchased_used,
        remaining_monthly=new_monthly,
        remaining_purchased=new_purchased,
        remaining_total=new_total,
        is_low_credits=new_total <= threshold,
        message=f"Used {credits_needed} credits for {request.action_type}"
    )


@router.get("/packs")
async def get_credit_packs(current_user: UserInDB = Depends(get_current_active_user)):
    """Get available credit packs for purchase"""
    return {
        "packs": get_credit_packs_for_api()
    }


@router.post("/purchase")
async def purchase_credit_pack(
    request: PurchaseCreditPackRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create a Stripe checkout session to purchase a credit pack.
    After successful payment, credits will be added via webhook.
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    pack_type = request.pack_type.value
    
    # Find the pack in our config
    pack = None
    for pack_key, pack_info in CREDIT_PACKS.items():
        if pack_info["pack_id"] == pack_type:
            pack = pack_info
            break
    
    if not pack:
        raise HTTPException(status_code=400, detail="Invalid credit pack type")
    
    tenant_id = current_user.tenant_id
    
    # Get the frontend URL for redirect
    frontend_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:3000")
    
    try:
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": pack["display_name"],
                        "description": pack["description"],
                    },
                    "unit_amount": pack["price_cents"],
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{frontend_url}/settings?credits=success&pack={pack_type}",
            cancel_url=f"{frontend_url}/settings?credits=cancelled",
            metadata={
                "tenant_id": tenant_id,
                "user_id": current_user.id,
                "pack_type": pack_type,
                "credits": pack["credits"],
                "type": "credit_pack_purchase"
            }
        )
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment session")


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhooks for credit pack purchases.
    Called by Stripe after successful payment.
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            # For testing without webhook signature verification
            import json
            event = json.loads(payload)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        
        if metadata.get("type") == "credit_pack_purchase":
            tenant_id = metadata.get("tenant_id")
            credits_to_add = int(metadata.get("credits", 0))
            pack_type = metadata.get("pack_type")
            
            if tenant_id and credits_to_add > 0:
                # Get current credits
                credits = await get_or_create_user_credits(tenant_id)
                current_purchased = credits.get("purchased_credits", 0)
                current_monthly = credits.get("monthly_credits", 0)
                new_purchased = current_purchased + credits_to_add
                new_total = current_monthly + new_purchased
                
                # Update purchased credits
                await db.user_credits.update_one(
                    {"tenant_id": tenant_id},
                    {
                        "$set": {
                            "purchased_credits": new_purchased,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                # Record transaction
                transaction = CreditTransaction(
                    tenant_id=tenant_id,
                    transaction_type=CreditTransactionType.PACK_PURCHASE,
                    amount=credits_to_add,
                    balance_after=new_total,
                    monthly_balance_after=current_monthly,
                    purchased_balance_after=new_purchased,
                    description=f"Purchased {pack_type}: +{credits_to_add} credits",
                    metadata={
                        "pack_type": pack_type,
                        "stripe_session_id": session.get("id"),
                        "stripe_payment_intent": session.get("payment_intent")
                    }
                )
                await db.credit_transactions.insert_one(transaction.model_dump())
                
                logger.info(f"Added {credits_to_add} credits to tenant {tenant_id}")
    
    return {"status": "success"}


@router.get("/history")
async def get_credit_history(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get credit transaction history for the user's tenant"""
    tenant_id = current_user.tenant_id
    
    transactions = await db.credit_transactions.find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
    
    total = await db.credit_transactions.count_documents({"tenant_id": tenant_id})
    
    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/cost/{action_type}")
async def get_action_credit_cost(
    action_type: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get the credit cost for a specific AI action"""
    cost = get_ai_credit_cost(action_type)
    return {
        "action_type": action_type,
        "credit_cost": cost
    }


@router.get("/costs")
async def get_all_credit_costs(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all AI action credit costs"""
    from services.founders_config import AI_CREDIT_COSTS
    return {
        "costs": AI_CREDIT_COSTS
    }
