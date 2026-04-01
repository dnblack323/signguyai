"""
Tier Management Routes

API endpoints for:
- Viewing available tiers/plans
- Checking feature access
- Managing tenant subscriptions
- Viewing usage

NOTE: Uses authoritative plan_configs.py system (not legacy tier_config.py)
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional

from models.product_tiers import (
    PlanType, PlanConfig, FeatureCheckResult, TenantUsage, TierLevel, ProductLine
)
from models import UserInDB, Permission, user_has_permission
from services.plan_configs import get_all_plans, get_plan_config, get_plans_by_product_line, legacy_tier_to_plan
from services.feature_gate import FeatureGate

router = APIRouter(prefix="/tiers", tags=["Subscription Tiers"])


# ============== DEPENDENCY INJECTION ==============
# These functions handle lazy imports to avoid circular dependencies

async def get_current_user_dep(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    """Get current user - wrapper to avoid circular import"""
    import jwt
    db = request.app.state.db
    secret_key = request.app.state.secret_key
    algorithm = request.app.state.algorithm
    
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
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


async def get_db(request: Request):
    """Get database connection"""
    return request.app.state.db


async def get_gate_dep(request: Request):
    """Get feature gate instance"""
    db = await get_db(request)
    return FeatureGate(db)


# ============== PUBLIC TIER INFO ==============

@router.get("/plans")
async def get_subscription_plans():
    """Get all available subscription plans (public endpoint)"""
    plans = get_all_plans()
    
    return {
        "plans": [
            {
                "id": plan.plan_type.value,
                "name": plan.display_name,
                "description": plan.description,
                "product_line": plan.product_line.value,
                "price_monthly": plan.pricing.monthly,
                "price_yearly": plan.pricing.annual,
                "founder_monthly": plan.pricing.founder_monthly,
                "founder_annual": plan.pricing.founder_annual,
                "founder_eligible": plan.founder_eligible,
                "highlights": _get_plan_highlights(plan)
            }
            for plan in plans
        ]
    }


def _get_plan_highlights(plan: PlanConfig) -> list:
    """Get highlight features for a plan (for marketing display)"""
    # OS Plans
    if plan.plan_type == PlanType.OS_STARTER:
        return [
            "2 Employees",
            "25 AI generations/month",
            "Basic Time Clock",
            "No online payments",
            "Email Support"
        ]
    elif plan.plan_type == PlanType.OS_PRO:
        return [
            "10 Employees",
            "3 Webstores",
            "100 AI generations/month",
            "Time Clock & Payroll",
            "Customer Portal",
            "Online Invoice Payments",
            "Priority Support"
        ]
    elif plan.plan_type == PlanType.OS_BUSINESS:
        return [
            "Unlimited Employees",
            "Unlimited Webstores",
            "Unlimited AI generations",
            "Full Financial Suite",
            "Advanced Analytics",
            "Business Data AI Assistant",
            "Dedicated Support"
        ]
    # Webstore Plans
    elif plan.plan_type == PlanType.WS_LAUNCH:
        return [
            "1 Webstore",
            "B2B & Fundraiser stores",
            "Basic Analytics",
            "3% Platform Fee"
        ]
    elif plan.plan_type == PlanType.WS_GROWTH:
        return [
            "5 Webstores",
            "All store types",
            "Advanced Branding",
            "Price Overrides",
            "2.5% Platform Fee"
        ]
    elif plan.plan_type == PlanType.WS_SCALE:
        return [
            "Unlimited Webstores",
            "Bulk Order Tools",
            "Advanced Analytics",
            "Payout Tracking",
            "2% Platform Fee"
        ]
    # AI Studio Plans
    elif plan.plan_type == PlanType.AI_BASIC:
        return [
            "Text Generation",
            "25 generations/month",
            "10 AI queries/month"
        ]
    elif plan.plan_type == PlanType.AI_PRO:
        return [
            "Text + Image Generation",
            "100 generations/month",
            "50 AI queries/month"
        ]
    elif plan.plan_type == PlanType.AI_MAX:
        return [
            "Unlimited Generations",
            "Branding Kit Generator",
            "Campaign Builder",
            "Content Calendar"
        ]
    return []


# Legacy alias for backwards compatibility
def _get_tier_highlights(tier: PlanConfig) -> list:
    """DEPRECATED: Use _get_plan_highlights()"""
    return _get_plan_highlights(tier)


# ============== TENANT FEATURES ==============

@router.get("/my-plan")
async def get_my_plan(
    request: Request,
    current_user: UserInDB = Depends(get_current_user_dep),
):
    """Get current tenant's subscription plan and all feature access"""
    gate = await get_gate_dep(request)
    return await gate.get_tenant_features(current_user.tenant_id)


@router.get("/check/{category}/{feature}")
async def check_feature_access(
    request: Request,
    category: str,
    feature: str,
    current_user: UserInDB = Depends(get_current_user_dep),
):
    """Check if current tenant can access a specific feature"""
    gate = await get_gate_dep(request)
    result = await gate.check_feature(current_user.tenant_id, category, feature)
    return result.model_dump()


@router.post("/use/{category}/{feature}")
async def use_feature(
    request: Request,
    category: str,
    feature: str,
    current_user: UserInDB = Depends(get_current_user_dep),
):
    """
    Use a limited feature (increments usage counter).
    Call this when actually consuming a limited resource (e.g., AI generation).
    """
    gate = await get_gate_dep(request)
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
async def get_my_usage(
    request: Request,
    current_user: UserInDB = Depends(get_current_user_dep),
):
    """Get current tenant's usage for all limited features"""
    db = await get_db(request)
    
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

@router.get("/admin/full-config/{plan}")
async def get_full_plan_config(
    plan: str,
    current_user: UserInDB = Depends(get_current_user_dep)
):
    """Get full configuration for a specific plan (admin only)"""
    if not user_has_permission(current_user.role, Permission.SETTINGS_VIEW):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Try new plan type first, then legacy tier
    try:
        plan_type = PlanType(plan)
    except ValueError:
        # Try legacy tier mapping
        plan_type = legacy_tier_to_plan(plan)
    
    config = get_plan_config(plan_type)
    return config.model_dump()


# Legacy alias
@router.get("/admin/full-config/tier/{tier}")
async def get_full_tier_config(
    tier: str,
    current_user: UserInDB = Depends(get_current_user_dep)
):
    """DEPRECATED: Use /admin/full-config/{plan} instead"""
    return await get_full_plan_config(tier, current_user)


@router.put("/admin/tenant/{tenant_id}/plan")
async def set_tenant_plan(
    tenant_id: str,
    plan: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user_dep)
):
    """Change a tenant's subscription plan (admin only)"""
    if not user_has_permission(current_user.role, Permission.SETTINGS_EDIT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Try new plan type first, then legacy tier
    try:
        plan_type = PlanType(plan)
    except ValueError:
        plan_type = legacy_tier_to_plan(plan)
    
    db = await get_db(request)
    
    # Check tenant exists
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    gate = await get_gate_dep(request)
    await gate.set_tenant_plan(tenant_id, plan_type)
    
    return {
        "success": True,
        "tenant_id": tenant_id,
        "new_plan": plan_type.value,
        "message": f"Tenant upgraded to {plan_type.value}"
    }


# Legacy alias
@router.put("/admin/tenant/{tenant_id}/tier")
async def set_tenant_tier(
    tenant_id: str,
    tier: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user_dep)
):
    """DEPRECATED: Use /admin/tenant/{tenant_id}/plan instead"""
    return await set_tenant_plan(tenant_id, tier, request, current_user)


@router.post("/admin/tenant/{tenant_id}/reset-usage")
async def reset_tenant_usage(
    tenant_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user_dep)
):
    """Reset monthly usage for a tenant (admin only)"""
    if not user_has_permission(current_user.role, Permission.SETTINGS_EDIT):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    gate = await get_gate_dep(request)
    await gate.reset_monthly_usage(tenant_id)
    
    return {"success": True, "message": "Monthly usage reset"}


# ============== UPGRADE PROMPTS ==============

@router.get("/upgrade-prompt/{category}/{feature}")
async def get_upgrade_prompt(
    category: str,
    feature: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user_dep)
):
    """Get upgrade prompt details for a blocked feature"""
    gate = await get_gate_dep(request)
    current_plan = await gate.get_tenant_plan(current_user.tenant_id)
    
    # Find which plan unlocks this feature (check higher tiers in same product line)
    unlock_plan = None
    
    # Determine upgrade path based on current product line
    if current_plan.value.startswith('os_'):
        upgrade_path = [PlanType.OS_PRO, PlanType.OS_BUSINESS]
    elif current_plan.value.startswith('ws_'):
        upgrade_path = [PlanType.WS_GROWTH, PlanType.WS_SCALE]
    elif current_plan.value.startswith('ai_'):
        upgrade_path = [PlanType.AI_PRO, PlanType.AI_MAX]
    else:
        upgrade_path = [PlanType.OS_PRO, PlanType.OS_BUSINESS]
    
    for plan_type in upgrade_path:
        config = get_plan_config(plan_type)
        category_config = getattr(config.features, category, None)
        if category_config:
            feature_value = getattr(category_config, feature, None)
            if feature_value and feature_value.status.value != "off":
                unlock_plan = plan_type
                break
    
    if not unlock_plan:
        return {"error": "Feature not found in any plan"}
    
    unlock_config = get_plan_config(unlock_plan)
    
    return {
        "current_plan": current_plan.value,
        "unlock_plan": unlock_plan.value,
        "unlock_plan_name": unlock_config.display_name,
        "unlock_price_monthly": unlock_config.pricing.monthly,
        "unlock_price_yearly": unlock_config.pricing.annual,
        "feature": f"{category}.{feature}",
        "message": f"Upgrade to {unlock_config.display_name} to unlock this feature",
        "cta_text": f"Upgrade to {unlock_config.display_name}",
        # Legacy fields
        "current_tier": current_plan.value,
        "unlock_tier": unlock_plan.value,
        "unlock_tier_name": unlock_config.display_name
    }
