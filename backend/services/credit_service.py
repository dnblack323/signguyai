"""
AI Credit Integration Service

Provides helper functions for checking and deducting credits
before AI actions are performed.
"""

from typing import Optional, Tuple
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from services.founders_config import (
    get_ai_credit_cost, FOUNDERS_EDITION_MONTHLY_CREDITS, AI_CREDIT_COSTS
)
from models.credits import (
    CreditTransaction, CreditTransactionType, UserCredits
)


async def check_and_deduct_credits(
    db, 
    tenant_id: str, 
    action_type: str,
    metadata: dict = None
) -> Tuple[bool, int, str]:
    """
    Check if user has enough credits and deduct if so.
    
    Returns:
        Tuple of (success, credits_used, message)
    """
    credits_needed = get_ai_credit_cost(action_type)
    
    # Get or create user credits
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
        credits = credits_doc
    
    # Check and refill if period ended
    if credits.get("monthly_credits_period_end"):
        period_end = datetime.fromisoformat(credits["monthly_credits_period_end"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        
        if now >= period_end:
            # Refill monthly credits
            old_monthly = credits.get("monthly_credits", 0)
            purchased = credits.get("purchased_credits", 0)
            
            new_period_end = now + relativedelta(months=1)
            
            await db.user_credits.update_one(
                {"tenant_id": tenant_id},
                {
                    "$set": {
                        "monthly_credits": FOUNDERS_EDITION_MONTHLY_CREDITS,
                        "monthly_credits_granted_at": now.isoformat(),
                        "monthly_credits_period_start": now.isoformat(),
                        "monthly_credits_period_end": new_period_end.isoformat(),
                        "updated_at": now.isoformat()
                    }
                }
            )
            
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
            
            # Record grant
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
            
            # Refresh credits
            credits = await db.user_credits.find_one({"tenant_id": tenant_id}, {"_id": 0})
    
    monthly = credits.get("monthly_credits", 0)
    purchased = credits.get("purchased_credits", 0)
    total = monthly + purchased
    
    # Check if enough credits
    if total < credits_needed:
        return (False, 0, f"Insufficient credits. Need {credits_needed}, have {total}.")
    
    # Deduct credits (monthly first, then purchased)
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
        description=f"AI action: {action_type}",
        metadata={
            "action_type": action_type,
            "monthly_used": monthly_used,
            "purchased_used": purchased_used,
            **(metadata or {})
        }
    )
    await db.credit_transactions.insert_one(transaction.model_dump())
    
    return (True, credits_needed, f"Used {credits_needed} credits for {action_type}")


async def get_credit_balance(db, tenant_id: str) -> dict:
    """Get the current credit balance for a tenant"""
    credits = await db.user_credits.find_one({"tenant_id": tenant_id}, {"_id": 0})
    
    if not credits:
        return {
            "monthly_credits": 0,
            "purchased_credits": 0,
            "total_credits": 0
        }
    
    return {
        "monthly_credits": credits.get("monthly_credits", 0),
        "purchased_credits": credits.get("purchased_credits", 0),
        "total_credits": credits.get("monthly_credits", 0) + credits.get("purchased_credits", 0)
    }


def get_all_credit_costs() -> dict:
    """Get all AI action credit costs"""
    return AI_CREDIT_COSTS
