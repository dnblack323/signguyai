"""
Plan Management API Routes

Endpoints for managing plans, checking features, and getting pricing information
across all 3 product lines.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from server import db, get_current_active_user
from models.auth import UserInDB
from models.product_tiers import (
    ProductLine, PlanType, FOUNDER_SPOTS_TOTAL
)
from services.plan_configs import (
    get_plan_config, get_all_plans, get_plans_by_product_line,
    get_founder_eligible_plans
)
from services.multi_product_gate import get_multi_product_feature_gate


router = APIRouter(prefix="/plans", tags=["Plans"])


# ============== RESPONSE MODELS ==============

class PlanSummary(BaseModel):
    """Summary of a plan for display"""
    plan_type: str
    product_line: str
    display_name: str
    description: str
    price_monthly: float
    price_annual: float
    founder_price_monthly: Optional[float]
    founder_price_annual: Optional[float]
    founder_eligible: bool


class ProductLinePlans(BaseModel):
    """Plans grouped by product line"""
    product_line: str
    display_name: str
    plans: List[PlanSummary]


class FounderStatus(BaseModel):
    """Founder availability status"""
    founder_spots_total: int
    founder_spots_used: int
    founder_spots_remaining: int
    founder_available: bool


class ProcessingFeeInfo(BaseModel):
    """Processing fee information"""
    invoice_fee_percent: float
    webstore_fee_percent: float
    stripe_connect_enabled: bool
    online_payments_enabled: bool
    fee_explanation: str


# ============== PUBLIC ENDPOINTS ==============

@router.get("/all", response_model=List[ProductLinePlans])
async def get_all_plans_grouped():
    """Get all plans grouped by product line"""
    result = []
    
    product_line_names = {
        ProductLine.OS: "SignGuy AI OS",
        ProductLine.WEBSTORES: "SignGuy Webstores",
        ProductLine.AI_STUDIO: "SignGuy AI Studio",
    }
    
    for product_line in ProductLine:
        plans = get_plans_by_product_line(product_line)
        plan_summaries = [
            PlanSummary(
                plan_type=p.plan_type.value,
                product_line=p.product_line.value,
                display_name=p.display_name,
                description=p.description,
                price_monthly=p.pricing.monthly,
                price_annual=p.pricing.annual,
                founder_price_monthly=p.pricing.founder_monthly,
                founder_price_annual=p.pricing.founder_annual,
                founder_eligible=p.founder_eligible,
            )
            for p in plans
        ]
        
        result.append(ProductLinePlans(
            product_line=product_line.value,
            display_name=product_line_names[product_line],
            plans=plan_summaries,
        ))
    
    return result


@router.get("/os", response_model=List[PlanSummary])
async def get_os_plans():
    """Get SignGuy AI OS plans (Shop Management)"""
    plans = get_plans_by_product_line(ProductLine.OS)
    return [
        PlanSummary(
            plan_type=p.plan_type.value,
            product_line=p.product_line.value,
            display_name=p.display_name,
            description=p.description,
            price_monthly=p.pricing.monthly,
            price_annual=p.pricing.annual,
            founder_price_monthly=p.pricing.founder_monthly,
            founder_price_annual=p.pricing.founder_annual,
            founder_eligible=p.founder_eligible,
        )
        for p in plans
    ]


@router.get("/webstores", response_model=List[PlanSummary])
async def get_webstore_plans():
    """Get SignGuy Webstores plans (Commerce-Only)"""
    plans = get_plans_by_product_line(ProductLine.WEBSTORES)
    return [
        PlanSummary(
            plan_type=p.plan_type.value,
            product_line=p.product_line.value,
            display_name=p.display_name,
            description=p.description,
            price_monthly=p.pricing.monthly,
            price_annual=p.pricing.annual,
            founder_price_monthly=p.pricing.founder_monthly,
            founder_price_annual=p.pricing.founder_annual,
            founder_eligible=p.founder_eligible,
        )
        for p in plans
    ]


@router.get("/ai-studio", response_model=List[PlanSummary])
async def get_ai_studio_plans():
    """Get SignGuy AI Studio plans (AI-Only)"""
    plans = get_plans_by_product_line(ProductLine.AI_STUDIO)
    return [
        PlanSummary(
            plan_type=p.plan_type.value,
            product_line=p.product_line.value,
            display_name=p.display_name,
            description=p.description,
            price_monthly=p.pricing.monthly,
            price_annual=p.pricing.annual,
            founder_price_monthly=p.pricing.founder_monthly,
            founder_price_annual=p.pricing.founder_annual,
            founder_eligible=p.founder_eligible,
        )
        for p in plans
    ]


@router.get("/founder-status", response_model=FounderStatus)
async def get_founder_status():
    """Get founder spot availability"""
    gate = get_multi_product_feature_gate(db)
    count = await gate.get_founder_count()
    remaining = await gate.get_founder_spots_remaining()
    
    return FounderStatus(
        founder_spots_total=FOUNDER_SPOTS_TOTAL,
        founder_spots_used=count,
        founder_spots_remaining=remaining,
        founder_available=remaining > 0,
    )


@router.get("/{plan_type}/details")
async def get_plan_details(plan_type: str):
    """Get detailed information for a specific plan"""
    try:
        plan = PlanType(plan_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    config = get_plan_config(plan)
    
    return {
        "plan_type": config.plan_type.value,
        "product_line": config.product_line.value,
        "display_name": config.display_name,
        "description": config.description,
        "pricing": {
            "monthly": config.pricing.monthly,
            "annual": config.pricing.annual,
            "founder_monthly": config.pricing.founder_monthly,
            "founder_annual": config.pricing.founder_annual,
        },
        "processing_fees": {
            "invoice_fee_percent": config.processing_fees.invoice_fee_percent,
            "webstore_fee_percent": config.processing_fees.webstore_fee_percent,
            "stripe_connect_enabled": config.processing_fees.stripe_connect_enabled,
            "online_payments_enabled": config.processing_fees.online_payments_enabled,
        },
        "founder_eligible": config.founder_eligible,
        "ui_visibility": {
            "show_jobs_ui": config.show_jobs_ui,
            "show_payroll_ui": config.show_payroll_ui,
            "show_time_clock_ui": config.show_time_clock_ui,
            "show_financials_ui": config.show_financials_ui,
            "show_ai_assistant_ui": config.show_ai_assistant_ui,
        },
        "features": config.features.model_dump(),
    }


@router.get("/processing-fees/explanation")
async def get_processing_fee_explanation():
    """Get explanation of processing fees for website copy"""
    return {
        "explanation": """Processing fees support:
• Secure checkout hosting
• PCI compliance handling
• Fraud monitoring
• Payment API maintenance
• Webhook processing
• Automated reconciliation
• Commission calculation engine
• Store hosting infrastructure
• Ongoing security updates

Stripe base processing fees apply separately.
All platform fees are displayed transparently.""",
        "note": "Stripe base fees (typically 2.9% + $0.30) apply in addition to platform fees."
    }


# ============== AUTHENTICATED ENDPOINTS ==============

@router.get("/my-plan")
async def get_my_plan(current_user: UserInDB = Depends(get_current_active_user)):
    """Get the current user's plan information"""
    gate = get_multi_product_feature_gate(db)
    return await gate.get_tenant_plan_info(current_user.tenant_id)


@router.get("/my-features")
async def get_my_features(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all features and their status for the current user"""
    gate = get_multi_product_feature_gate(db)
    return await gate.get_all_features(current_user.tenant_id)


@router.get("/my-ui-visibility")
async def get_my_ui_visibility(current_user: UserInDB = Depends(get_current_active_user)):
    """Get UI visibility flags for the current user's plan"""
    gate = get_multi_product_feature_gate(db)
    return await gate.get_ui_visibility(current_user.tenant_id)


@router.get("/my-processing-fees", response_model=ProcessingFeeInfo)
async def get_my_processing_fees(current_user: UserInDB = Depends(get_current_active_user)):
    """Get processing fee information for the current user"""
    gate = get_multi_product_feature_gate(db)
    fees = await gate.get_processing_fees(current_user.tenant_id)
    
    return ProcessingFeeInfo(
        invoice_fee_percent=fees.invoice_fee_percent,
        webstore_fee_percent=fees.webstore_fee_percent,
        stripe_connect_enabled=fees.stripe_connect_enabled,
        online_payments_enabled=fees.online_payments_enabled,
        fee_explanation="Platform fees help cover secure payment processing, compliance, and infrastructure costs."
    )


@router.post("/check-feature")
async def check_feature_access(
    category: str,
    feature: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Check if the current user can access a specific feature"""
    gate = get_multi_product_feature_gate(db)
    result = await gate.check_feature(current_user.tenant_id, category, feature)
    return result.model_dump()


@router.get("/upgrade-options")
async def get_upgrade_options(current_user: UserInDB = Depends(get_current_active_user)):
    """Get available upgrade options for the current plan"""
    gate = get_multi_product_feature_gate(db)
    plan_type, is_founder = await gate.get_tenant_plan(current_user.tenant_id)
    current_config = get_plan_config(plan_type)
    
    # Get all plans for upgrade comparison
    all_plans = get_all_plans()
    
    upgrades = []
    for plan in all_plans:
        if plan.plan_type == plan_type:
            continue  # Skip current plan
        
        # Calculate savings/differences
        price_diff = plan.pricing.monthly - current_config.pricing.monthly
        
        upgrades.append({
            "plan_type": plan.plan_type.value,
            "product_line": plan.product_line.value,
            "display_name": plan.display_name,
            "description": plan.description,
            "price_monthly": plan.pricing.monthly,
            "price_annual": plan.pricing.annual,
            "price_difference": price_diff,
            "same_product_line": plan.product_line == current_config.product_line,
            "founder_eligible": plan.founder_eligible and await gate.is_founder_available(),
        })
    
    return {
        "current_plan": plan_type.value,
        "current_product_line": current_config.product_line.value,
        "is_founder": is_founder,
        "upgrade_options": upgrades,
    }


# ============== FOUNDERS EDITION ENDPOINTS ==============

@router.get("/founders-edition")
async def get_founders_edition():
    """Get Founders Edition plan details and availability"""
    from services.founders_config import (
        get_founders_edition_config, 
        FOUNDERS_EDITION_MAX_CUSTOMERS,
        FOUNDERS_EDITION_MONTHLY_CREDITS,
        FOUNDERS_PROMO_CODE
    )
    
    # Count current founders
    founders_count = await db.tenants.count_documents({"plan": "founders_edition"})
    spots_remaining = max(0, FOUNDERS_EDITION_MAX_CUSTOMERS - founders_count)
    
    return {
        "plan": get_founders_edition_config(),
        "availability": {
            "max_spots": FOUNDERS_EDITION_MAX_CUSTOMERS,
            "spots_claimed": founders_count,
            "spots_remaining": spots_remaining,
            "is_available": spots_remaining > 0
        },
        "promo_code": {
            "code": FOUNDERS_PROMO_CODE,
            "description": "Pay for 6 months, get 12 months of access",
            "discount_percent": 50  # Effectively 50% off annual
        },
        "ai_credits": {
            "monthly_allowance": FOUNDERS_EDITION_MONTHLY_CREDITS,
            "expires_monthly": True,
            "packs_available": True
        }
    }


@router.post("/founders-edition/validate-promo")
async def validate_founders_promo_code(
    code: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Validate the FOUNDERS promo code"""
    from services.founders_config import FOUNDERS_PROMO_CODE, FOUNDERS_EDITION_MAX_CUSTOMERS
    
    # Check if code matches
    if code.upper() != FOUNDERS_PROMO_CODE:
        return {
            "valid": False,
            "reason": "Invalid promo code"
        }
    
    # Check if user already used this code
    existing_usage = await db.promo_code_usage.find_one({
        "tenant_id": current_user.tenant_id,
        "promo_code": FOUNDERS_PROMO_CODE
    })
    if existing_usage:
        return {
            "valid": False,
            "reason": "You have already used this promo code"
        }
    
    # Check if spots available
    founders_count = await db.tenants.count_documents({"plan": "founders_edition"})
    if founders_count >= FOUNDERS_EDITION_MAX_CUSTOMERS:
        return {
            "valid": False,
            "reason": "All Founders Edition spots have been claimed"
        }
    
    return {
        "valid": True,
        "discount": {
            "type": "annual_50_percent",
            "description": "Pay for 6 months, get 12 months",
            "original_annual": 1188.00,  # $99 x 12
            "discounted_annual": 594.00   # $99 x 6
        },
        "spots_remaining": FOUNDERS_EDITION_MAX_CUSTOMERS - founders_count
    }

