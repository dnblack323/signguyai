"""
Feature Gating Service

Provides utilities to check feature access and track usage for tenants.
Uses the authoritative plan_configs.py and multi_product_gate.py system.
"""

from typing import Optional, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException, Depends

from models.product_tiers import (
    PlanType, FeatureStatus, FeatureValue, FeatureCheckResult,
    TenantUsage, TierLevel
)
from services.plan_configs import get_plan_config, legacy_tier_to_plan, PLAN_CONFIGS


class FeatureGate:
    """Service for checking feature access and tracking usage"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_tenant_plan(self, tenant_id: str) -> PlanType:
        """Get the current plan for a tenant"""
        tenant = await self.db.tenants.find_one({"id": tenant_id}, {"_id": 0, "plan": 1})
        if not tenant:
            return PlanType.OS_STARTER
        
        plan = tenant.get("plan", "starter")
        # Handle both new plan types and legacy tier names
        try:
            return PlanType(plan)
        except ValueError:
            # Legacy tier mapping
            return legacy_tier_to_plan(plan)
    
    # Legacy alias for backwards compatibility
    async def get_tenant_tier(self, tenant_id: str) -> TierLevel:
        """DEPRECATED: Use get_tenant_plan() instead. Maps to legacy TierLevel."""
        plan = await self.get_tenant_plan(tenant_id)
        # Map plan to legacy tier
        tier_map = {
            PlanType.OS_STARTER: TierLevel.STARTER,
            PlanType.OS_PRO: TierLevel.PRO,
            PlanType.OS_BUSINESS: TierLevel.BUSINESS,
            PlanType.WS_LAUNCH: TierLevel.STARTER,
            PlanType.WS_GROWTH: TierLevel.PRO,
            PlanType.WS_SCALE: TierLevel.BUSINESS,
            PlanType.AI_BASIC: TierLevel.STARTER,
            PlanType.AI_PRO: TierLevel.PRO,
            PlanType.AI_MAX: TierLevel.BUSINESS,
        }
        return tier_map.get(plan, TierLevel.STARTER)
    
    async def get_feature_value(
        self,
        tenant_id: str,
        category: str,
        feature: str
    ) -> FeatureValue:
        """Get the feature value for a tenant's plan"""
        plan = await self.get_tenant_plan(tenant_id)
        config = get_plan_config(plan)
        
        # Navigate to the feature
        category_config = getattr(config.features, category, None)
        if not category_config:
            return FeatureValue(status=FeatureStatus.OFF)
        
        feature_value = getattr(category_config, feature, None)
        if not feature_value:
            return FeatureValue(status=FeatureStatus.OFF)
        
        return feature_value
    
    async def check_feature(
        self,
        tenant_id: str,
        category: str,
        feature: str,
        increment_usage: bool = False
    ) -> FeatureCheckResult:
        """
        Check if a tenant can access a feature.
        Returns detailed result including usage info for LIMITED features.
        """
        feature_value = await self.get_feature_value(tenant_id, category, feature)
        
        # OFF = Not allowed
        if feature_value.status == FeatureStatus.OFF:
            return FeatureCheckResult(
                allowed=False,
                feature=f"{category}.{feature}",
                status=feature_value.status,
                message="This feature is not available on your current plan. Please upgrade."
            )
        
        # ON = Allowed (unlimited)
        if feature_value.status == FeatureStatus.ON:
            return FeatureCheckResult(
                allowed=True,
                feature=f"{category}.{feature}",
                status=feature_value.status
            )
        
        # LIMITED = Check usage
        if feature_value.status == FeatureStatus.LIMITED:
            usage = await self._get_or_create_usage(tenant_id, category, feature, feature_value.limit)
            
            # Check if within limit
            if usage.current_usage >= usage.limit:
                return FeatureCheckResult(
                    allowed=False,
                    feature=f"{category}.{feature}",
                    status=feature_value.status,
                    limit=usage.limit,
                    current_usage=usage.current_usage,
                    remaining=0,
                    message=f"You've reached the limit of {usage.limit} for this feature. Please upgrade for more."
                )
            
            # Increment if requested
            if increment_usage:
                await self._increment_usage(tenant_id, category, feature)
                usage.current_usage += 1
            
            return FeatureCheckResult(
                allowed=True,
                feature=f"{category}.{feature}",
                status=feature_value.status,
                limit=usage.limit,
                current_usage=usage.current_usage,
                remaining=usage.limit - usage.current_usage
            )
        
        return FeatureCheckResult(
            allowed=False,
            feature=f"{category}.{feature}",
            status=FeatureStatus.OFF,
            message="Unknown feature status"
        )
    
    async def require_feature(
        self,
        tenant_id: str,
        category: str,
        feature: str,
        increment_usage: bool = False
    ) -> FeatureCheckResult:
        """
        Check feature access and raise HTTPException if not allowed.
        Use this in route handlers.
        """
        result = await self.check_feature(tenant_id, category, feature, increment_usage)
        
        if not result.allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "feature_not_available",
                    "feature": result.feature,
                    "status": result.status.value,
                    "message": result.message,
                    "limit": result.limit,
                    "current_usage": result.current_usage
                }
            )
        
        return result
    
    async def get_tenant_features(self, tenant_id: str) -> dict:
        """Get all features and their status for a tenant"""
        plan = await self.get_tenant_plan(tenant_id)
        config = get_plan_config(plan)
        
        # Get usage data for limited features
        usage_data = await self._get_all_usage(tenant_id)
        
        # Build response
        features_dict = config.features.model_dump()
        
        # Add usage info for limited features
        for category_name, category_features in features_dict.items():
            for feature_name, feature_data in category_features.items():
                if feature_data.get("status") == "limited":
                    usage_key = f"{category_name}.{feature_name}"
                    if usage_key in usage_data:
                        feature_data["current_usage"] = usage_data[usage_key]["current_usage"]
                        feature_data["remaining"] = max(0, feature_data.get("limit", 0) - usage_data[usage_key]["current_usage"])
        
        return {
            "plan": plan.value,
            "plan_display_name": config.display_name,
            "product_line": config.product_line.value,
            # Legacy fields for backwards compat
            "tier": plan.value,
            "tier_display_name": config.display_name,
            "features": features_dict
        }
    
    async def _get_or_create_usage(
        self,
        tenant_id: str,
        category: str,
        feature: str,
        limit: int
    ) -> TenantUsage:
        """Get or create usage tracking for a feature"""
        usage_key = f"{category}.{feature}"
        
        usage = await self.db.tenant_usage.find_one(
            {"tenant_id": tenant_id, "usage_type": usage_key},
            {"_id": 0}
        )
        
        if usage:
            return TenantUsage(**usage)
        
        # Create new usage record
        new_usage = TenantUsage(
            tenant_id=tenant_id,
            usage_type=usage_key,
            current_usage=0,
            limit=limit
        )
        await self.db.tenant_usage.insert_one(new_usage.model_dump())
        
        return new_usage
    
    async def _increment_usage(self, tenant_id: str, category: str, feature: str):
        """Increment usage counter for a feature"""
        usage_key = f"{category}.{feature}"
        
        await self.db.tenant_usage.update_one(
            {"tenant_id": tenant_id, "usage_type": usage_key},
            {
                "$inc": {"current_usage": 1},
                "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
            }
        )
    
    async def _get_all_usage(self, tenant_id: str) -> dict:
        """Get all usage data for a tenant"""
        usage_records = await self.db.tenant_usage.find(
            {"tenant_id": tenant_id},
            {"_id": 0}
        ).to_list(100)
        
        return {
            record["usage_type"]: record
            for record in usage_records
        }
    
    async def reset_monthly_usage(self, tenant_id: str):
        """Reset monthly usage counters (call this on billing cycle)"""
        monthly_features = [
            "ai_tools.monthly_generations",
            "ai_assistant.natural_language"
        ]
        
        for feature in monthly_features:
            await self.db.tenant_usage.update_one(
                {"tenant_id": tenant_id, "usage_type": feature},
                {
                    "$set": {
                        "current_usage": 0,
                        "period_start": datetime.now(timezone.utc).isoformat(),
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
    
    async def set_tenant_tier(self, tenant_id: str, tier: TierLevel):
        """Update a tenant's subscription tier"""
        await self.db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"plan": tier.value}}
        )
        
        # Update usage limits based on new tier
        config = get_tier_config(tier)
        await self._update_usage_limits(tenant_id, config)
    
    async def _update_usage_limits(self, tenant_id: str, config):
        """Update usage limits when tier changes"""
        # Map of features to their new limits
        limit_updates = {
            "ai_tools.monthly_generations": config.features.ai_tools.monthly_generations.limit,
            "ai_assistant.natural_language": config.features.ai_assistant.natural_language.limit,
            "team.team_members": config.features.team.team_members.limit,
            "webstores.num_stores": config.features.webstores.num_stores.limit,
            "webstores.product_images": config.features.webstores.product_images.limit,
            "data.storage_mb": config.features.data.storage_mb.limit,
            "data.retention_years": config.features.data.retention_years.limit,
        }
        
        for usage_type, new_limit in limit_updates.items():
            if new_limit is not None:
                await self.db.tenant_usage.update_one(
                    {"tenant_id": tenant_id, "usage_type": usage_type},
                    {"$set": {"limit": new_limit}},
                    upsert=True
                )


# Helper function to create feature gate instance
def get_feature_gate(db) -> FeatureGate:
    """Factory function to create FeatureGate with database"""
    return FeatureGate(db)
