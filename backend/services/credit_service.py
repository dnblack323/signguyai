"""AI Credit Integration Service."""

from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from services.founders_config import (
    get_ai_credit_cost, FOUNDERS_EDITION_MONTHLY_CREDITS, AI_CREDIT_COSTS
)
from models.credits import (
    CreditTransaction, CreditTransactionType, UserCredits
)


async def get_or_create_credit_record(db, tenant_id: str) -> dict:
    credits = await db.user_credits.find_one({"tenant_id": tenant_id}, {"_id": 0})

    if not credits:
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
        credits = new_credits.model_dump()
        await db.user_credits.insert_one(credits)

        grant_transaction = CreditTransaction(
            tenant_id=tenant_id,
            transaction_type=CreditTransactionType.MONTHLY_GRANT,
            amount=FOUNDERS_EDITION_MONTHLY_CREDITS,
            balance_after=FOUNDERS_EDITION_MONTHLY_CREDITS,
            monthly_balance_after=FOUNDERS_EDITION_MONTHLY_CREDITS,
            purchased_balance_after=0,
            description=f"Initial monthly credit grant: {FOUNDERS_EDITION_MONTHLY_CREDITS} credits"
        )
        await db.credit_transactions.insert_one(grant_transaction.model_dump())

    return credits


async def check_and_refill_monthly_credits(db, tenant_id: str) -> dict:
    credits = await get_or_create_credit_record(db, tenant_id)

    if not credits.get("monthly_credits_period_end"):
        return credits

    period_end = datetime.fromisoformat(credits["monthly_credits_period_end"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    if now >= period_end:
        old_monthly = credits.get("monthly_credits", 0)
        purchased = credits.get("purchased_credits", 0)
        new_period_end = now + relativedelta(months=1)

        await db.user_credits.update_one(
            {"tenant_id": tenant_id},
            {"$set": {
                "monthly_credits": FOUNDERS_EDITION_MONTHLY_CREDITS,
                "monthly_credits_granted_at": now.isoformat(),
                "monthly_credits_period_start": now.isoformat(),
                "monthly_credits_period_end": new_period_end.isoformat(),
                "updated_at": now.isoformat(),
            }}
        )

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
        credits = await db.user_credits.find_one({"tenant_id": tenant_id}, {"_id": 0})

    return credits


def build_credit_preview(credits: dict, action_type: str, credits_needed: int) -> Dict[str, Any]:
    monthly = credits.get("monthly_credits", 0)
    purchased = credits.get("purchased_credits", 0)
    total = monthly + purchased
    monthly_used = min(monthly, credits_needed)
    purchased_used = max(0, credits_needed - monthly_used)
    threshold = credits.get("low_credits_threshold", 10)

    days_until_refill = None
    if credits.get("monthly_credits_period_end"):
        period_end = datetime.fromisoformat(credits["monthly_credits_period_end"].replace("Z", "+00:00"))
        days_until_refill = max(0, (period_end - datetime.now(timezone.utc)).days)

    return {
        "action_type": action_type,
        "credit_cost": credits_needed,
        "monthly_credits": monthly,
        "purchased_credits": purchased,
        "total_credits": total,
        "monthly_credits_to_use": monthly_used,
        "purchased_credits_to_use": purchased_used,
        "will_use_purchased": purchased_used > 0,
        "sufficient_credits": total >= credits_needed,
        "is_low_credits": total <= threshold,
        "low_credits_threshold": threshold,
        "monthly_credits_period_end": credits.get("monthly_credits_period_end"),
        "days_until_refill": days_until_refill,
    }


async def preview_credit_usage(
    db,
    tenant_id: str,
    action_type: str,
    credits_required: Optional[int] = None,
) -> Dict[str, Any]:
    credits_needed = credits_required or get_ai_credit_cost(action_type)
    credits = await check_and_refill_monthly_credits(db, tenant_id)
    return build_credit_preview(credits, action_type, credits_needed)


async def log_ai_usage(
    db,
    *,
    tenant_id: str,
    user_id: str,
    action_type: str,
    module: str,
    feature_name: str,
    status: str,
    credits_charged: int,
    monthly_credits_used: int,
    purchased_credits_used: int,
    metadata: Optional[dict] = None,
) -> Dict[str, Any]:
    log_entry = {
        "id": f"aiuse_{datetime.now(timezone.utc).timestamp()}_{user_id[:6]}",
        "tenant_id": tenant_id,
        "user_id": user_id,
        "action_type": action_type,
        "module": module,
        "feature_name": feature_name,
        "credits_charged": credits_charged,
        "monthly_credits_used": monthly_credits_used,
        "purchased_credits_used": purchased_credits_used,
        "credit_source": "mixed" if monthly_credits_used and purchased_credits_used else "monthly" if monthly_credits_used else "purchased" if purchased_credits_used else "none",
        "status": status,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.ai_usage_logs.insert_one(log_entry)
    return log_entry


async def deduct_credits_after_success(
    db,
    *,
    tenant_id: str,
    user_id: str,
    action_type: str,
    module: str,
    feature_name: str,
    metadata: Optional[dict] = None,
    credits_required: Optional[int] = None,
) -> Dict[str, Any]:
    preview = await preview_credit_usage(db, tenant_id, action_type, credits_required)
    if not preview["sufficient_credits"]:
        raise ValueError(f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")

    new_monthly = preview["monthly_credits"] - preview["monthly_credits_to_use"]
    new_purchased = preview["purchased_credits"] - preview["purchased_credits_to_use"]
    new_total = new_monthly + new_purchased

    await db.user_credits.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "monthly_credits": new_monthly,
            "purchased_credits": new_purchased,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    transaction = CreditTransaction(
        tenant_id=tenant_id,
        transaction_type=CreditTransactionType.AI_USAGE,
        amount=-preview["credit_cost"],
        balance_after=new_total,
        monthly_balance_after=new_monthly,
        purchased_balance_after=new_purchased,
        description=f"AI action: {action_type}",
        metadata={
            "action_type": action_type,
            "module": module,
            "feature_name": feature_name,
            "monthly_used": preview["monthly_credits_to_use"],
            "purchased_used": preview["purchased_credits_to_use"],
            **(metadata or {}),
        }
    )
    await db.credit_transactions.insert_one(transaction.model_dump())

    usage_log = await log_ai_usage(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        action_type=action_type,
        module=module,
        feature_name=feature_name,
        status="success",
        credits_charged=preview["credit_cost"],
        monthly_credits_used=preview["monthly_credits_to_use"],
        purchased_credits_used=preview["purchased_credits_to_use"],
        metadata=metadata,
    )

    return {
        **preview,
        "remaining_monthly": new_monthly,
        "remaining_purchased": new_purchased,
        "remaining_total": new_total,
        "usage_log_id": usage_log["id"],
        "transaction_id": transaction.id,
    }


async def log_failed_ai_usage(
    db,
    *,
    tenant_id: str,
    user_id: str,
    action_type: str,
    module: str,
    feature_name: str,
    metadata: Optional[dict] = None,
) -> Dict[str, Any]:
    return await log_ai_usage(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        action_type=action_type,
        module=module,
        feature_name=feature_name,
        status="failed",
        credits_charged=0,
        monthly_credits_used=0,
        purchased_credits_used=0,
        metadata=metadata,
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
    preview = await preview_credit_usage(db, tenant_id, action_type)
    if not preview["sufficient_credits"]:
        return (False, 0, f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")

    result = await deduct_credits_after_success(
        db,
        tenant_id=tenant_id,
        user_id=metadata.get("user_id", tenant_id) if metadata else tenant_id,
        action_type=action_type,
        module=(metadata or {}).get("module", "legacy"),
        feature_name=(metadata or {}).get("feature_name", action_type),
        metadata=metadata,
    )
    return (True, result["credit_cost"], f"Used {result['credit_cost']} credits for {action_type}")


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
