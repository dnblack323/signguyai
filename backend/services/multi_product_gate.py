"""
Multi-Product Feature Gating Service

Provides utilities to check feature access and track usage across all 3 product lines.
Handles founder pricing, processing fees, and UI visibility controls.
"""

from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException

from models.product_tiers import (
    ProductLine, PlanType, FeatureStatus, FeatureValue, FeatureCheckResult,
    TenantUsage, ProcessingFees, FOUNDER_SPOTS_TOTAL
)
from services.plan_configs import (
    get_plan_config, get_all_plans, legacy_tier_to_plan, PLAN_CONFIGS
)


class MultiProductFeatureGate:
    """Service for checking feature access across all product lines"""
    
    def __init__(self, db):
        self.db = db
    
    # ============== TENANT INFO ==============
    
    async def get_tenant_plan(self, tenant_id: str) -> Tuple[PlanType, bool]:
        """
        Get the current plan and founder status for a tenant.
        Returns (plan_type, is_founder)
        """
        tenant = await self.db.tenants.find_one(
            {"id": tenant_id}, 
            {"_id": 0, "plan": 1, "product_line": 1, "is_founder": 1}
        )
        
        if not tenant:
            return PlanType.OS_STARTER, False
        
        plan_str = tenant.get("plan", "os_starter")
        is_founder = tenant.get("is_founder", False)
        
        # Handle legacy tier names
        try:
            plan_type = PlanType(plan_str)
        except ValueError:
            # Legacy mapping
            plan_type = legacy_tier_to_plan(plan_str)
        
        return plan_type, is_founder
    
    async def get_tenant_product_line(self, tenant_id: str) -> ProductLine:
        """Get the product line for a tenant"""
        plan_type, _ = await self.get_tenant_plan(tenant_id)
        config = get_plan_config(plan_type)
        return config.product_line
    
    # ============== FEATURE CHECKS ==============
    
    async def get_feature_value(
        self,
        tenant_id: str,
        category: str,
        feature: str
    ) -> FeatureValue:
        """Get the feature value for a tenant's current plan"""
        plan_type, _ = await self.get_tenant_plan(tenant_id)
        config = get_plan_config(plan_type)
        
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
            usage = await self._get_or_create_usage(
                tenant_id, category, feature, feature_value.limit or 0
            )
            
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
    
    # ============== UI VISIBILITY ==============
    
    async def get_ui_visibility(self, tenant_id: str) -> Dict[str, bool]:
        """Get UI visibility flags for a tenant's plan"""
        plan_type, _ = await self.get_tenant_plan(tenant_id)
        config = get_plan_config(plan_type)
        
        return {
            "show_jobs_ui": config.show_jobs_ui,
            "show_payroll_ui": config.show_payroll_ui,
            "show_time_clock_ui": config.show_time_clock_ui,
            "show_financials_ui": config.show_financials_ui,
            "show_ai_assistant_ui": config.show_ai_assistant_ui,
            "product_line": config.product_line.value,
            "plan_type": config.plan_type.value,
            "display_name": config.display_name,
        }
    
    # ============== PROCESSING FEES ==============
    
    async def get_processing_fees(self, tenant_id: str) -> ProcessingFees:
        """Get processing fee configuration for a tenant"""
        plan_type, is_founder = await self.get_tenant_plan(tenant_id)
        config = get_plan_config(plan_type)
        
        fees = config.processing_fees
        
        # Apply founder discount on annual plans
        # Founder annual Business: 0.5% invoice, 1.5% webstore
        if is_founder and plan_type == PlanType.OS_BUSINESS:
            # Check if on annual billing
            subscription = await self.db.subscriptions.find_one(
                {"tenant_id": tenant_id},
                {"_id": 0, "billing_interval": 1}
            )
            if subscription and subscription.get("billing_interval") == "annual":
                return ProcessingFees(
                    invoice_fee_percent=0.5,
                    webstore_fee_percent=1.5,
                    stripe_connect_enabled=fees.stripe_connect_enabled,
                    online_payments_enabled=fees.online_payments_enabled,
                )
        
        return fees
    
    def calculate_platform_fee(
        self,
        amount: float,
        fee_percent: float
    ) -> float:
        """Calculate platform fee for a transaction"""
        return round(amount * (fee_percent / 100), 2)
    
    # ============== FOUNDER MANAGEMENT ==============
    
    async def get_founder_count(self) -> int:
        """Get current count of founder accounts"""
        count = await self.db.tenants.count_documents({"is_founder": True})
        return count
    
    async def is_founder_available(self) -> bool:
        """Check if founder spots are still available"""
        count = await self.get_founder_count()
        return count < FOUNDER_SPOTS_TOTAL
    
    async def get_founder_spots_remaining(self) -> int:
        """Get number of founder spots remaining"""
        count = await self.get_founder_count()
        return max(0, FOUNDER_SPOTS_TOTAL - count)
    
    async def assign_founder_number(self, tenant_id: str) -> Optional[int]:
        """
        Assign founder number to a tenant.
        Returns the founder number if successful, None if no spots left.
        """
        if not await self.is_founder_available():
            return None
        
        # Get next founder number
        current_count = await self.get_founder_count()
        founder_number = current_count + 1
        
        # Update tenant
        await self.db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {
                "is_founder": True,
                "founder_number": founder_number,
                "founder_locked_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return founder_number
    
    # ============== PLAN INFO ==============
    
    async def get_tenant_plan_info(self, tenant_id: str) -> Dict[str, Any]:
        """Get complete plan information for a tenant"""
        plan_type, is_founder = await self.get_tenant_plan(tenant_id)
        config = get_plan_config(plan_type)
        fees = await self.get_processing_fees(tenant_id)
        ui_visibility = await self.get_ui_visibility(tenant_id)
        
        # Get subscription details
        subscription = await self.db.subscriptions.find_one(
            {"tenant_id": tenant_id},
            {"_id": 0}
        )
        
        # Get usage data
        usage_data = await self._get_all_usage(tenant_id)
        
        return {
            "plan_type": config.plan_type.value,
            "product_line": config.product_line.value,
            "display_name": config.display_name,
            "description": config.description,
            "is_founder": is_founder,
            "founder_eligible": config.founder_eligible,
            "pricing": {
                "monthly": config.pricing.monthly,
                "annual": config.pricing.annual,
                "founder_monthly": config.pricing.founder_monthly,
                "founder_annual": config.pricing.founder_annual,
                "current_price": (
                    config.pricing.founder_monthly if is_founder 
                    else config.pricing.monthly
                ),
            },
            "processing_fees": {
                "invoice_fee_percent": fees.invoice_fee_percent,
                "webstore_fee_percent": fees.webstore_fee_percent,
                "stripe_connect_enabled": fees.stripe_connect_enabled,
                "online_payments_enabled": fees.online_payments_enabled,
            },
            "ui_visibility": ui_visibility,
            "subscription": subscription,
            "usage": usage_data,
        }
    
    async def get_all_features(self, tenant_id: str) -> Dict[str, Any]:
        """Get all features and their status for a tenant"""
        plan_type, _ = await self.get_tenant_plan(tenant_id)
        config = get_plan_config(plan_type)
        
        # Get usage data for limited features
        usage_data = await self._get_all_usage(tenant_id)
        
        # Build response
        features_dict = {}
        for category_name in ["core", "customer_portal", "webstores", "ai_tools", "ai_assistant", "crm"]:
            category = getattr(config.features, category_name, None)
            if category:
                features_dict[category_name] = {}
                for field_name in category.model_fields:
                    feature_value = getattr(category, field_name)
                    feature_data = feature_value.model_dump()
                    
                    # Add usage info for limited features
                    if feature_value.status == FeatureStatus.LIMITED:
                        usage_key = f"{category_name}.{field_name}"
                        if usage_key in usage_data:
                            feature_data["current_usage"] = usage_data[usage_key]["current_usage"]
                            feature_data["remaining"] = max(
                                0, 
                                (feature_value.limit or 0) - usage_data[usage_key]["current_usage"]
                            )
                    
                    features_dict[category_name][field_name] = feature_data
        
        return {
            "plan_type": config.plan_type.value,
            "product_line": config.product_line.value,
            "display_name": config.display_name,
            "features": features_dict
        }
    
    # ============== USAGE TRACKING ==============
    
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
        import uuid
        new_usage = TenantUsage(
            id=str(uuid.uuid4()),
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
    
    async def _get_all_usage(self, tenant_id: str) -> Dict[str, Any]:
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
        """Reset monthly usage counters"""
        monthly_features = [
            "ai_tools.monthly_generations",
            "ai_assistant.monthly_queries",
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
    
    # ============== PLAN CHANGES ==============
    
    async def set_tenant_plan(
        self,
        tenant_id: str,
        plan_type: PlanType,
        is_founder: bool = False
    ):
        """Update a tenant's subscription plan"""
        config = get_plan_config(plan_type)
        
        update_data = {
            "plan": plan_type.value,
            "product_line": config.product_line.value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Handle founder status
        if is_founder and config.founder_eligible:
            if not await self.db.tenants.find_one({"id": tenant_id, "is_founder": True}):
                founder_number = await self.assign_founder_number(tenant_id)
                if founder_number:
                    update_data["is_founder"] = True
                    update_data["founder_number"] = founder_number
        
        await self.db.tenants.update_one(
            {"id": tenant_id},
            {"$set": update_data}
        )
        
        # Update usage limits based on new plan
        await self._update_usage_limits(tenant_id, config)
    
    async def _update_usage_limits(self, tenant_id: str, config):
        """Update usage limits when plan changes"""
        limit_updates = {}
        
        # AI generations limit
        ai_gen = config.features.ai_tools.monthly_generations
        if ai_gen.status == FeatureStatus.LIMITED and ai_gen.limit:
            limit_updates["ai_tools.monthly_generations"] = ai_gen.limit
        
        # AI queries limit
        ai_queries = config.features.ai_assistant.monthly_queries
        if ai_queries.status == FeatureStatus.LIMITED and ai_queries.limit:
            limit_updates["ai_assistant.monthly_queries"] = ai_queries.limit
        
        # Employees limit
        employees = config.features.core.employees
        if employees.status == FeatureStatus.LIMITED and employees.limit:
            limit_updates["core.employees"] = employees.limit
        
        # Webstores limit
        num_stores = config.features.webstores.num_stores
        if num_stores.status == FeatureStatus.LIMITED and num_stores.limit:
            limit_updates["webstores.num_stores"] = num_stores.limit
        
        # Document storage limit
        storage = config.features.customer_portal.document_storage_mb
        if storage.status == FeatureStatus.LIMITED and storage.limit:
            limit_updates["customer_portal.document_storage_mb"] = storage.limit
        
        for usage_type, new_limit in limit_updates.items():
            await self.db.tenant_usage.update_one(
                {"tenant_id": tenant_id, "usage_type": usage_type},
                {"$set": {"limit": new_limit}},
                upsert=True
            )


# Factory function
def get_multi_product_feature_gate(db) -> MultiProductFeatureGate:
    """Create MultiProductFeatureGate instance with database"""
    return MultiProductFeatureGate(db)
