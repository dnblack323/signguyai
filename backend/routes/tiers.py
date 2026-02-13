"""
Tier Management Routes

API endpoints for:
- Viewing available tiers
- Checking feature access
- Managing tenant subscriptions
- Viewing usage
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from models.tiers import (
    TierLevel, TierConfig, FeatureCheckResult, TenantUsage
)
from models import UserInDB
from services.tier_config import get_all_tiers, get_tier_config
from services.feature_gate import FeatureGate

# Import from server
from server import db, logger, get_current_active_user, has_permission
from models import Permission

router = APIRouter(prefix="/tiers", tags=["Subscription Tiers"])


# Create feature gate instance
def get_gate() -> FeatureGate:
    return FeatureGate(db)


# ============== PUBLIC TIER INFO ==============

@router.get("/plans")
async def get_subscription_plans():
    """Get all available subscription plans (public endpoint)"""
    tiers = get_all_tiers()
    
    return {
        "plans": [
            {
                "id": tier.level.value,
                "name": tier.display_name,
                "description": tier.description,
                "price_monthly": tier.price_monthly,
                "price_yearly": tier.price_yearly,
                "highlights": _get_tier_highlights(tier)
            }
            for tier in tiers
        ]
    }


def _get_tier_highlights(tier: TierConfig) -> list:
    """Get highlight features for a tier (for marketing display)"""
    if tier.level == TierLevel.STARTER:
        return [
            "1 Webstore",
            "25 AI generations/month",
            "1 Team member",
            "100MB Storage",
            "Basic Analytics",
            "Email Support"
        ]
    elif tier.level == TierLevel.PRO:
        return [
            "5 Webstores",
            "100 AI generations/month",
            "5 Team members",
            "1GB Storage",
            "Advanced Analytics",
            "Time Clock & Payroll",
            "Kanban & Calendar",
            "Priority Support"
        ]
    else:  # BUSINESS
        return [
            "Unlimited Webstores",
            "Unlimited AI generations",
            "Unlimited Team members",
            "5GB Storage",
            "Custom Reports",
            "B2B Features",
            "BNPL Payments",
            "SMS Notifications",
            "API Access",
            "Dedicated Support"
        ]


# ============== TENANT FEATURES ==============

@router.get("/my-plan")
async def get_my_plan(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current tenant's subscription plan and all feature access"""
    gate = get_gate()
    return await gate.get_tenant_features(current_user.tenant_id)


@router.get("/check/{category}/{feature}")
async def check_feature_access(
    category: str,
    feature: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Check if current tenant can access a specific feature"""
    gate = get_gate()
    result = await gate.check_feature(current_user.tenant_id, category, feature)
    return result.model_dump()


@router.post("/use/{category}/{feature}")
async def use_feature(
    category: str,
    feature: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Use a limited feature (increments usage counter).
    Call this when actually consuming a limited resource (e.g., AI generation).
    """
    gate = get_gate()
    result = await gate.check_feature(
        current_user.tenant_id, 
        category, 
        feature, 
        increment_usage=True
    )
    
    if not result.allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_limit_reached",
                "feature": f"{category}.{feature}",
                "message": result.message,
                "limit": result.limit,
                "current_usage": result.current_usage
            }
        )
    
    return {
        "success": True,
        "feature": f"{category}.{feature}",
        "remaining": result.remaining,
        "limit": result.limit
    }


# ============== USAGE TRACKING ==============

@router.get("/usage")
async def get_my_usage(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current tenant's usage for all limited features"""
    usage_records = await db.tenant_usage.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).to_list(100)
    
    return {
        "usage": [
            {
                "feature": record["usage_type"],
                "current": record["current_usage"],
                "limit": record["limit"],
                "remaining": max(0, record["limit"] - record["current_usage"]),
                "percentage": round(record["current_usage"] / record["limit"] * 100, 1) if record["limit"] > 0 else 0,
                "last_updated": record.get("last_updated")
            }
            for record in usage_records
        ]
    }


# ============== ADMIN: TIER MANAGEMENT ==============

@router.get("/admin/full-config/{tier}")
async def get_full_tier_config(
    tier: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get full configuration for a specific tier (admin only)"""
    if not has_permission(current_user, Permission.SETTINGS_VIEW):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        tier_level = TierLevel(tier)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
    
    config = get_tier_config(tier_level)
    return config.model_dump()


@router.put("/admin/tenant/{tenant_id}/tier")
async def set_tenant_tier(
    tenant_id: str,
    tier: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Change a tenant's subscription tier (admin only)"""
    if not has_permission(current_user, Permission.SETTINGS_EDIT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        tier_level = TierLevel(tier)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
    
    # Check tenant exists
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    gate = get_gate()
    await gate.set_tenant_tier(tenant_id, tier_level)
    
    logger.info(f"Tenant {tenant_id} tier changed to {tier} by {current_user.email}")
    
    return {
        "success": True,
        "tenant_id": tenant_id,
        "new_tier": tier,
        "message": f"Tenant upgraded to {tier_level.value}"
    }


@router.post("/admin/tenant/{tenant_id}/reset-usage")
async def reset_tenant_usage(
    tenant_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Reset monthly usage for a tenant (admin only)"""
    if not has_permission(current_user, Permission.SETTINGS_EDIT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    gate = get_gate()
    await gate.reset_monthly_usage(tenant_id)
    
    return {"success": True, "message": "Monthly usage reset"}


# ============== UPGRADE PROMPTS ==============

@router.get("/upgrade-prompt/{category}/{feature}")
async def get_upgrade_prompt(
    category: str,
    feature: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get upgrade prompt details for a blocked feature"""
    gate = get_gate()
    current_tier = await gate.get_tenant_tier(current_user.tenant_id)
    
    # Find which tier unlocks this feature
    unlock_tier = None
    for tier_level in [TierLevel.PRO, TierLevel.BUSINESS]:
        config = get_tier_config(tier_level)
        category_config = getattr(config.features, category, None)
        if category_config:
            feature_value = getattr(category_config, feature, None)
            if feature_value and feature_value.status.value != "off":
                unlock_tier = tier_level
                break
    
    if not unlock_tier:
        return {"error": "Feature not found in any tier"}
    
    unlock_config = get_tier_config(unlock_tier)
    
    return {
        "current_tier": current_tier.value,
        "unlock_tier": unlock_tier.value,
        "unlock_tier_name": unlock_config.display_name,
        "unlock_price_monthly": unlock_config.price_monthly,
        "unlock_price_yearly": unlock_config.price_yearly,
        "feature": f"{category}.{feature}",
        "message": f"Upgrade to {unlock_config.display_name} to unlock this feature",
        "cta_text": f"Upgrade to {unlock_config.display_name}"
    }
