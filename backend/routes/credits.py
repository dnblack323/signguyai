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
from services.credit_service import (
    preview_credit_usage,
    deduct_credits_after_success,
    log_failed_ai_usage,
    get_or_create_credit_record,
    check_and_refill_monthly_credits as service_check_and_refill_monthly_credits,
)

router = APIRouter(prefix="/credits", tags=["AI Credits"])

# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# ============== HELPER FUNCTIONS ==============

async def get_or_create_user_credits(tenant_id: str) -> dict:
    """Get user credits record or create one if it doesn't exist"""
    return await get_or_create_credit_record(db, tenant_id)


async def check_and_refill_monthly_credits(tenant_id: str) -> dict:
    """Check if monthly credits need to be refilled and do so if needed"""
    return await service_check_and_refill_monthly_credits(db, tenant_id)


def default_credit_preferences() -> dict:
    return {
        "hide_ai_credit_popup": False,
        "acknowledged_costs": {},
    }


async def get_credit_preferences_for_user(user_id: str, tenant_id: str) -> dict:
    prefs = await db.ai_credit_preferences.find_one({"user_id": user_id, "tenant_id": tenant_id}, {"_id": 0})
    return {**default_credit_preferences(), **(prefs or {"user_id": user_id, "tenant_id": tenant_id})}


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


@router.get("/preferences")
async def get_credit_preferences(current_user: UserInDB = Depends(get_current_active_user)):
    return await get_credit_preferences_for_user(current_user.id, current_user.tenant_id)


@router.put("/preferences")
async def update_credit_preferences(payload: Dict[str, Any], current_user: UserInDB = Depends(get_current_active_user)):
    current = await get_credit_preferences_for_user(current_user.id, current_user.tenant_id)
    updated = {
        **current,
        "hide_ai_credit_popup": payload.get("hide_ai_credit_popup", current.get("hide_ai_credit_popup", False)),
        "acknowledged_costs": payload.get("acknowledged_costs", current.get("acknowledged_costs", {})),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.ai_credit_preferences.update_one(
        {"user_id": current_user.id, "tenant_id": current_user.tenant_id},
        {"$set": updated},
        upsert=True,
    )
    updated.pop("_id", None)
    return updated


@router.post("/preflight")
async def preflight_ai_credit_check(
    payload: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user)
):
    action_type = payload.get("action_type")
    if not action_type:
        raise HTTPException(status_code=400, detail="action_type is required")

    preview = await preview_credit_usage(db, current_user.tenant_id, action_type, payload.get("credits_required"))
    prefs = await get_credit_preferences_for_user(current_user.id, current_user.tenant_id)
    acknowledged_cost = (prefs.get("acknowledged_costs") or {}).get(action_type)

    popup_reasons = []
    if not prefs.get("hide_ai_credit_popup"):
        popup_reasons.append("preference_off")
    if acknowledged_cost != preview["credit_cost"]:
        popup_reasons.append("cost_changed")
    if preview["is_low_credits"] or preview["total_credits"] < preview["credit_cost"]:
        popup_reasons.append("low_balance")
    if preview["will_use_purchased"]:
        popup_reasons.append("purchased_credits_needed")
    if preview["credit_cost"] >= 3:
        popup_reasons.append("high_cost_action")

    return {
        **preview,
        "preferences": prefs,
        "should_show_popup": len(popup_reasons) > 0,
        "popup_reasons": popup_reasons,
    }


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
    
    preview = await preview_credit_usage(db, tenant_id, request.action_type, request.credits_required)
    if not preview["sufficient_credits"]:
        return CreditUsageResponse(
            success=False,
            credits_used=0,
            monthly_credits_used=0,
            purchased_credits_used=0,
            remaining_monthly=preview["monthly_credits"],
            remaining_purchased=preview["purchased_credits"],
            remaining_total=preview["total_credits"],
            is_low_credits=preview["is_low_credits"],
            message=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}."
        )
    result = await deduct_credits_after_success(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action_type=request.action_type,
        module=request.metadata.get("module", "manual"),
        feature_name=request.metadata.get("feature_name", request.action_type),
        metadata=request.metadata,
        credits_required=request.credits_required,
    )
    
    return CreditUsageResponse(
        success=True,
        credits_used=result["credit_cost"],
        monthly_credits_used=result["monthly_credits_to_use"],
        purchased_credits_used=result["purchased_credits_to_use"],
        remaining_monthly=result["remaining_monthly"],
        remaining_purchased=result["remaining_purchased"],
        remaining_total=result["remaining_total"],
        is_low_credits=result["remaining_total"] <= result["low_credits_threshold"],
        message=f"Used {result['credit_cost']} credits for {request.action_type}"
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


@router.get("/admin-summary")
async def get_admin_credit_summary(current_user: UserInDB = Depends(get_current_active_user)):
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only admins and owners can view AI usage summary")

    tenant_id = current_user.tenant_id
    balance = await get_credit_balance(current_user)
    usage_entries = await db.ai_usage_logs.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)

    by_tool = {}
    by_user = {}
    for entry in usage_entries:
        tool_key = entry.get("action_type")
        user_key = entry.get("user_id")
        by_tool.setdefault(tool_key, {"action_type": tool_key, "credits_used": 0, "count": 0})
        by_tool[tool_key]["credits_used"] += entry.get("credits_charged", 0)
        by_tool[tool_key]["count"] += 1
        by_user.setdefault(user_key, {"user_id": user_key, "credits_used": 0, "count": 0})
        by_user[user_key]["credits_used"] += entry.get("credits_charged", 0)
        by_user[user_key]["count"] += 1

    monthly_consumed = sum(entry.get("monthly_credits_used", 0) for entry in usage_entries if entry.get("status") == "success")
    purchased_consumed = sum(entry.get("purchased_credits_used", 0) for entry in usage_entries if entry.get("status") == "success")

    return {
        "balance": balance.model_dump() if hasattr(balance, 'model_dump') else balance,
        "total_ai_credits_used": sum(entry.get("credits_charged", 0) for entry in usage_entries if entry.get("status") == "success"),
        "monthly_credits_consumed": monthly_consumed,
        "purchased_credits_consumed": purchased_consumed,
        "by_tool": sorted(by_tool.values(), key=lambda item: item["credits_used"], reverse=True),
        "by_user": sorted(by_user.values(), key=lambda item: item["credits_used"], reverse=True),
        "recent_usage": usage_entries[:20],
    }
