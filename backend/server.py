"""
SignGuy AI - Backend API Server

This file contains the FastAPI application setup and core utilities.
All models are in /models and all routes are in /routes.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
import base64
from starlette.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from typing import Optional, List, Dict  # Added List, Dict for Phase 2
from datetime import datetime, timezone, timedelta
import re
from services.storage_config import init_storage
from core_runtime import (
    client,
    db,
    logger,
    security,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    pwd_context,
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_active_user,
    has_permission,
    generate_tenant_slug,
)
import bcrypt

# Create the main app
app = FastAPI(title="SignGuy AI API")
app.state.db = db
app.state.secret_key = SECRET_KEY
app.state.algorithm = ALGORITHM

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============== IMPORT MODELS ==============
# All models are now in the /models directory
from models import (
    # Enums
    CustomerStatus, QuoteStatus, JobStatus, JobActivityType,
    JobItemStatus, JobItemType, InvoiceStatus,
    PricingCategory, ServiceType, ApparelType, TransferType,
    VinylType, PrintMaterial, SubstrateType, VehicleType,
    CoverageType, PromoProductType, PayrollTransactionType, ExpenseCategory,
    UserRole, TenantPlan, PaymentMethod,
    MessageType, ProofStatus, AppointmentType, AppointmentStatus,
    WebstoreType, WebstoreStatus, OrderStatus,
    
    # Customer & Portal models
    CustomerBase, CustomerCreate, CustomerUpdate, Customer,
    ConversationMessage, Conversation, ArtworkProof,
    CustomerNotification, Appointment,
    CustomerPortalLogin, CustomerPortalRegister, CustomerPortalToken,
    CustomerProfileUpdate, ConversationCreate, MessageCreate, ProofResponseCreate,
    
    # Jobs, Quotes, Invoices models
    QuoteLineItem, QuoteBase, QuoteCreate, QuoteUpdate, Quote,
    JobBase, JobCreate, JobUpdate, Job,
    JobNoteBase, JobNoteCreate, JobNote,
    JobActivity, JobItemBase, JobItemCreate, JobItemUpdate, JobItem,
    InvoiceLineItem, InvoiceBase, InvoiceCreate, InvoiceUpdate, Invoice,
    
    # Auth & Tenant models
    TenantBase, TenantCreate, TenantUpdate, Tenant,
    UserBase, UserCreate, UserLogin, User, UserInDB, UserRoleUpdate,
    Token, TokenData, PasswordReset,
    Permission, ROLE_PERMISSIONS, get_user_permissions, user_has_permission,
    
    # Pricing models
    MaterialConfig, PricingDefaults, PricingCalculation,
    JobItemPricingData, JobItemEnhanced, JobItemEnhancedCreate, JobItemEnhancedUpdate,
    PricingTemplate, PricingTemplateCreate, PriceCalculateRequest
)


async def require_write_access(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    """Block write operations if the tenant is in grace period (read-only mode).
    Use this dependency on POST/PUT/DELETE routes that create or modify business data."""
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0, "is_platform_owner": 1, "is_founder": 1, "subscription_status": 1, "subscription_ended_at": 1})
    if not tenant:
        return current_user
    if tenant.get("is_platform_owner"):
        return current_user
    if tenant.get("subscription_status") == "active":
        return current_user
    if tenant.get("is_founder") and tenant.get("subscription_ended_at"):
        from datetime import timedelta
        try:
            ended = datetime.fromisoformat(tenant["subscription_ended_at"].replace("Z", "+00:00"))
            if ended.tzinfo is None:
                ended = ended.replace(tzinfo=timezone.utc)
            grace_end = ended + timedelta(days=14)
            if datetime.now(timezone.utc) < grace_end:
                raise HTTPException(
                    status_code=403,
                    detail="Your account is in a 14-day grace period (read-only). Please resubscribe to add new data."
                )
        except (ValueError, TypeError):
            pass
    return current_user


# ============== PERMISSION HELPER ==============

def require_permission(permission: Permission):
    """Dependency to require a specific permission"""
    async def permission_checker(current_user: UserInDB = Depends(get_current_active_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to perform this action"
            )
        return current_user
    return permission_checker


def require_any_permission(*permissions: Permission):
    """Dependency to require any of the specified permissions"""
    async def permission_checker(current_user: UserInDB = Depends(get_current_active_user)):
        for permission in permissions:
            if has_permission(current_user, permission):
                return current_user
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to perform this action"
        )
    return permission_checker


# ============== TENANT HELPER FUNCTIONS ==============

async def get_current_tenant(current_user: UserInDB = Depends(get_current_active_user)) -> Tenant:
    """Get the tenant for the current user"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no associated tenant")
    
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return Tenant(**tenant)


def tenant_query(base_query: dict, tenant_id: str) -> dict:
    """Add tenant_id to a query for data isolation"""
    return {**base_query, "tenant_id": tenant_id}


async def get_tenant_id(current_user: UserInDB = Depends(get_current_active_user)) -> str:
    """Get just the tenant_id for the current user"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no associated tenant")
    return current_user.tenant_id


# ============== JOB ACTIVITY HELPER ==============

async def log_job_activity(
    job_id: str,
    activity_type: JobActivityType,
    description: str,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Log an activity for a job"""
    activity = JobActivity(
        job_id=job_id,
        activity_type=activity_type,
        description=description,
        user_id=user_id,
        user_name=user_name,
        old_value=old_value,
        new_value=new_value,
        metadata=metadata or {}
    )
    await db.job_activities.insert_one(activity.model_dump())
    return activity


# ============== PRICING CALCULATOR FUNCTIONS ==============

async def get_pricing_defaults(tenant_id: str) -> dict:
    """Get pricing defaults for a tenant, or return system defaults"""
    base_defaults = PricingDefaults(tenant_id=tenant_id).model_dump()
    config = await db.pricing_configuration.find_one({"tenant_id": tenant_id}, {"_id": 0})

    if not config:
        config = await db.pricing_defaults.find_one({"tenant_id": tenant_id}, {"_id": 0})

    if not config:
        return base_defaults

    merged = {**base_defaults, **config}
    base_materials = base_defaults.get("materials", [])
    config_materials = config.get("materials") or []
    if config_materials:
        material_map = { (m.get("key") or m.get("id")): m for m in base_materials }
        for material in config_materials:
            key = material.get("key") or material.get("id")
            if key:
                material_map[key] = material
        merged["materials"] = list(material_map.values())
    else:
        merged["materials"] = base_materials
    merged["hardware_accessories"] = config.get("hardware_accessories") or base_defaults.get("hardware_accessories", [])
    base_hardware = base_defaults.get("hardware_accessories", []) or []
    config_hardware = config.get("hardware_accessories") or []
    if config_hardware:
        hardware_map = { (h.get("id") or h.get("name")): h for h in base_hardware }
        for h in config_hardware:
            hk = h.get("id") or h.get("name")
            if hk:
                hardware_map[hk] = h
        merged["hardware_accessories"] = list(hardware_map.values())
    else:
        merged["hardware_accessories"] = base_hardware
    merged["labor_rates"] = {
        **base_defaults.get("labor_rates", {}),
        **config.get("labor_rates", {}),
    }
    merged["category_defaults"] = {
        **base_defaults.get("category_defaults", {}),
        **config.get("category_defaults", {}),
    }
    base_categories = base_defaults.get("category_defaults", {})
    config_categories = config.get("category_defaults", {})
    merged_categories = {}
    for key, base_cat in base_categories.items():
        merged_categories[key] = {**base_cat, **config_categories.get(key, {})}
    for key, value in config_categories.items():
        if key not in merged_categories:
            merged_categories[key] = value
    merged["category_defaults"] = merged_categories
    merged["selling_price_benchmarks"] = {
        **base_defaults.get("selling_price_benchmarks", {}),
        **config.get("selling_price_benchmarks", {}),
    }
    merged["ai_estimation_rules"] = {
        **base_defaults.get("ai_estimation_rules", {}),
        **config.get("ai_estimation_rules", {}),
    }
    merged["benchmark_rules"] = {
        **base_defaults.get("benchmark_rules", {}),
        **config.get("benchmark_rules", {}),
    }
    merged["global_calc_rules"] = {
        **base_defaults.get("global_calc_rules", {}),
        **config.get("global_calc_rules", {}),
    }
    return merged


def get_material_cost_map(defaults: dict) -> dict:
    material_map = {}
    for material in defaults.get("materials", []):
        key = material.get("key") or material.get("id")
        if key:
            cost_value = material.get("cost_per_sqft")
            if cost_value in (None, ""):
                cost_value = material.get("cost_per_unit", 0)
            material_map[key] = float(cost_value or 0)
    return material_map


def find_material(defaults: dict, key: str) -> dict:
    if not key:
        return {}
    for material in defaults.get("materials", []):
        if material.get("key") == key or material.get("id") == key:
            return material
    return {}


def get_material_sell_rate(defaults: dict, key: str) -> float:
    material = find_material(defaults, key)
    if not material:
        return 0
    return float(material.get("sell_rate_per_sqft", 0) or 0)


def get_material_cost_per_sqft(defaults: dict, key: str) -> float:
    material = find_material(defaults, key)
    if not material:
        return 0
    cost_value = material.get("cost_per_sqft")
    if cost_value in (None, ""):
        cost_value = material.get("cost_per_unit", 0)
    return float(cost_value or 0)


def find_hardware_accessory(defaults: dict, key: str) -> dict:
    if not key:
        return {}
    for item in defaults.get("hardware_accessories", []):
        if item.get("id") == key or item.get("name") == key:
            return item
    return {}


def get_hardware_cost(defaults: dict, key: str) -> float:
    item = find_hardware_accessory(defaults, key)
    if not item:
        return 0
    return float(item.get("purchase_cost", 0) or 0)


def get_hardware_sell_price(defaults: dict, key: str) -> float:
    item = find_hardware_accessory(defaults, key)
    if not item:
        return 0
    return float(item.get("default_sell_price", 0) or 0)


def get_category_pricing_config(defaults: dict, category_key: str) -> dict:
    return {
        "default_labor_hours_per_sqft": 0,
        "default_markup_multiplier": defaults.get("default_markup_multiplier", 2.5),
        "target_profit_margin_percent": defaults.get("target_profit_margin_percent", 40.0),
        "minimum_charge": defaults.get("minimum_order", 0),
        **defaults.get("category_defaults", {}).get(category_key, {}),
    }


def calculate_overhead_cost(base_cost: float, labor_hours: float, defaults: dict, category_config: dict) -> float:
    if not defaults.get("apply_overhead_to_jobs", True):
        return 0

    overhead_percent = float(
        category_config.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
    )
    shop_overhead_per_hour = float(
        category_config.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
    )
    return (base_cost * (overhead_percent / 100)) + (labor_hours * shop_overhead_per_hour)



def get_labor_minutes_and_rate(
    category_key: str,
    defaults: dict,
    cfg: dict,
    quantity: float = 1.0,
    is_yard_sign: bool = False,
) -> tuple[float, float, bool]:
    """
    Get production labor minutes and rate from new quiz-based Pricing Foundation fields.
    
    Returns: (production_minutes, shop_labor_rate, include_in_price)
    Falls back to old hours-based calculation if new fields don't exist.
    """
    # Get global labor config
    labor_config = defaults.get("labor", {})
    shop_labor_rate = float(labor_config.get("shop_labor_rate", 75.0) or 75.0)
    include_in_price = labor_config.get("include_labor_in_price", True)
    if include_in_price is None:
        include_in_price = True
    
    # Get category-specific production minutes
    category_defaults = defaults.get("category_defaults", {}).get(category_key, {})
    
    # Special handling for yard signs (quantity-based)
    if is_yard_sign:
        setup_minutes = category_defaults.get("yard_sign_setup_minutes")
        minutes_per_sign = category_defaults.get("yard_sign_minutes_per_sign")
        if setup_minutes is not None and minutes_per_sign is not None:
            total_minutes = float(setup_minutes) + (quantity * float(minutes_per_sign))
            return (total_minutes, shop_labor_rate, include_in_price)
    
    # Regular categories
    production_minutes_basic = category_defaults.get("production_minutes_basic")
    if production_minutes_basic:
        return (float(production_minutes_basic), shop_labor_rate, include_in_price)
    
    # Fallback to old system (return 0 to signal fallback needed)
    return (0.0, shop_labor_rate, include_in_price)


def get_design_charge_config(defaults: dict) -> tuple[str, float, float]:
    """
    Get design charge configuration from new quiz-based fields.
    
    Returns: (charge_separately, design_rate, included_minutes)
    charge_separately values: "yes", "no", "sometimes"
    """
    design_config = defaults.get("design", {})
    charge_separately = design_config.get("charge_design_separately", "yes")
    if isinstance(charge_separately, bool):
        charge_separately = "yes" if charge_separately else "no"
    default_design_rate = float(design_config.get("default_design_rate", 85.0) or 85.0)
    included_minutes = float(design_config.get("included_design_minutes", 30.0) or 30.0)
    
    return (charge_separately, default_design_rate, included_minutes)


def get_apparel_labor_minutes(
    defaults: dict,
    cfg: dict,
    quantity: float,
) -> float:
    """Get apparel labor minutes: setup + (per-item × quantity)"""
    category_defaults = defaults.get("category_defaults", {}).get("apparel", {})
    setup_minutes = float(category_defaults.get("setup_minutes_per_order", 15.0) or 15.0)
    minutes_per_item = float(category_defaults.get("production_minutes_per_item", 3.0) or 3.0)
    return setup_minutes + (quantity * minutes_per_item)



def resolve_selling_price(total_cost: float, markup_multiplier: float, target_margin_percent: float) -> float:
    safe_total_cost = max(float(total_cost or 0), 0)
    safe_markup = max(float(markup_multiplier or 1), 1.0)
    markup_price = safe_total_cost * safe_markup

    margin_price = 0
    margin_decimal = float(target_margin_percent or 0) / 100
    if 0 < margin_decimal < 0.95:
        margin_price = safe_total_cost / (1 - margin_decimal)

    return max(markup_price, margin_price, safe_total_cost)


def get_complexity_multiplier(complexity: int, base: float = 1.0, max_mult: float = 1.5) -> float:
    """Calculate complexity multiplier (1-5 scale) - reduced from 2.0 to 1.5 max"""
    if complexity <= 1:
        return base
    return base + (max_mult - base) * (complexity - 1) / 4


def get_quantity_discount(quantity: float, quantity_breaks: dict) -> float:
    """Calculate quantity discount based on breaks"""
    normalized_breaks = []

    for qty_key, discount_value in quantity_breaks.items():
        if isinstance(discount_value, dict):
            min_qty = float(discount_value.get("min_qty", 0) or 0)
            discount = float(discount_value.get("discount_percent", 0) or 0) / 100
        else:
            min_qty = float(qty_key)
            discount = float(discount_value or 0)
            if discount > 1:
                discount /= 100
        normalized_breaks.append((min_qty, discount))

    for min_qty, discount in sorted(normalized_breaks, key=lambda item: item[0], reverse=True):
        if quantity >= min_qty:
            return discount
    return 0


def apply_rush_order_multiplier(suggested_price: float, rush_order: bool, multiplier: float = 1.25) -> float:
    if not rush_order:
        return suggested_price
    return suggested_price * multiplier


def apply_rounding(price: float, rounding_rule: str = "nearest_dollar") -> float:
    """Apply rounding rule from pricing defaults"""
    if rounding_rule == "nearest_dollar":
        return round(price)
    if rounding_rule == "nearest_5":
        return round(price / 5) * 5
    if rounding_rule == "nearest_10":
        return round(price / 10) * 10
    if rounding_rule == "ceiling":
        import math
        return math.ceil(price)
    if rounding_rule == "nearest_cent":
        return round(price, 2)
    return round(price, 2)


def create_pricing_result(
    material_cost: float,
    labor_cost: float,
    setup_cost: float,
    additional_costs: float,
    suggested_price: float,
    overhead_cost: float = 0,
    estimated_labor_minutes: float = 0,
    breakdown: dict = None
) -> PricingCalculation:
    """Create a PricingCalculation with properly calculated profit fields"""
    production_cost = material_cost + labor_cost + setup_cost + additional_costs + overhead_cost
    profit_amount = suggested_price - production_cost
    profit_margin_percent = round((profit_amount / suggested_price * 100), 1) if suggested_price > 0 else 0
    
    return PricingCalculation(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost, 2),
        setup_cost=round(setup_cost, 2),
        additional_costs=round(additional_costs, 2),
        overhead_cost=round(overhead_cost, 2),
        production_cost=round(production_cost, 2),
        total_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        selling_price=round(suggested_price, 2),
        markup_percent=round((suggested_price / production_cost - 1) * 100, 1) if production_cost > 0 else 0,
        profit_margin_percent=profit_margin_percent,
        profit_amount=round(profit_amount, 2),
        estimated_labor_minutes=round(estimated_labor_minutes, 1),
        breakdown=breakdown or {}
    )



# ============== PHASE 2: STANDARDIZED PRICING RESULT ==============

def create_standardized_pricing_result(
    # === ITEMIZED COSTS ===
    material_cost: float = 0,
    labor_cost: float = 0,              # Production labor only
    design_cost: float = 0,
    setup_cost: float = 0,
    finishing_cost: float = 0,
    hardware_cost: float = 0,
    install_cost: float = 0,
    outsourcing_cost: float = 0,
    overhead_cost: float = 0,
    
    # === PRICING ===
    suggested_price: float = 0,
    minimum_charge: float = 0,
    
    # === METADATA ===
    estimated_labor_minutes: float = 0,
    pricing_method: str = "cost_plus",
    
    # === BREAKDOWN ARRAYS (Optional) ===
    materials_breakdown: List[Dict] = None,
    labor_breakdown: List[Dict] = None,
    design_breakdown: List[Dict] = None,
    setup_breakdown: List[Dict] = None,
    finishing_breakdown: List[Dict] = None,
    hardware_breakdown: List[Dict] = None,
    install_breakdown: List[Dict] = None,
    outsourcing_breakdown: List[Dict] = None,
    
    # === METADATA FIELDS ===
    area_sqft: float = 0,
    billable_sqft: float = 0,
    quantity: float = 1,
    width_inches: float = 0,
    height_inches: float = 0,
    waste_percentage: float = 0,
    target_margin_percent: float = 0,
    markup_multiplier: float = 1.0,
    warnings: List[str] = None,
    overhead_basis: dict = None,  # Phase 2D: explainability for overhead calculation
    
    # === LEGACY FIELDS ===
    legacy_breakdown: dict = None,
) -> PricingCalculation:
    """
    Create standardized pricing response (Phase 2).
    
    Corrected cost structure:
    - base_cost = sum of all itemized costs (before overhead)
    - overhead_cost = overhead applied to base_cost
    - true_cost = base_cost + overhead_cost
    - production_cost = true_cost (alias)
    - profit_amount = selling_price - true_cost
    - profit_margin_percent = profit_amount / selling_price * 100
    """
    from models.pricing import CostLineItem
    
    # Calculate base_cost (sum of all itemized costs before overhead)
    base_cost = (
        material_cost + labor_cost + design_cost + setup_cost +
        finishing_cost + hardware_cost + install_cost + outsourcing_cost
    )
    
    # true_cost = base_cost + overhead
    true_cost = base_cost + overhead_cost
    production_cost = true_cost  # Alias
    
    # Apply minimum charge if needed
    minimum_charge_applied = False
    if minimum_charge > 0 and suggested_price < minimum_charge:
        selling_price = minimum_charge
        minimum_charge_applied = True
    else:
        selling_price = suggested_price
    
    # Calculate profit (based on true_cost)
    profit_amount = selling_price - true_cost
    profit_margin_percent = round(
        (profit_amount / selling_price * 100), 1
    ) if selling_price > 0 else 0
    markup_percent = round(
        (selling_price / true_cost - 1) * 100, 1
    ) if true_cost > 0 else 0
    
    # Helper to convert dict list to CostLineItem list
    def to_line_items(items: List[Dict]) -> List[Dict]:
        """Convert breakdown dicts to proper format for JSON serialization"""
        if not items:
            return []
        result = []
        for item in items:
            result.append({
                "name": item.get("name", ""),
                "quantity": item.get("quantity", 1.0),
                "unit": item.get("unit", "each"),
                "unit_cost": item.get("unit_cost", 0.0),
                "total_cost": item.get("total_cost", 0.0),
                "notes": item.get("notes"),
            })
        return result
    
    # Build structured breakdown
    breakdown = {
        "materials": to_line_items(materials_breakdown or []),
        "labor": to_line_items(labor_breakdown or []),
        "design": to_line_items(design_breakdown or []),
        "setup": to_line_items(setup_breakdown or []),
        "finishing": to_line_items(finishing_breakdown or []),
        "hardware": to_line_items(hardware_breakdown or []),
        "install": to_line_items(install_breakdown or []),
        "outsourcing": to_line_items(outsourcing_breakdown or []),
        "overhead": [
            {
                "name": "Overhead",
                "quantity": overhead_cost,
                "unit": "amount",
                "unit_cost": 0,
                "total_cost": overhead_cost,
                "notes": None,
            }
        ] if overhead_cost > 0 else [],
        "metadata": {
            "area_sqft": area_sqft,
            "billable_sqft": billable_sqft,
            "quantity": quantity,
            "width_inches": width_inches,
            "height_inches": height_inches,
            "waste_percentage": waste_percentage,
            "target_margin_percent": target_margin_percent,
            "markup_multiplier": markup_multiplier,
            "minimum_charge": minimum_charge,
            "warnings": warnings or [],
            "overhead_basis": overhead_basis or {},
            # Merge legacy breakdown for backward compatibility
            **(legacy_breakdown or {})
        }
    }
    
    return PricingCalculation(
        # Itemized costs
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost, 2),
        design_cost=round(design_cost, 2),
        setup_cost=round(setup_cost, 2),
        finishing_cost=round(finishing_cost, 2),
        hardware_cost=round(hardware_cost, 2),
        install_cost=round(install_cost, 2),
        outsourcing_cost=round(outsourcing_cost, 2),
        overhead_cost=round(overhead_cost, 2),
        
        # Legacy
        additional_costs=0,  # Deprecated
        
        # Totals (corrected structure)
        base_cost=round(base_cost, 2),
        true_cost=round(true_cost, 2),
        production_cost=round(production_cost, 2),
        total_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        selling_price=round(selling_price, 2),
        
        # Profit
        profit_amount=round(profit_amount, 2),
        profit_margin_percent=profit_margin_percent,
        markup_percent=markup_percent,
        
        # Metadata
        estimated_labor_minutes=round(estimated_labor_minutes, 1),
        minimum_charge_applied=minimum_charge_applied,
        pricing_method_used=pricing_method,
        
        # Breakdown
        breakdown=breakdown
    )


async def calculate_promotional(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate promotional items using tenant settings and optional overrides."""
    category_config = get_category_pricing_config(defaults, "custom")
    material_cost_map = get_material_cost_map(defaults)
    base_cost = data.unit_cost or material_cost_map.get("misc_material", 0)
    product_type = data.promo_product_type
    
    material_cost = base_cost * quantity
    labor_hours = float(category_config.get("default_labor_hours_per_unit", 0.25) or 0.25) * quantity
    production_rate = float(defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75)) or 0)
    labor_cost = labor_hours * production_rate
    
    # Setup fee is OPTIONAL - only if checkbox is checked
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = 0
    if include_setup:
        setup_fee = data.setup_fee or defaults.get("promo_setup_fee", 15.0)
    
    markup_multiplier = (
        1 + (data.markup_percent / 100)
        if data.markup_percent is not None
        else category_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5))
    )

    # Double-sided upcharge: 'different' art = 1.5× material, 'same' art = 1.2× material
    double_sided_art = getattr(data, 'double_sided_art', None)
    double_sided_multiplier = 1.0
    if double_sided_art == "different":
        double_sided_multiplier = 1.5
    elif double_sided_art in ("same", "true", True):
        double_sided_multiplier = 1.2
    material_cost *= double_sided_multiplier

    pre_overhead_total = material_cost + labor_cost  # setup_fee added flat after markup
    overhead_cost = calculate_overhead_cost(pre_overhead_total, labor_hours, defaults, category_config)
    suggested_price = resolve_selling_price(
        pre_overhead_total + overhead_cost,
        markup_multiplier,
        category_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40.0)),
    )
    # Setup fee added FLAT — not marked up
    suggested_price += setup_fee
    
    # Quantity discount
    discount = get_quantity_discount(quantity, defaults.get("quantity_breaks", {}))
    if discount > 0:
        suggested_price *= (1 - discount)
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order)

    # ============== PHASE 2D: USE STANDARDIZED RESPONSE ==============
    # Promotional is a wholesale + markup model. The per-unit vendor cost is the
    # primary material cost (already multiplied by quantity and double-sided modifier).
    # Overhead math is preserved: overhead is calculated on (material_cost + labor_cost),
    # i.e., setup_fee is intentionally excluded from the overhead basis.
    product_label = str(product_type.value) if product_type and hasattr(product_type, "value") else (str(product_type) if product_type else "Promotional Item")

    materials_list = []
    if material_cost > 0:
        # Effective per-unit cost after double-sided adjustment, so the breakdown line
        # sums exactly to material_cost.
        effective_unit_cost = (material_cost / quantity) if quantity > 0 else material_cost
        materials_list.append({
            "name": f"{product_label} (vendor unit cost)",
            "quantity": quantity,
            "unit": "each",
            "unit_cost": effective_unit_cost,
            "total_cost": material_cost,
            "notes": (
                f"double_sided_multiplier={double_sided_multiplier}" if double_sided_multiplier != 1.0 else None
            ),
        })

    labor_list = []
    if labor_cost > 0:
        labor_list.append({
            "name": "Handling/Production Labor",
            "quantity": labor_hours,
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": labor_cost,
        })

    setup_list = []
    if setup_fee > 0:
        setup_list.append({
            "name": "Setup Fee",
            "quantity": 1,
            "unit": "job",
            "unit_cost": setup_fee,
            "total_cost": setup_fee,
        })

    return create_standardized_pricing_result(
        # Costs (itemized by type)
        material_cost=material_cost,
        labor_cost=labor_cost,
        design_cost=0,
        setup_cost=setup_fee,
        finishing_cost=0,
        hardware_cost=0,
        install_cost=0,
        outsourcing_cost=0,
        overhead_cost=overhead_cost,

        # Pricing
        suggested_price=suggested_price,
        minimum_charge=0,

        # Metadata
        estimated_labor_minutes=labor_hours * 60,
        pricing_method="markup",
        markup_multiplier=markup_multiplier,
        target_margin_percent=float(
            category_config.get(
                "target_profit_margin_percent",
                defaults.get("target_profit_margin_percent", 40.0),
            ) or 0
        ),

        # Overhead explainability (Phase 2D)
        overhead_basis={
            "formula": "(basis_amount * overhead_percentage / 100) + (labor_hours * shop_overhead_per_hour)",
            "basis_amount": round(pre_overhead_total, 2),
            "basis_components": [
                "material_cost",
                "labor_cost",
            ],
            "labor_hours": round(labor_hours, 2),
            "overhead_percentage": float(
                category_config.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
            ),
            "shop_overhead_per_hour": float(
                category_config.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
            ),
            "overhead_excludes_setup_cost": True,
            "notes": (
                "Overhead is calculated from the legacy basis: material_cost + labor_cost. "
                "setup_fee is intentionally excluded from this basis to preserve pre-Phase-2D "
                "behavior (setup fee is added FLAT to selling price, never marked up or "
                "subjected to overhead)."
            ),
        },

        # Breakdown arrays
        materials_breakdown=materials_list,
        labor_breakdown=labor_list,
        setup_breakdown=setup_list,

        # Metadata fields
        quantity=quantity,
        warnings=[],

        # Legacy breakdown (preserve existing keys for backward compat)
        legacy_breakdown={
            "product_type": product_type,
            "base_unit_cost": base_cost,
            "quantity": quantity,
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "markup_multiplier": markup_multiplier,
            "labor_hours": round(labor_hours, 2),
            "production_rate": production_rate,
            "overhead_cost": round(overhead_cost, 2),
            "quantity_discount": discount,
            "double_sided_art": double_sided_art,
            "double_sided_multiplier": double_sided_multiplier,
            "price_per_item": round(suggested_price / quantity, 2) if quantity > 0 else 0,
        },
    )


async def calculate_cut_vinyl(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate cut vinyl using Pricing Foundation defaults."""
    width = data.width_inches or 12
    height = data.height_inches or data.length_inches or 12  # Phase 1: Use canonical height_inches, fallback to legacy length_inches
    unit = (data.unit_of_measure or "inches").lower()
    area_per_piece = (width * height) / 144 if unit != "feet" else (width * height)

    category_config = get_category_pricing_config(defaults, "cut_vinyl")
    min_billable = float(category_config.get("default_minimum_billable_area", 0.5) or 0.5)
    billable_area_per_piece = max(area_per_piece, min_billable)
    total_billable_area = billable_area_per_piece * quantity

    waste_percent = float(category_config.get("waste_percentage", defaults.get("waste_percentage", 0)) or 0)
    waste_adjusted_area = total_billable_area * (1 + (waste_percent / 100))

    default_vinyl_key = category_config.get("default_vinyl_type_key", "oracal_651")
    vinyl_key = data.vinyl_type_key or (data.vinyl_type.value if data.vinyl_type else None) or default_vinyl_key
    vinyl_material = find_material(defaults, vinyl_key)
    vinyl_warning = ""
    if not vinyl_material:
        vinyl_warning = f"Missing vinyl type: {vinyl_key}. Using default."
        vinyl_key = default_vinyl_key
        vinyl_material = find_material(defaults, vinyl_key)

    vinyl_cost_per_sqft = get_material_cost_per_sqft(defaults, vinyl_key)
    vinyl_sell_rate = get_material_sell_rate(defaults, vinyl_key)

    masking_required = data.masking_required
    if masking_required is None:
        masking_required = bool(category_config.get("default_masking_required", True))
    transfer_tape_key = category_config.get("transfer_tape_key", "transfer_tape")
    transfer_tape_cost_per_sqft = get_material_cost_per_sqft(defaults, transfer_tape_key)
    transfer_tape_cost = waste_adjusted_area * transfer_tape_cost_per_sqft if masking_required else 0

    vinyl_cost = waste_adjusted_area * vinyl_cost_per_sqft
    material_cost = vinyl_cost + transfer_tape_cost

    # ===== PRODUCTION LABOR =====
    # Try new minute-based system first
    labor_minutes, shop_labor_rate, include_labor = get_labor_minutes_and_rate(
        "cut_vinyl", defaults, category_config, quantity
    )
    
    if labor_minutes > 0:
        # Use new minute-based labor
        base_production_hours = labor_minutes / 60.0
    else:
        # Fallback to old hours-based system
        base_hours_per_sqft = float(category_config.get("production_labor_hours_per_sqft", category_config.get("default_labor_hours_per_sqft", 0.2)) or 0)
        min_prod_hours = float(category_config.get("min_production_labor_hours_per_item", 0.25) or 0)
        per_piece_hours = billable_area_per_piece * base_hours_per_sqft
        per_piece_hours = max(per_piece_hours, min_prod_hours)
        base_production_hours = per_piece_hours * quantity

    # Apply complexity multipliers
    color_count = max(int(data.num_colors or category_config.get("default_number_of_colors", 1) or 1), 1)
    color_multipliers = category_config.get("color_multipliers", {})
    if color_count >= 4:
        color_mult = float(color_multipliers.get("4_plus", 2.5) or 2.5)
        manual_review = True
    else:
        color_mult = float(color_multipliers.get(str(color_count), 1.0) or 1.0)
        manual_review = False

    weeding_complexity = data.weeding_complexity or category_config.get("default_weeding_complexity", "simple")
    weeding_mult = float(category_config.get("weeding_multipliers", {}).get(weeding_complexity, 1.0) or 1.0)

    production_hours = base_production_hours * color_mult * weeding_mult

    # Get labor rates
    labor_rates = defaults.get("labor_rates", {})
    production_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75))) or 0)
    design_rate = float(labor_rates.get("design", {}).get("hourly_rate", defaults.get("design_hourly_rate", 85)) or 0)
    install_rate = float(labor_rates.get("installation", {}).get("hourly_rate", defaults.get("install_hourly_rate", 95)) or 0)

    # Calculate production cost with new labor inclusion logic
    if labor_minutes > 0 and not include_labor:
        production_cost = 0  # Track internally only, not charged
    else:
        production_cost = production_hours * (shop_labor_rate if labor_minutes > 0 else production_rate)

    # ===== DESIGN CHARGE =====
    charge_separately, default_design_rate, included_minutes = get_design_charge_config(defaults)
    design_hours = 0
    design_cost = 0
    
    if data.artwork_ready:
        design_hours = 0
        design_cost = 0
    elif data.artwork_needed or data.artwork_needed is None:
        # Calculate design time
        base_design_time = float(category_config.get("default_design_time_hours", 0.5) or 0)
        design_complexity = data.design_complexity or category_config.get("default_design_complexity", "simple")
        design_mult = {
            "simple": 1.0,
            "medium": 1.25,
            "complex": 1.5,
            "extreme": 2.0,
        }.get(design_complexity, 1.0)
        design_hours = base_design_time * design_mult
        
        # Apply new design charge logic
        if charge_separately == "no":
            design_cost = 0  # Design included in price, not charged separately
        else:
            # Deduct included minutes before charging
            design_minutes = design_hours * 60
            billable_design_minutes = max(0, design_minutes - included_minutes)
            billable_design_hours = billable_design_minutes / 60.0
            design_cost = billable_design_hours * default_design_rate

    file_cleanup_fee = 0
    if data.file_cleanup_needed:
        file_cleanup_fee = float(category_config.get("default_cleanup_fee", defaults.get("file_cleanup_fee_default", 0)) or 0)

    install_hours = 0
    install_cost = 0
    if data.install_required:
        base_install_hours = total_billable_area * float(category_config.get("install_hours_per_sqft", 0.06) or 0)
        install_complexity = data.install_complexity or category_config.get("default_install_complexity", "easy")
        install_mult = float(category_config.get("install_complexity_multipliers", {}).get(install_complexity, 1.0) or 1.0)
        surface_type = data.surface_type or category_config.get("default_surface_type", "flat_smooth")
        surface_mult = float(category_config.get("surface_multipliers", {}).get(surface_type, 1.0) or 1.0)
        install_hours = base_install_hours * install_mult * surface_mult
        install_min = float(defaults.get("minimum_install_charge", 0) or 0)
        install_cost = max(install_min, install_hours * install_rate)
    else:
        surface_type = data.surface_type or category_config.get("default_surface_type", "flat_smooth")

    labor_cost = production_cost + design_cost + install_cost

    overhead_cost = calculate_overhead_cost(
        material_cost + labor_cost,
        production_hours + design_hours + install_hours,
        defaults,
        category_config,
    )

    base_sell_rate = float(vinyl_sell_rate or category_config.get("sell_rate_defaults", {}).get("base_rate", 12.0) or 12.0)
    sell_base = base_sell_rate * total_billable_area * color_mult * weeding_mult

    use_type = data.use_type or category_config.get("default_use_type", "indoor")
    use_type_mult = float(category_config.get("use_type_multipliers", {}).get(use_type, 1.0) or 1.0)
    sell_base *= use_type_mult

    min_sell = float(category_config.get("default_minimum_sell_price", category_config.get("minimum_charge", 20.0)) or 20.0)
    if category_config.get("sell_method") == "max_of_rate_or_minimum":
        sell_base = max(sell_base, min_sell)

    discount_percent = 0
    for tier in category_config.get("quantity_discounts", []):
        min_qty = float(tier.get("min_qty", 0) or 0)
        max_qty = tier.get("max_qty")
        if quantity >= min_qty and (max_qty is None or quantity <= float(max_qty)):
            discount_percent = float(tier.get("discount_percent", 0) or 0)
            break
    sell_base = sell_base * (1 - (discount_percent / 100))

    suggested_price = sell_base + design_cost + install_cost + file_cleanup_fee
    rush_multiplier = 1 + (float(defaults.get("rush_fee_percentage", 0) or 0) / 100)
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order, rush_multiplier)

    # ============== PHASE 2: USE STANDARDIZED RESPONSE ==============
    # Materials breakdown (vinyl + transfer tape/masking)
    materials_list = []
    if vinyl_cost > 0:
        materials_list.append({
            "name": vinyl_material.get("name", vinyl_key) if vinyl_material else vinyl_key,
            "quantity": waste_adjusted_area,
            "unit": "sqft",
            "unit_cost": vinyl_cost_per_sqft,
            "total_cost": vinyl_cost,
        })
    
    # Labor breakdown (production/weeding labor only)
    labor_list = []
    if production_cost > 0:
        labor_list.append({
            "name": "Production/Weeding Labor",
            "quantity": production_hours,
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": production_cost,
        })
    
    # Design breakdown
    design_list = []
    if design_cost > 0:
        design_list.append({
            "name": "Design/Artwork",
            "quantity": design_hours,
            "unit": "hours",
            "unit_cost": design_rate,
            "total_cost": design_cost,
        })
    
    # Finishing breakdown (transfer tape/masking material cost)
    finishing_list = []
    if transfer_tape_cost > 0:
        finishing_list.append({
            "name": "Transfer Tape/Masking",
            "quantity": waste_adjusted_area,
            "unit": "sqft",
            "unit_cost": transfer_tape_cost_per_sqft,
            "total_cost": transfer_tape_cost,
        })
    
    # Install breakdown
    install_list = []
    if install_cost > 0:
        install_list.append({
            "name": "Installation",
            "quantity": install_hours,
            "unit": "hours",
            "unit_cost": install_rate,
            "total_cost": install_cost,
        })
    
    # Setup breakdown (file cleanup fee)
    setup_list = []
    if file_cleanup_fee > 0:
        setup_list.append({
            "name": "File Cleanup",
            "quantity": 1,
            "unit": "job",
            "unit_cost": file_cleanup_fee,
            "total_cost": file_cleanup_fee,
        })
    
    # Collect warnings
    warnings_list = []
    if vinyl_warning:
        warnings_list.append(vinyl_warning)
    
    # Categorize costs for Phase 2 structure
    # Vinyl → material_cost
    material_costs_only = vinyl_cost
    
    # Transfer tape/masking → finishing_cost
    finishing_costs = transfer_tape_cost
    
    # Production/weeding → labor_cost (design and install are separate)
    labor_costs_only = production_cost
    
    # Design → design_cost
    design_costs = design_cost
    
    # Install → install_cost
    install_costs = install_cost
    
    # File cleanup → setup_cost
    setup_costs = file_cleanup_fee
    
    return create_standardized_pricing_result(
        # Costs (itemized by type)
        material_cost=material_costs_only,
        labor_cost=labor_costs_only,
        design_cost=design_costs,
        setup_cost=setup_costs,
        finishing_cost=finishing_costs,
        hardware_cost=0,
        install_cost=install_costs,
        outsourcing_cost=0,
        overhead_cost=overhead_cost,
        
        # Pricing
        suggested_price=suggested_price,
        minimum_charge=min_sell,
        
        # Metadata
        estimated_labor_minutes=(production_hours + design_hours + install_hours) * 60,
        pricing_method="sell_rate",

        # Overhead explainability (Phase 2D)
        overhead_basis={
            "formula": "(basis_amount * overhead_percentage / 100) + (labor_hours * shop_overhead_per_hour)",
            "basis_amount": round(material_cost + labor_cost, 2),
            "basis_components": [
                "vinyl_cost",
                "transfer_tape_cost",
                "production_cost",
                "design_cost",
                "install_cost",
            ],
            "labor_hours": round(production_hours + design_hours + install_hours, 2),
            "overhead_percentage": float(
                category_config.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
            ),
            "shop_overhead_per_hour": float(
                category_config.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
            ),
            "overhead_excludes_setup_cost": True,
            "notes": (
                "Overhead is calculated from the legacy basis: "
                "vinyl_cost + transfer_tape_cost + production_cost + design_cost + install_cost. "
                "file_cleanup_fee (setup_cost) is intentionally excluded from this basis to preserve "
                "pre-Phase-2D behavior."
            ),
        },
        
        # Breakdown arrays
        materials_breakdown=materials_list,
        labor_breakdown=labor_list,
        design_breakdown=design_list,
        setup_breakdown=setup_list,
        finishing_breakdown=finishing_list,
        install_breakdown=install_list,
        
        # Metadata fields
        area_sqft=area_per_piece,
        billable_sqft=billable_area_per_piece,
        quantity=quantity,
        width_inches=width,
        height_inches=height,
        waste_percentage=waste_percent,
        warnings=warnings_list,
        
        # Legacy breakdown (preserve existing keys for backward compat)
        legacy_breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "unit_of_measure": unit,
            "area_per_piece": round(area_per_piece, 2),
            "billable_area_per_piece": round(billable_area_per_piece, 2),
            "total_billable_area": round(total_billable_area, 2),
            "waste_adjusted_area": round(waste_adjusted_area, 2),
            "vinyl_key": vinyl_key,
            "vinyl_warning": vinyl_warning,
            "vinyl_cost_per_sqft": vinyl_cost_per_sqft,
            "transfer_tape_cost_per_sqft": transfer_tape_cost_per_sqft,
            "masking_required": masking_required,
            "color_count": color_count,
            "manual_review": manual_review,
            "color_multiplier": color_mult,
            "weeding_complexity": weeding_complexity,
            "weeding_multiplier": weeding_mult,
            "production_hours": round(production_hours, 2),
            "design_hours": round(design_hours, 2),
            "install_hours": round(install_hours, 2),
            "use_type": use_type,
            "use_type_multiplier": use_type_mult,
            "surface_type": surface_type,
            "quantity_discount_percent": discount_percent,
            "file_cleanup_fee": round(file_cleanup_fee, 2),
        },
    )


async def calculate_digital_print(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate digital print pricing using Pricing Foundation defaults."""
    width = data.width_inches or 24
    height = data.height_inches or data.length_inches or 24  # Phase 1: Use canonical height_inches, fallback to legacy length_inches
    unit = (data.unit_of_measure or "inches").lower()
    area_per_piece = (width * height) / 144 if unit != "feet" else (width * height)

    category_config = get_category_pricing_config(defaults, "digital_print")
    min_billable = float(category_config.get("default_minimum_billable_area", 1.0) or 1.0)
    billable_area_per_piece = max(area_per_piece, min_billable)
    total_billable_area = billable_area_per_piece * quantity

    waste_percent = float(category_config.get("waste_percentage", defaults.get("waste_percentage", 0)) or 0)
    waste_adjusted_area = total_billable_area * (1 + (waste_percent / 100))

    default_media_key = category_config.get("default_print_media_key", "printable_adhesive_vinyl")
    media_key = data.print_media_key
    if not media_key and data.print_material:
        media_map = {
            "banner_13oz": "printable_adhesive_vinyl",
            "banner_18oz": "printable_adhesive_vinyl",
            "vinyl_adhesive": "printable_adhesive_vinyl",
            "poster_paper": "poster_paper",
            "canvas": "canvas",
            "backlit": "backlit_film",
            "perforated": "perforated_window_film",
        }
        media_key = media_map.get(str(data.print_material.value), default_media_key)
    media_key = media_key or default_media_key

    media_material = find_material(defaults, media_key)
    media_warning = ""
    if not media_material:
        media_warning = f"Missing media type: {media_key}. Using default."
        media_key = default_media_key
        media_material = find_material(defaults, media_key)

    media_cost_per_sqft = get_material_cost_per_sqft(defaults, media_key)
    media_sell_rate = get_material_sell_rate(defaults, media_key)

    material_cost = waste_adjusted_area * media_cost_per_sqft

    ink_coverage = float(data.ink_coverage_percent or category_config.get("default_ink_coverage_percent", 35) or 0)
    ink_key = category_config.get("default_ink_material_key", "digital_print_ink")
    ink_cost_per_sqft = get_material_cost_per_sqft(defaults, ink_key) or float(category_config.get("base_ink_cost_per_sqft", 0.75) or 0)
    ink_cost = waste_adjusted_area * ink_cost_per_sqft * (ink_coverage / 100.0)

    laminate_required = bool(data.laminate)
    laminate_key = data.laminate_material_key or data.laminate_type or category_config.get("default_laminate_key", "laminate_gloss")
    laminate_cost = 0
    laminate_sell_addon = 0
    laminate_warning = ""
    if laminate_required:
        laminate_cost_per_sqft = get_material_cost_per_sqft(defaults, laminate_key)
        if laminate_cost_per_sqft <= 0:
            laminate_warning = f"Missing laminate type: {laminate_key}."
        laminate_cost = waste_adjusted_area * laminate_cost_per_sqft

        laminate_sell_rate = get_material_sell_rate(defaults, laminate_key)
        if laminate_sell_rate <= 0:
            # Fallback when laminate rows don't define explicit sell rates.
            # Keep behavior deterministic and tied to tenant's category markup settings.
            laminate_markup = float(
                category_config.get(
                    "laminate_sell_markup_multiplier",
                    category_config.get(
                        "default_markup_multiplier",
                        defaults.get("default_markup_multiplier", 2.5),
                    ),
                ) or 0
            )
            laminate_sell_rate = laminate_cost_per_sqft * max(laminate_markup, 1.0)

        laminate_sell_addon = waste_adjusted_area * laminate_sell_rate

    substrate_cost = 0
    mounting_hours = 0
    substrate_warning = ""
    if data.mounted_to_substrate:
        substrate_key = data.substrate_material_key
        if not substrate_key and data.substrate_type:
            substrate_map = {
                "coroplast_4mm": "coroplast",
                "coroplast_10mm": "coroplast",
                "aluminum_040": "aluminum_composite",
                "aluminum_063": "aluminum_composite",
                "aluminum_080": "aluminum_composite",
                "pvc_3mm": "foam_board",
                "pvc_6mm": "foam_board",
                "acrylic": "acrylic_sheet",
                "dibond": "aluminum_composite",
                "mdo": "rigid_sign_board",
            }
            substrate_key = substrate_map.get(str(data.substrate_type.value), "")
        if substrate_key:
            substrate_cost_per_sqft = get_material_cost_per_sqft(defaults, substrate_key)
            substrate_cost = waste_adjusted_area * substrate_cost_per_sqft
        else:
            substrate_warning = "Missing substrate type."

        mounting_rate = float(category_config.get("mounting_labor_hours_per_sqft", 0.08) or 0)
        mounting_hours = waste_adjusted_area * mounting_rate

    quality_mode = (data.print_quality_mode or category_config.get("default_print_quality_mode", "standard"))
    quality_mult = float(category_config.get("quality_multipliers", {}).get(quality_mode, 1.0) or 1.0)
    contour_type = (data.contour_cut_type or category_config.get("default_contour_cut_type", "none"))
    contour_mult = float(category_config.get("contour_cut_multipliers", {}).get(contour_type, 1.0) or 1.0)

    # ===== PRODUCTION LABOR =====
    # Try new minute-based system first
    labor_minutes, shop_labor_rate, include_labor = get_labor_minutes_and_rate(
        "digital_print", defaults, category_config, quantity
    )
    
    if labor_minutes > 0:
        # Use new minute-based labor
        base_production_hours = labor_minutes / 60.0
    else:
        # Fallback to old hours-based system
        base_prod_hours_per_sqft = float(category_config.get("production_labor_hours_per_sqft", category_config.get("default_labor_hours_per_sqft", 0.08)) or 0)
        min_prod_hours = float(category_config.get("min_production_labor_hours_per_item", 0.2) or 0)
        per_piece_prod_hours = billable_area_per_piece * base_prod_hours_per_sqft * quality_mult * contour_mult
        per_piece_prod_hours = max(per_piece_prod_hours, min_prod_hours)
        base_production_hours = per_piece_prod_hours * quantity

    # Apply complexity multiplier
    complexity_mult = get_complexity_multiplier(
        int(data.complexity or 1),
        float(defaults.get("complexity_multiplier_base", 1.0) or 1.0),
        float(defaults.get("complexity_multiplier_max", 1.5) or 1.5)
    )
    production_hours = base_production_hours * complexity_mult

    # Piece separation labor
    separation_hours = 0
    if data.piece_separation_required:
        count = max(int(data.separated_piece_count or 0), 0)
        separation_rate = float(category_config.get("piece_separation_hours_per_piece", 0.02) or 0)
        separation_hours = count * separation_rate

    # ===== DESIGN CHARGE =====
    charge_separately, default_design_rate, included_minutes = get_design_charge_config(defaults)
    design_hours = 0
    design_cost = 0
    
    if data.artwork_ready:
        design_hours = 0
        design_cost = 0
    elif data.artwork_needed or data.artwork_needed is None:
        # Calculate design time
        base_design_time = float(category_config.get("default_design_time_hours", 0.5) or 0)
        design_complexity = (data.design_complexity or category_config.get("default_design_complexity", "simple"))
        design_mult = {
            "simple": 1.0,
            "medium": 1.25,
            "complex": 1.5,
            "extreme": 2.0,
        }.get(design_complexity, 1.0)
        design_hours = base_design_time * design_mult
        
        # Apply new design charge logic
        if charge_separately == "no":
            design_cost = 0  # Design included in price, not charged separately
        else:
            # Deduct included minutes before charging
            design_minutes = design_hours * 60
            billable_design_minutes = max(0, design_minutes - included_minutes)
            billable_design_hours = billable_design_minutes / 60.0
            design_cost = billable_design_hours * default_design_rate

    # Get labor rates
    labor_rates = defaults.get("labor_rates", {})
    production_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75))) or 0)
    design_rate = float(labor_rates.get("design", {}).get("hourly_rate", defaults.get("design_hourly_rate", 85)) or 0)
    install_rate = float(labor_rates.get("installation", {}).get("hourly_rate", defaults.get("install_hourly_rate", 95)) or 0)

    # Calculate production cost with new labor inclusion logic
    if labor_minutes > 0 and not include_labor:
        production_labor_cost = 0  # Track internally only, not charged
    else:
        production_labor_cost = production_hours * (shop_labor_rate if labor_minutes > 0 else production_rate)
    
    mounting_labor_cost = mounting_hours * production_rate
    separation_labor_cost = separation_hours * production_rate

    install_hours = 0
    install_cost = 0
    if data.install_required:
        base_install_hours = total_billable_area * float(category_config.get("install_hours_per_sqft", 0.08) or 0)
        install_complexity = (data.install_complexity or category_config.get("default_install_complexity", "easy"))
        install_mult = {
            "easy": 1.0,
            "medium": 1.25,
            "difficult": 1.5,
            "extreme": 2.0,
        }.get(install_complexity, 1.0)
        install_hours = base_install_hours * install_mult
        install_min = float(defaults.get("minimum_install_charge", 0) or 0)
        install_cost = max(install_min, install_hours * install_rate)

    file_cleanup_fee = 0
    if data.file_cleanup_needed:
        file_cleanup_fee = float(category_config.get("default_file_prep_fee", defaults.get("file_cleanup_fee_default", 0)) or 0)

    trim_finish = data.trim_finish_type or category_config.get("default_trim_finish_type", "standard")
    trim_addon = 0
    if trim_finish == "premium":
        trim_addon = float(category_config.get("trim_premium_addon", 3.0) or 0) * quantity

    # Setup fee (optional)
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = 0
    if include_setup:
        setup_fee = float(data.setup_fee or defaults.get("setup_fee_print", defaults.get("setup_fee_default", 0)) or 0)

    material_cost = material_cost + ink_cost + laminate_cost + substrate_cost
    labor_cost = production_labor_cost + mounting_labor_cost + separation_labor_cost + design_cost + install_cost

    overhead_cost = calculate_overhead_cost(material_cost + labor_cost, production_hours + mounting_hours + separation_hours + design_hours + install_hours, defaults, category_config)

    base_sell_rate = float(media_sell_rate or category_config.get("sell_rate_defaults", {}).get("base_rate", 0) or 0)
    sell_base = base_sell_rate * total_billable_area * quality_mult * contour_mult
    sell_base += laminate_sell_addon
    min_sell = float(category_config.get("default_minimum_sell_price", category_config.get("minimum_charge", 0)) or 0)
    sell_base = max(sell_base, min_sell)

    discount_tiers = category_config.get("quantity_discounts", [])
    discount_percent = 0
    for tier in discount_tiers:
        min_qty = float(tier.get("min_qty", 0) or 0)
        max_qty = tier.get("max_qty")
        if quantity >= min_qty and (max_qty is None or quantity <= float(max_qty)):
            discount_percent = float(tier.get("discount_percent", 0) or 0)
            break
    sell_base = sell_base * (1 - (discount_percent / 100))

    suggested_price = sell_base + design_cost + install_cost + file_cleanup_fee + trim_addon + setup_fee
    rush_multiplier = 1 + (float(defaults.get("rush_fee_percentage", 0) or 0) / 100)
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order, rush_multiplier)

    # ============== PHASE 2D: USE STANDARDIZED RESPONSE ==============
    # Categorize costs into the standard buckets.
    # NOTE: overhead math basis is preserved from legacy: material_cost + labor_cost
    # (where material_cost = media + ink + laminate + substrate;
    #        labor_cost   = production + mounting + separation + design + install).
    # This means trim_addon, file_cleanup_fee, and setup_fee are NOT in the overhead basis.
    media_material_cost = waste_adjusted_area * media_cost_per_sqft
    media_name = media_material.get("name", media_key) if media_material else media_key

    # Materials breakdown: print media + ink + substrate (if mounted)
    materials_list = []
    if media_material_cost > 0:
        materials_list.append({
            "name": media_name,
            "quantity": waste_adjusted_area,
            "unit": "sqft",
            "unit_cost": media_cost_per_sqft,
            "total_cost": media_material_cost,
        })
    if ink_cost > 0:
        materials_list.append({
            "name": "Print Ink",
            "quantity": waste_adjusted_area,
            "unit": "sqft",
            "unit_cost": ink_cost_per_sqft * (ink_coverage / 100.0),
            "total_cost": ink_cost,
        })
    if substrate_cost > 0:
        materials_list.append({
            "name": "Mounting Substrate",
            "quantity": waste_adjusted_area,
            "unit": "sqft",
            "unit_cost": get_material_cost_per_sqft(defaults, data.substrate_material_key or "") if (data.substrate_material_key or data.substrate_type) else 0,
            "total_cost": substrate_cost,
        })
    materials_total = media_material_cost + ink_cost + substrate_cost

    # Labor breakdown: production + mounting + separation (design and install are separate)
    labor_list = []
    if production_labor_cost > 0:
        labor_list.append({
            "name": "Production Labor",
            "quantity": production_hours,
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": production_labor_cost,
        })
    if mounting_labor_cost > 0:
        labor_list.append({
            "name": "Mounting Labor",
            "quantity": mounting_hours,
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": mounting_labor_cost,
        })
    if separation_labor_cost > 0:
        labor_list.append({
            "name": "Piece Separation Labor",
            "quantity": separation_hours,
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": separation_labor_cost,
        })
    labor_total = production_labor_cost + mounting_labor_cost + separation_labor_cost

    # Design breakdown
    design_list = []
    if design_cost > 0:
        design_list.append({
            "name": "Design/Artwork",
            "quantity": design_hours,
            "unit": "hours",
            "unit_cost": design_rate,
            "total_cost": design_cost,
        })

    # Finishing breakdown: laminate material cost (sell-side addons excluded)
    finishing_list = []
    if laminate_cost > 0:
        laminate_cost_per_sqft_now = get_material_cost_per_sqft(defaults, laminate_key)
        finishing_list.append({
            "name": "Laminate",
            "quantity": waste_adjusted_area,
            "unit": "sqft",
            "unit_cost": laminate_cost_per_sqft_now,
            "total_cost": laminate_cost,
        })

    # Install breakdown
    install_list = []
    if install_cost > 0:
        install_list.append({
            "name": "Installation",
            "quantity": install_hours,
            "unit": "hours",
            "unit_cost": install_rate,
            "total_cost": install_cost,
        })

    # Setup breakdown: file cleanup, trim premium addon, setup_fee
    setup_list = []
    if file_cleanup_fee > 0:
        setup_list.append({
            "name": "File Cleanup",
            "quantity": 1,
            "unit": "job",
            "unit_cost": file_cleanup_fee,
            "total_cost": file_cleanup_fee,
        })
    if trim_addon > 0:
        setup_list.append({
            "name": "Premium Trim Finish",
            "quantity": quantity,
            "unit": "each",
            "unit_cost": float(category_config.get("trim_premium_addon", 3.0) or 0),
            "total_cost": trim_addon,
        })
    if setup_fee > 0:
        setup_list.append({
            "name": "Setup Fee",
            "quantity": 1,
            "unit": "job",
            "unit_cost": setup_fee,
            "total_cost": setup_fee,
        })
    setup_total = file_cleanup_fee + trim_addon + setup_fee

    # Warnings
    warnings_list = []
    if media_warning:
        warnings_list.append(media_warning)
    if laminate_warning:
        warnings_list.append(laminate_warning)
    if substrate_warning:
        warnings_list.append(substrate_warning)

    return create_standardized_pricing_result(
        # Costs (itemized by type)
        material_cost=materials_total,
        labor_cost=labor_total,
        design_cost=design_cost,
        setup_cost=setup_total,
        finishing_cost=laminate_cost,
        hardware_cost=0,
        install_cost=install_cost,
        outsourcing_cost=0,
        overhead_cost=overhead_cost,

        # Pricing
        suggested_price=suggested_price,
        minimum_charge=min_sell,

        # Metadata
        estimated_labor_minutes=(production_hours + mounting_hours + separation_hours + design_hours + install_hours) * 60,
        pricing_method="sell_rate",

        # Overhead explainability (Phase 2D)
        overhead_basis={
            "formula": "(basis_amount * overhead_percentage / 100) + (labor_hours * shop_overhead_per_hour)",
            "basis_amount": round(material_cost + labor_cost, 2),
            "basis_components": [
                "media_cost",
                "ink_cost",
                "laminate_cost",
                "substrate_cost",
                "production_labor_cost",
                "mounting_labor_cost",
                "separation_labor_cost",
                "design_cost",
                "install_cost",
            ],
            "labor_hours": round(
                production_hours + mounting_hours + separation_hours + design_hours + install_hours, 2
            ),
            "overhead_percentage": float(
                category_config.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
            ),
            "shop_overhead_per_hour": float(
                category_config.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
            ),
            "overhead_excludes_setup_cost": True,
            "notes": (
                "Overhead is calculated from the legacy basis: "
                "media + ink + laminate + substrate + production + mounting + separation + design + install. "
                "file_cleanup_fee, trim_addon, and setup_fee (all setup_cost) are intentionally excluded "
                "from the overhead basis to preserve pre-Phase-2D behavior."
            ),
        },

        # Breakdown arrays
        materials_breakdown=materials_list,
        labor_breakdown=labor_list,
        design_breakdown=design_list,
        setup_breakdown=setup_list,
        finishing_breakdown=finishing_list,
        install_breakdown=install_list,

        # Metadata fields
        area_sqft=area_per_piece,
        billable_sqft=billable_area_per_piece,
        quantity=quantity,
        width_inches=width,
        height_inches=height,
        waste_percentage=waste_percent,
        warnings=warnings_list,

        # Legacy breakdown (preserve existing keys for backward compat)
        legacy_breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "unit_of_measure": unit,
            "area_per_piece": round(area_per_piece, 2),
            "billable_area_per_piece": round(billable_area_per_piece, 2),
            "total_billable_area": round(total_billable_area, 2),
            "waste_adjusted_area": round(waste_adjusted_area, 2),
            "print_media_key": media_key,
            "media_warning": media_warning,
            "media_cost_per_sqft": media_cost_per_sqft,
            "ink_cost_per_sqft": ink_cost_per_sqft,
            "ink_coverage_percent": ink_coverage,
            "laminate_required": laminate_required,
            "laminate_key": laminate_key,
            "laminate_warning": laminate_warning,
            "laminate_cost_per_sqft": get_material_cost_per_sqft(defaults, laminate_key),
            "laminate_sell_addon": round(laminate_sell_addon, 2),
            "substrate_key": data.substrate_material_key or (data.substrate_type.value if data.substrate_type else ""),
            "substrate_warning": substrate_warning,
            "substrate_cost": round(substrate_cost, 2),
            "quality_mode": quality_mode,
            "quality_multiplier": quality_mult,
            "contour_cut_type": contour_type,
            "contour_multiplier": contour_mult,
            "production_hours": round(production_hours, 2),
            "design_hours": round(design_hours, 2),
            "install_hours": round(install_hours, 2),
            "mounting_hours": round(mounting_hours, 2),
            "separation_hours": round(separation_hours, 2),
            "quantity_discount_percent": discount_percent,
            "file_cleanup_fee": round(file_cleanup_fee, 2),
            "trim_addon": round(trim_addon, 2),
            "setup_fee": round(setup_fee, 2),
        },
    )


async def calculate_rigid_signs(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate rigid sign pricing using Pricing Foundation defaults."""
    width = data.width_inches or 24
    height = data.height_inches or data.length_inches or 24  # Phase 1: Use canonical height_inches, fallback to legacy length_inches
    unit = (data.unit_of_measure or "inches").lower()
    area_per_piece = (width * height) / 144 if unit != "feet" else (width * height)

    category_config = get_category_pricing_config(defaults, "rigid_signs")
    min_billable = float(category_config.get("default_minimum_billable_area", 1.0) or 1.0)
    billable_area_per_piece = max(area_per_piece, min_billable)
    total_billable_area = billable_area_per_piece * quantity

    waste_percent = float(category_config.get("waste_percentage", defaults.get("waste_percentage", 0)) or 0)
    waste_adjusted_area = total_billable_area * (1 + (waste_percent / 100))

    default_substrate_key = category_config.get("default_substrate_key", "coroplast_4mm")
    substrate_key = data.substrate_type_key or (data.substrate_type.value if data.substrate_type else None) or default_substrate_key
    substrate_material = find_material(defaults, substrate_key)
    substrate_warning = ""
    if not substrate_material:
        substrate_warning = f"Missing substrate type: {substrate_key}. Using default."
        substrate_key = default_substrate_key
        substrate_material = find_material(defaults, substrate_key)

    substrate_cost_per_sqft = get_material_cost_per_sqft(defaults, substrate_key)
    substrate_sell_rate = get_material_sell_rate(defaults, substrate_key)
    substrate_cost = waste_adjusted_area * substrate_cost_per_sqft

    graphic_method = data.graphic_method or category_config.get("default_graphic_method", "direct_print")
    graphic_cost_per_sqft = 0
    mounting_hours = 0
    graphic_warning = ""
    if graphic_method == "direct_print":
        graphic_cost_per_sqft = get_material_cost_per_sqft(defaults, category_config.get("direct_print_consumable_key", "direct_print_consumable"))
    elif graphic_method == "mounted_print":
        graphic_cost_per_sqft = get_material_cost_per_sqft(defaults, category_config.get("mounted_print_graphic_key", "mounted_print_graphic"))
        mounting_hours = waste_adjusted_area * float(category_config.get("default_mounting_labor_hours_per_sqft", 0.08) or 0)
    elif graphic_method == "cut_vinyl_applied":
        cut_vinyl_key = category_config.get("cut_vinyl_material_key", "oracal_651")
        graphic_cost_per_sqft = get_material_cost_per_sqft(defaults, cut_vinyl_key)
    else:
        graphic_warning = f"Unknown graphic method: {graphic_method}. Using direct print consumables."
        graphic_cost_per_sqft = get_material_cost_per_sqft(defaults, category_config.get("direct_print_consumable_key", "direct_print_consumable"))

    sidedness = data.sidedness or category_config.get("default_sidedness", "single")
    double_art = data.double_sided_art or category_config.get("default_double_sided_art", "same")
    if sidedness == "double":
        sided_key = "double_diff" if double_art == "different" else "double_same"
    else:
        sided_key = "single"
    sided_mult = float(category_config.get("sidedness_multipliers", {}).get(sided_key, 1.0) or 1.0)

    shape_type = data.shape_type or category_config.get("default_shape_type", "rectangle")
    shape_mult = float(category_config.get("shape_multipliers", {}).get(shape_type, 1.0) or 1.0)

    thickness_value = (data.thickness or "").lower()
    if any(token in thickness_value for token in ["10mm", "0.080", "1/4", "1/2"]):
        thickness_tier = "thick_heavy"
    elif any(token in thickness_value for token in ["6mm", "0.063"]):
        thickness_tier = "medium"
    else:
        thickness_tier = "thin_basic"
    thickness_mult = float(category_config.get("thickness_multipliers", {}).get(thickness_tier, 1.0) or 1.0)

    finish_quality = data.finish_quality or category_config.get("default_finish_quality", "standard")
    finish_quality_mult = float(category_config.get("finish_quality_multipliers", {}).get(finish_quality, 1.0) or 1.0)

    finish_required = data.protective_finish
    if finish_required is None:
        finish_required = bool(category_config.get("default_finish_required", False))
    finish_key = data.protective_finish_type or category_config.get("default_finish_key", "rigid_finish_standard")
    finish_warning = ""
    finish_cost = 0
    if finish_required:
        finish_cost_per_sqft = get_material_cost_per_sqft(defaults, finish_key)
        if finish_cost_per_sqft <= 0:
            finish_warning = f"Missing finish type: {finish_key}."
        finish_cost = waste_adjusted_area * finish_cost_per_sqft * sided_mult

    graphic_face_cost = waste_adjusted_area * graphic_cost_per_sqft * sided_mult

    # ===== PRODUCTION LABOR =====
    # Try new minute-based system first
    labor_minutes, shop_labor_rate, include_labor = get_labor_minutes_and_rate(
        "rigid_signs", defaults, category_config, quantity
    )
    
    if labor_minutes > 0:
        # Use new minute-based labor
        base_production_hours = labor_minutes / 60.0
    else:
        # Fallback to old hours-based system
        base_hours_per_sqft = float(category_config.get("production_labor_hours_per_sqft", category_config.get("default_labor_hours_per_sqft", 0.15)) or 0)
        min_prod_hours = float(category_config.get("min_production_labor_hours_per_item", 0.2) or 0)
        per_piece_hours = billable_area_per_piece * base_hours_per_sqft
        per_piece_hours = max(per_piece_hours, min_prod_hours)
        base_production_hours = per_piece_hours * quantity

    # Apply multipliers for rigid signs
    production_hours = base_production_hours * thickness_mult * shape_mult * sided_mult

    # Get labor rates
    labor_rates = defaults.get("labor_rates", {})
    production_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75))) or 0)
    design_rate = float(labor_rates.get("design", {}).get("hourly_rate", defaults.get("design_hourly_rate", 85)) or 0)
    install_rate = float(labor_rates.get("installation", {}).get("hourly_rate", defaults.get("install_hourly_rate", 95)) or 0)

    # Calculate production cost with new labor inclusion logic
    if labor_minutes > 0 and not include_labor:
        production_cost = 0  # Track internally only, not charged
    else:
        production_cost = production_hours * (shop_labor_rate if labor_minutes > 0 else production_rate)
    
    mounting_cost = mounting_hours * production_rate

    # ===== DESIGN CHARGE =====
    charge_separately, default_design_rate, included_minutes = get_design_charge_config(defaults)
    design_hours = 0
    design_cost = 0
    
    if data.artwork_ready:
        design_hours = 0
        design_cost = 0
    elif data.artwork_needed or data.artwork_needed is None:
        # Calculate design time
        base_design_time = float(category_config.get("default_design_time_hours", 0.5) or 0)
        design_complexity = data.design_complexity or "simple"
        design_mult = {
            "simple": 1.0,
            "medium": 1.25,
            "complex": 1.5,
            "extreme": 2.0,
        }.get(design_complexity, 1.0)
        design_hours = base_design_time * design_mult
        
        # Apply new design charge logic
        if charge_separately == "no":
            design_cost = 0  # Design included in price, not charged separately
        else:
            # Deduct included minutes before charging
            design_minutes = design_hours * 60
            billable_design_minutes = max(0, design_minutes - included_minutes)
            billable_design_hours = billable_design_minutes / 60.0
            design_cost = billable_design_hours * default_design_rate

    install_hours = 0
    install_cost = 0
    if data.install_required:
        base_install_hours = total_billable_area * float(category_config.get("install_hours_per_sqft", 0.08) or 0)
        install_complexity = data.install_complexity or "easy"
        install_mult = float(category_config.get("install_complexity_multipliers", {}).get(install_complexity, 1.0) or 1.0)
        install_hours = base_install_hours * install_mult
        install_min = float(defaults.get("minimum_install_charge", 0) or 0)
        install_cost = max(install_min, install_hours * install_rate)

    hardware_cost = 0
    hardware_sell = 0
    hardware_warning = ""
    hardware_labor_cost = 0
    if data.hardware_included:
        hardware_key = data.hardware_type or ""
        hardware_cost = get_hardware_cost(defaults, hardware_key) * quantity
        hardware_sell = get_hardware_sell_price(defaults, hardware_key) * quantity
        if hardware_key and hardware_cost == 0 and hardware_sell == 0:
            hardware_warning = f"Missing hardware: {hardware_key}."
        hardware_labor_cost = float(category_config.get("hardware_handling_labor_cost", 5.0) or 0) * quantity

    drill_prep_fee = 0
    if data.drill_prep_required:
        drill_prep_fee = float(category_config.get("drill_prep_fee", 3.0) or 0) * quantity

    material_cost = substrate_cost + graphic_face_cost + finish_cost + hardware_cost
    labor_cost = production_cost + mounting_cost + design_cost + install_cost + hardware_labor_cost

    overhead_cost = calculate_overhead_cost(material_cost + labor_cost, production_hours + design_hours + install_hours + mounting_hours, defaults, category_config)

    base_sell_rate = float(substrate_sell_rate or category_config.get("sell_rate_defaults", {}).get("base_rate", 0) or 0)
    sell_base = base_sell_rate * total_billable_area
    sell_base *= sided_mult * thickness_mult * shape_mult * finish_quality_mult

    min_sell = float(category_config.get("default_minimum_sell_price", category_config.get("minimum_charge", 25.0)) or 25.0)
    if category_config.get("sell_method") == "max_of_rate_or_minimum":
        sell_base = max(sell_base, min_sell)

    discount_percent = 0
    for tier in category_config.get("quantity_discounts", []):
        min_qty = float(tier.get("min_qty", 0) or 0)
        max_qty = tier.get("max_qty")
        if quantity >= min_qty and (max_qty is None or quantity <= float(max_qty)):
            discount_percent = float(tier.get("discount_percent", 0) or 0)
            break
    sell_base = sell_base * (1 - (discount_percent / 100))

    suggested_price = sell_base + design_cost + install_cost + drill_prep_fee + hardware_sell
    rush_multiplier = 1 + (float(defaults.get("rush_fee_percentage", 0) or 0) / 100)
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order, rush_multiplier)

    # ============== PHASE 2: USE STANDARDIZED RESPONSE ==============
    # Separate costs by category for itemized breakdown
    production_labor_cost = production_cost + mounting_cost  # Production + mounting
    design_labor_cost = design_cost
    install_labor_cost = install_cost + hardware_labor_cost
    
    # Materials breakdown
    materials_list = []
    if substrate_cost > 0:
        materials_list.append({
            "name": substrate_material.get("name", substrate_key) if substrate_material else substrate_key,
            "quantity": waste_adjusted_area,
            "unit": "sqft",
            "unit_cost": substrate_cost_per_sqft,
            "total_cost": substrate_cost,
        })
    if graphic_face_cost > 0:
        materials_list.append({
            "name": f"Graphics ({graphic_method})",
            "quantity": waste_adjusted_area * sided_mult,
            "unit": "sqft",
            "unit_cost": graphic_cost_per_sqft,
            "total_cost": graphic_face_cost,
        })
    
    # Labor breakdown
    labor_list = []
    if production_cost > 0:
        labor_list.append({
            "name": "Production Labor",
            "quantity": production_hours,
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": production_cost,
        })
    if mounting_cost > 0:
        labor_list.append({
            "name": "Mounting Labor",
            "quantity": mounting_hours,
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": mounting_cost,
        })
    
    # Design breakdown
    design_list = []
    if design_hours > 0:
        design_list.append({
            "name": "Design/Artwork",
            "quantity": design_hours,
            "unit": "hours",
            "unit_cost": design_rate,
            "total_cost": design_cost,
        })
    
    # Finishing breakdown
    finishing_list = []
    if finish_cost > 0:
        finishing_list.append({
            "name": finish_key,
            "quantity": waste_adjusted_area * sided_mult,
            "unit": "sqft",
            "unit_cost": get_material_cost_per_sqft(defaults, finish_key),
            "total_cost": finish_cost,
        })
    
    # Hardware breakdown
    hardware_list = []
    if hardware_cost > 0:
        hardware_list.append({
            "name": data.hardware_type or "Hardware",
            "quantity": quantity,
            "unit": "each",
            "unit_cost": hardware_cost / quantity,
            "total_cost": hardware_cost,
        })
    
    # Install breakdown
    install_list = []
    if install_hours > 0:
        install_list.append({
            "name": "Installation",
            "quantity": install_hours,
            "unit": "hours",
            "unit_cost": install_rate,
            "total_cost": install_cost,
        })
    if hardware_labor_cost > 0:
        install_list.append({
            "name": "Hardware Installation Labor",
            "quantity": quantity,
            "unit": "pieces",
            "unit_cost": hardware_labor_cost / quantity,
            "total_cost": hardware_labor_cost,
        })
    
    # Setup breakdown
    setup_list = []
    if drill_prep_fee > 0:
        setup_list.append({
            "name": "Drill Prep",
            "quantity": quantity,
            "unit": "pieces",
            "unit_cost": drill_prep_fee / quantity,
            "total_cost": drill_prep_fee,
        })
    
    # Collect warnings
    warnings_list = []
    if substrate_warning:
        warnings_list.append(substrate_warning)
    if graphic_warning:
        warnings_list.append(graphic_warning)
    if finish_warning:
        warnings_list.append(finish_warning)
    if hardware_warning:
        warnings_list.append(hardware_warning)
    
    return create_standardized_pricing_result(
        # Costs (itemized by type)
        material_cost=substrate_cost + graphic_face_cost,  # Materials only
        labor_cost=production_labor_cost,  # Production labor only
        design_cost=design_labor_cost,
        setup_cost=drill_prep_fee,
        finishing_cost=finish_cost,
        hardware_cost=hardware_cost,
        install_cost=install_labor_cost,
        outsourcing_cost=0,
        overhead_cost=overhead_cost,
        
        # Pricing
        suggested_price=suggested_price,
        minimum_charge=min_sell,
        
        # Metadata
        estimated_labor_minutes=(production_hours + design_hours + install_hours + mounting_hours) * 60,
        pricing_method="sell_rate",

        # Overhead explainability (Phase 2D)
        overhead_basis={
            "formula": "(basis_amount * overhead_percentage / 100) + (labor_hours * shop_overhead_per_hour)",
            "basis_amount": round(material_cost + labor_cost, 2),
            "basis_components": [
                "substrate_cost",
                "graphic_face_cost",
                "finish_cost",
                "hardware_cost",
                "production_labor_cost",
                "mounting_labor_cost",
                "design_labor_cost",
                "install_labor_cost",
                "hardware_labor_cost",
            ],
            "labor_hours": round(production_hours + design_hours + install_hours + mounting_hours, 2),
            "overhead_percentage": float(
                category_config.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
            ),
            "shop_overhead_per_hour": float(
                category_config.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
            ),
            "overhead_excludes_setup_cost": True,
            "notes": (
                "Overhead is calculated from the legacy basis: substrate + graphic_face + "
                "finish + hardware + production + mounting + design + install + hardware_labor. "
                "drill_prep_fee (setup_cost) is intentionally excluded from this basis to "
                "preserve pre-Phase-2D behavior."
            ),
        },

        # Breakdown arrays
        materials_breakdown=materials_list,
        labor_breakdown=labor_list,
        design_breakdown=design_list,
        setup_breakdown=setup_list,
        finishing_breakdown=finishing_list,
        hardware_breakdown=hardware_list,
        install_breakdown=install_list,
        
        # Metadata fields
        area_sqft=area_per_piece,
        billable_sqft=billable_area_per_piece,
        quantity=quantity,
        width_inches=width,
        height_inches=height,
        waste_percentage=waste_percent,
        markup_multiplier=0,  # Not used in sell_rate method
        warnings=warnings_list,
        
        # Legacy breakdown (preserve existing keys for backward compat)
        legacy_breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "unit_of_measure": unit,
            "area_per_piece": round(area_per_piece, 2),
            "billable_area_per_piece": round(billable_area_per_piece, 2),
            "total_billable_area": round(total_billable_area, 2),
            "waste_adjusted_area": round(waste_adjusted_area, 2),
            "substrate_key": substrate_key,
            "substrate_warning": substrate_warning,
            "substrate_cost_per_sqft": substrate_cost_per_sqft,
            "graphic_method": graphic_method,
            "graphic_warning": graphic_warning,
            "graphic_cost_per_sqft": graphic_cost_per_sqft,
            "finish_required": finish_required,
            "finish_key": finish_key,
            "finish_warning": finish_warning,
            "finish_cost_per_sqft": get_material_cost_per_sqft(defaults, finish_key),
            "sidedness": sidedness,
            "double_sided_art": double_art,
            "sidedness_multiplier": sided_mult,
            "shape_type": shape_type,
            "shape_multiplier": shape_mult,
            "thickness": data.thickness,
            "thickness_tier": thickness_tier,
            "thickness_multiplier": thickness_mult,
            "finish_quality": finish_quality,
            "finish_quality_multiplier": finish_quality_mult,
            "production_hours": round(production_hours, 2),
            "mounting_hours": round(mounting_hours, 2),
            "design_hours": round(design_hours, 2),
            "install_hours": round(install_hours, 2),
            "hardware_key": data.hardware_type,
            "hardware_warning": hardware_warning,
            "hardware_cost": round(hardware_cost, 2),
            "hardware_sell": round(hardware_sell, 2),
            "hardware_labor_cost": round(hardware_labor_cost, 2),
            "drill_prep_fee": round(drill_prep_fee, 2),
            "quantity_discount_percent": discount_percent,
        }
    )


async def calculate_banners(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate Banner pricing using Pricing Foundation defaults.

    Spec-driven flow:
      1. Load defaults  2. Compute area  3. Apply min billable + waste
      4. Material cost (banner material + print consumable + optional coating)
      5. Finishing: hems, grommets, pole pockets, reinforced corners, wind slits, specialty sewing
      6. Labor: production + design + install + hardware handling
      7. Overhead  8. Suggested price (sell rate + multipliers + discounts)
      9. Hardware additive  10. Minimum sell price enforcement  11. Rush
    """
    cfg = get_category_pricing_config(defaults, "banners")

    # Dimensions & area
    width = float(data.width_inches or 0)
    height = float(data.height_inches or data.length_inches or 0)  # Phase 1: Use canonical height_inches, fallback to legacy length_inches
    unit = (data.unit_of_measure or cfg.get("default_unit_of_measure", "feet")).lower()
    if unit == "feet":
        area_per_piece = width * height
        perimeter_feet = 2 * (width + height)
        width_feet = width
        height_feet = height
    else:
        area_per_piece = (width * height) / 144 if width and height else 0
        perimeter_feet = 2 * (width + height) / 12 if width and height else 0
        width_feet = width / 12
        height_feet = height / 12

    min_billable = float(cfg.get("default_minimum_billable_area", 4.0) or 4.0)
    billable_area_per_piece = max(area_per_piece, min_billable)
    total_billable_area = billable_area_per_piece * quantity

    waste_percent = float(cfg.get("waste_percentage", 8.0) or 0)
    waste_adjusted_area = total_billable_area * (1 + (waste_percent / 100))

    # ===== BANNER MATERIAL =====
    default_material_key = cfg.get("default_banner_material_key", "banner_13oz")
    material_key = data.banner_material_key or default_material_key
    banner_material = find_material(defaults, material_key)
    material_warning = ""
    if not banner_material:
        material_warning = f"Banner material not found: {material_key}. Using 13 oz fallback."
        material_key = default_material_key
        banner_material = find_material(defaults, material_key)

    material_cost_per_sqft = get_material_cost_per_sqft(defaults, material_key)
    material_sell_rate = get_material_sell_rate(defaults, material_key)

    # Sidedness multiplier (applies to material + sell)
    sided_key = data.banner_double_sided or cfg.get("default_double_sided", "no")
    if sided_key == "same":
        sided_mult_key = "double_same"
    elif sided_key == "different":
        sided_mult_key = "double_diff"
    else:
        sided_mult_key = "single"
    sided_mult = float(cfg.get("sidedness_multipliers", {}).get(sided_mult_key, 1.0) or 1.0)

    banner_material_cost = waste_adjusted_area * material_cost_per_sqft * sided_mult

    # Print consumable (always)
    consumable_key = cfg.get("banner_print_consumable_key", "banner_print_consumable")
    print_consumable_cost_per_sqft = get_material_cost_per_sqft(defaults, consumable_key) or 0.75
    print_consumable_cost = waste_adjusted_area * print_consumable_cost_per_sqft * sided_mult

    # Optional laminate / coating
    laminate_required = data.banner_laminate
    if laminate_required is None:
        laminate_required = bool(cfg.get("default_laminate_required", False))
    laminate_key = data.banner_laminate_type_key or cfg.get("default_laminate_key", "banner_laminate_coating")
    laminate_cost_per_sqft = 0.0
    laminate_cost = 0.0
    laminate_warning = ""
    if laminate_required:
        laminate_cost_per_sqft = get_material_cost_per_sqft(defaults, laminate_key)
        if laminate_cost_per_sqft <= 0:
            laminate_warning = f"Laminate/coating not found: {laminate_key}."
        laminate_cost = waste_adjusted_area * laminate_cost_per_sqft * sided_mult

    # ===== FINISHING =====
    hems = data.banner_hems or cfg.get("default_hems", "standard")
    hem_rate = 0.0
    if hems == "standard":
        hem_rate = float(cfg.get("standard_hem_rate_per_linear_foot", 0.75) or 0)
    elif hems == "reinforced":
        hem_rate = float(cfg.get("reinforced_hem_rate_per_linear_foot", 1.25) or 0)
    hem_cost_per_item = perimeter_feet * hem_rate
    hem_cost = hem_cost_per_item * quantity

    # Grommets
    grommet_mode = data.banner_grommets or cfg.get("default_grommets", "corners")
    grommet_cost_each = float(cfg.get("grommet_cost_each", 0.20) or 0)
    grommet_sell_each = float(cfg.get("grommet_sell_each", 0.75) or 0)
    grommet_min_charge = float(cfg.get("grommet_minimum_charge", 4.0) or 0)
    default_corner_count = int(cfg.get("grommet_default_corner_count", 4) or 4)
    grommet_labor_minutes_each = 0.5
    grommet_count_per_item = 0
    if grommet_mode == "none":
        grommet_count_per_item = 0
    elif grommet_mode == "corners":
        grommet_count_per_item = default_corner_count
    elif grommet_mode == "every_2ft":
        spacing = float(cfg.get("grommet_spacing_feet", {}).get("every_2ft", 2.0) or 2.0)
        grommet_count_per_item = max(4, int(round(perimeter_feet / spacing))) if perimeter_feet else default_corner_count
    elif grommet_mode == "every_3ft":
        spacing = float(cfg.get("grommet_spacing_feet", {}).get("every_3ft", 3.0) or 3.0)
        grommet_count_per_item = max(4, int(round(perimeter_feet / spacing))) if perimeter_feet else default_corner_count
    elif grommet_mode == "custom":
        grommet_count_per_item = int(data.banner_grommet_count or 0)
    total_grommets = grommet_count_per_item * quantity
    grommet_material_cost = total_grommets * grommet_cost_each
    grommet_sell_subtotal = total_grommets * grommet_sell_each
    if grommet_mode != "none" and grommet_sell_subtotal > 0:
        grommet_sell_subtotal = max(grommet_sell_subtotal, grommet_min_charge * quantity)
    grommet_labor_hours = (total_grommets * grommet_labor_minutes_each) / 60.0

    # Pole pockets
    pole_mode = data.banner_pole_pockets or cfg.get("default_pole_pockets", "none")
    pole_rate = float(cfg.get("pole_pocket_rate_per_linear_foot", 3.50) or 0)
    pole_linear_feet_per_item = 0.0
    if pole_mode == "top":
        pole_linear_feet_per_item = width_feet
    elif pole_mode == "top_and_bottom":
        pole_linear_feet_per_item = width_feet * 2
    elif pole_mode == "side_pockets":
        pole_linear_feet_per_item = height_feet * 2
    pole_pocket_cost = pole_linear_feet_per_item * pole_rate * quantity

    # Reinforced corners
    reinforced_corners = data.banner_reinforced_corners
    if reinforced_corners is None:
        reinforced_corners = bool(cfg.get("default_reinforced_corners", False))
    reinforced_corners_cost = (float(cfg.get("reinforced_corners_charge", 6.0) or 0) * quantity) if reinforced_corners else 0.0

    # Wind slits
    wind_slits = data.banner_wind_slits
    if wind_slits is None:
        wind_slits = bool(cfg.get("default_wind_slits", False))
    wind_slit_cost = (float(cfg.get("wind_slit_charge", 2.0) or 0) * quantity) if wind_slits else 0.0

    # Specialty sewing (uses perimeter as linear footage basis)
    specialty_sewing = data.banner_specialty_sewing
    if specialty_sewing is None:
        specialty_sewing = bool(cfg.get("default_specialty_sewing", False))
    specialty_sewing_rate = float(cfg.get("specialty_sewing_rate_per_linear_foot", 2.0) or 0)
    specialty_sewing_cost = (perimeter_feet * specialty_sewing_rate * quantity) if specialty_sewing else 0.0

    # ===== LABOR =====
    labor_rates = defaults.get("labor_rates", {})
    production_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75))) or 75)
    design_rate = float(labor_rates.get("design", {}).get("hourly_rate", defaults.get("design_hourly_rate", 85)) or 85)
    install_rate = float(labor_rates.get("installation", {}).get("hourly_rate", defaults.get("install_hourly_rate", 95)) or 95)
    finishing_rate = float(labor_rates.get("finishing", {}).get("hourly_rate", production_rate) or production_rate)
    install_minimum = float(labor_rates.get("installation", {}).get("minimum_charge", defaults.get("minimum_install_charge", 0)) or 0)

    # ===== PRODUCTION LABOR =====
    # Try new minute-based system first
    labor_minutes, shop_labor_rate, include_labor = get_labor_minutes_and_rate(
        "banners", defaults, cfg, quantity
    )
    
    if labor_minutes > 0:
        # Use new minute-based labor
        production_hours = labor_minutes / 60.0
        if include_labor:
            production_cost = production_hours * shop_labor_rate
        else:
            production_cost = 0  # Track internally only
    else:
        # Fallback to old hours-based system
        base_hrs_per_sqft = float(cfg.get("production_labor_hours_per_sqft", 0.10) or 0)
        min_prod_hrs = float(cfg.get("min_production_labor_hours_per_item", 0.20) or 0)
        per_piece_hours = max(billable_area_per_piece * base_hrs_per_sqft, min_prod_hrs)
        production_hours = per_piece_hours * quantity
        production_cost = production_hours * production_rate

    # Design labor
    design_hours = 0.0
    artwork_ready = data.artwork_ready
    artwork_needed = data.artwork_needed
    if artwork_ready:
        design_hours = 0.0
    elif artwork_needed or artwork_needed is None:
        base_design_time = float(cfg.get("default_design_time_hours", 0.5) or 0)
        complexity = data.design_complexity or cfg.get("default_design_complexity", "simple")
        design_mult = float(cfg.get("design_complexity_multipliers", {}).get(complexity, 1.0) or 1.0)
        design_hours = base_design_time * design_mult
    design_cost = design_hours * design_rate

    # Install labor
    install_hours = 0.0
    install_cost = 0.0
    if data.install_required:
        base_install_hours = float(cfg.get("install_base_hours", 0.5) or 0) + (total_billable_area * float(cfg.get("install_hours_per_sqft", 0.04) or 0))
        complexity = data.install_complexity or cfg.get("default_install_complexity", "easy")
        install_mult = float(cfg.get("install_complexity_multipliers", {}).get(complexity, 1.0) or 1.0)
        install_hours = base_install_hours * install_mult
        install_cost = max(install_minimum, install_hours * install_rate)

    # Hardware (from banner_hardware_keys list)
    hardware_keys_list = data.banner_hardware_keys or []
    hardware_cost = 0.0
    hardware_sell = 0.0
    hardware_labor_minutes = 0.0
    hardware_warning = ""
    for hk in hardware_keys_list:
        hw_list = defaults.get("hardware_accessories", []) or []
        hw = next((h for h in hw_list if h.get("id") == hk or h.get("key") == hk), None)
        if not hw:
            if not hardware_warning:
                hardware_warning = f"Hardware not found: {hk}."
            continue
        hardware_cost += float(hw.get("purchase_cost", 0) or 0) * quantity
        hardware_sell += float(hw.get("default_sell_price", 0) or 0) * quantity
        hardware_labor_minutes += float(hw.get("default_labor_addon_minutes", 0) or 0) * quantity
    hardware_labor_hours = hardware_labor_minutes / 60.0
    hardware_labor_cost = hardware_labor_hours * production_rate

    finishing_labor_hours = grommet_labor_hours
    finishing_labor_cost = finishing_labor_hours * finishing_rate

    # ===== TOTALS =====
    material_cost_total = (
        banner_material_cost
        + print_consumable_cost
        + laminate_cost
        + grommet_material_cost
        + hardware_cost
    )
    labor_cost_total = (
        production_cost
        + design_cost
        + install_cost
        + finishing_labor_cost
        + hardware_labor_cost
    )
    total_labor_hours = production_hours + design_hours + install_hours + finishing_labor_hours + hardware_labor_hours

    overhead_cost = calculate_overhead_cost(
        material_cost_total + labor_cost_total,
        total_labor_hours,
        defaults,
        cfg,
    )

    # ===== SELL SIDE =====
    # Area-based sell rate from material library + sidedness multiplier
    sell_base = (material_sell_rate or 0) * total_billable_area * sided_mult

    # Finishing sell additions (hems/pole pockets/reinforced corners/wind slits/specialty sewing/grommets)
    finishing_sell = hem_cost + pole_pocket_cost + reinforced_corners_cost + wind_slit_cost + specialty_sewing_cost + grommet_sell_subtotal

    # Enforce minimum sell per item using sell_method
    min_sell_per_item = float(cfg.get("default_minimum_sell_price", cfg.get("minimum_charge", 35.0)) or 35.0)
    if cfg.get("sell_method") == "max_of_rate_or_minimum":
        sell_base = max(sell_base, min_sell_per_item * quantity)

    suggested_price = sell_base + finishing_sell + design_cost + install_cost + hardware_sell

    # Quantity discount
    discount_percent = 0
    for tier in cfg.get("quantity_discounts", []) or []:
        min_q = float(tier.get("min_qty", 0) or 0)
        max_q = tier.get("max_qty")
        if quantity >= min_q and (max_q is None or quantity <= float(max_q)):
            discount_percent = float(tier.get("discount_percent", 0) or 0)
            break
    suggested_price = suggested_price * (1 - (discount_percent / 100))

    # Event / pole banner premium
    event_premium_applied = 1.0
    use_type = (data.banner_use_type or cfg.get("default_use_type", "outdoor")).lower()
    event_flag = data.banner_event_premium
    if event_flag is None:
        event_flag = use_type in ("backwall_step_repeat", "event_display")
    if event_flag:
        event_premium_applied *= float(cfg.get("event_premium_multiplier", 1.20) or 1.0)
    if use_type == "pole_banner":
        event_premium_applied *= float(cfg.get("pole_banner_premium_multiplier", 1.30) or 1.0)
    suggested_price = suggested_price * event_premium_applied

    # Enforce total minimum (per-item min × qty)
    suggested_price = max(suggested_price, min_sell_per_item * quantity)

    # Rush
    rush_multiplier = 1 + (float(defaults.get("rush_fee_percentage", 0) or 0) / 100)
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order, rush_multiplier)

    # Price override
    if data.override_enabled and data.price_override:
        suggested_price = float(data.price_override) * quantity

    # ============== PHASE 2: USE STANDARDIZED RESPONSE ==============
    # Separate costs by category for itemized breakdown
    
    # Materials breakdown (banner material + print consumable + laminate)
    materials_list = []
    if banner_material_cost > 0:
        materials_list.append({
            "name": banner_material.get("name", material_key) if banner_material else material_key,
            "quantity": waste_adjusted_area * sided_mult,
            "unit": "sqft",
            "unit_cost": material_cost_per_sqft,
            "total_cost": banner_material_cost,
        })
    if print_consumable_cost > 0:
        materials_list.append({
            "name": "Print Consumable",
            "quantity": waste_adjusted_area * sided_mult,
            "unit": "sqft",
            "unit_cost": print_consumable_cost_per_sqft,
            "total_cost": print_consumable_cost,
        })
    if laminate_cost > 0:
        materials_list.append({
            "name": f"Laminate ({laminate_key})" if laminate_key else "Laminate",
            "quantity": waste_adjusted_area * sided_mult,
            "unit": "sqft",
            "unit_cost": laminate_cost_per_sqft,
            "total_cost": laminate_cost,
        })
    
    # Labor breakdown (production + finishing labor)
    labor_list = []
    if production_cost > 0:
        labor_list.append({
            "name": "Production Labor",
            "quantity": production_hours,
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": production_cost,
        })
    if finishing_labor_cost > 0:
        labor_list.append({
            "name": "Finishing Labor (Grommets)",
            "quantity": finishing_labor_hours,
            "unit": "hours",
            "unit_cost": finishing_rate,
            "total_cost": finishing_labor_cost,
        })
    if hardware_labor_cost > 0:
        labor_list.append({
            "name": "Hardware Installation Labor",
            "quantity": hardware_labor_hours,
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": hardware_labor_cost,
        })
    
    # Design breakdown
    design_list = []
    if design_cost > 0:
        design_list.append({
            "name": "Design/Artwork",
            "quantity": design_hours,
            "unit": "hours",
            "unit_cost": design_rate,
            "total_cost": design_cost,
        })
    
    # Finishing breakdown (only actual material costs, not sell-price additions)
    # Grommets material = actual cost
    # Hems, pole pockets, reinforced corners, wind slits, specialty sewing = sell-price additions (not costs)
    finishing_list = []
    if grommet_material_cost > 0:
        finishing_list.append({
            "name": f"Grommets ({grommet_mode})",
            "quantity": total_grommets,
            "unit": "each",
            "unit_cost": grommet_cost_each,
            "total_cost": grommet_material_cost,
        })
    
    # Hardware breakdown
    hardware_list = []
    if hardware_cost > 0:
        for hk in hardware_keys_list:
            hw_list = defaults.get("hardware_accessories", []) or []
            hw = next((h for h in hw_list if h.get("id") == hk or h.get("key") == hk), None)
            if hw:
                hardware_list.append({
                    "name": hw.get("name", hk),
                    "quantity": quantity,
                    "unit": hw.get("unit_type", "each"),
                    "unit_cost": float(hw.get("purchase_cost", 0) or 0),
                    "total_cost": float(hw.get("purchase_cost", 0) or 0) * quantity,
                })
    
    # Install breakdown
    install_list = []
    if install_cost > 0:
        install_list.append({
            "name": "Installation",
            "quantity": install_hours,
            "unit": "hours",
            "unit_cost": install_rate,
            "total_cost": install_cost,
        })
    
    # Collect warnings
    warnings_list = []
    if material_warning:
        warnings_list.append(material_warning)
    if laminate_warning:
        warnings_list.append(laminate_warning)
    if hardware_warning:
        warnings_list.append(hardware_warning)
    
    # Categorize costs for Phase 2 structure
    # Banner material, print consumable, laminate → material_cost
    material_costs_only = banner_material_cost + print_consumable_cost + laminate_cost
    
    # Grommets material → finishing_cost  
    finishing_costs = grommet_material_cost
    
    # Production + finishing + hardware labor → labor_cost
    labor_costs_only = production_cost + finishing_labor_cost + hardware_labor_cost
    
    # Design → design_cost
    design_costs = design_cost
    
    # Install → install_cost  
    install_costs = install_cost
    
    # Hardware → hardware_cost
    hardware_costs = hardware_cost
    
    return create_standardized_pricing_result(
        # Costs (itemized by type)
        material_cost=material_costs_only,
        labor_cost=labor_costs_only,
        design_cost=design_costs,
        setup_cost=0,
        finishing_cost=finishing_costs,
        hardware_cost=hardware_costs,
        install_cost=install_costs,
        outsourcing_cost=0,
        overhead_cost=overhead_cost,
        
        # Pricing
        suggested_price=suggested_price,
        minimum_charge=min_sell_per_item * quantity,
        
        # Metadata
        estimated_labor_minutes=total_labor_hours * 60,
        pricing_method="cost_plus",

        # Overhead explainability (Phase 2D)
        overhead_basis={
            "formula": "(basis_amount * overhead_percentage / 100) + (labor_hours * shop_overhead_per_hour)",
            "basis_amount": round(material_cost_total + labor_cost_total, 2),
            "basis_components": [
                "banner_material_cost",
                "print_consumable_cost",
                "laminate_cost",
                "production_labor_cost",
                "design_labor_cost",
                "install_labor_cost",
                "finishing_labor_cost",
                "hardware_labor_cost",
            ],
            "labor_hours": round(total_labor_hours, 2),
            "overhead_percentage": float(
                cfg.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
            ),
            "shop_overhead_per_hour": float(
                cfg.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
            ),
            "overhead_excludes_setup_cost": True,
            "notes": (
                "Overhead is calculated from the legacy basis: banner material + print "
                "consumable + laminate + production + design + install + finishing labor + "
                "hardware labor. Sell-side finishing additives (hems, grommets, pole pockets, "
                "reinforced corners, wind slits, specialty sewing) are NOT in this basis."
            ),
        },

        # Breakdown arrays
        materials_breakdown=materials_list,
        labor_breakdown=labor_list,
        design_breakdown=design_list,
        finishing_breakdown=finishing_list,
        hardware_breakdown=hardware_list,
        install_breakdown=install_list,
        
        # Metadata fields
        area_sqft=area_per_piece,
        billable_sqft=billable_area_per_piece,
        quantity=quantity,
        width_inches=width if unit == "inches" else width * 12,
        height_inches=height if unit == "inches" else height * 12,
        waste_percentage=waste_percent,
        warnings=warnings_list,
        
        # Legacy breakdown (preserve existing keys for backward compat)
        legacy_breakdown={
            "dimensions": f"{width} x {height} {unit}",
            "unit_of_measure": unit,
            "area_per_piece": round(area_per_piece, 2),
            "billable_area_per_piece": round(billable_area_per_piece, 2),
            "total_billable_area": round(total_billable_area, 2),
            "waste_adjusted_area": round(waste_adjusted_area, 2),
            "waste_percent": waste_percent,
            "perimeter_feet": round(perimeter_feet, 2),
            "banner_material_key": material_key,
            "banner_material_cost_per_sqft": material_cost_per_sqft,
            "banner_material_sell_rate": material_sell_rate,
            "banner_material_cost": round(banner_material_cost, 2),
            "banner_material_warning": material_warning,
            "print_consumable_cost": round(print_consumable_cost, 2),
            "print_consumable_cost_per_sqft": print_consumable_cost_per_sqft,
            "laminate_required": laminate_required,
            "laminate_key": laminate_key if laminate_required else None,
            "laminate_cost_per_sqft": laminate_cost_per_sqft,
            "laminate_cost": round(laminate_cost, 2),
            "laminate_warning": laminate_warning,
            "sidedness": sided_key,
            "sidedness_multiplier": sided_mult,
            "hems": hems,
            "hem_rate_per_linear_foot": hem_rate,
            "hem_cost": round(hem_cost, 2),
            "grommet_mode": grommet_mode,
            "grommet_count_per_item": grommet_count_per_item,
            "total_grommets": total_grommets,
            "grommet_material_cost": round(grommet_material_cost, 2),
            "grommet_sell_subtotal": round(grommet_sell_subtotal, 2),
            "pole_pockets": pole_mode,
            "pole_pocket_linear_feet_per_item": round(pole_linear_feet_per_item, 2),
            "pole_pocket_cost": round(pole_pocket_cost, 2),
            "reinforced_corners": reinforced_corners,
            "reinforced_corners_cost": round(reinforced_corners_cost, 2),
            "wind_slits": wind_slits,
            "wind_slit_cost": round(wind_slit_cost, 2),
            "specialty_sewing": specialty_sewing,
            "specialty_sewing_cost": round(specialty_sewing_cost, 2),
            "production_hours": round(production_hours, 2),
            "production_cost": round(production_cost, 2),
            "design_hours": round(design_hours, 2),
            "design_cost": round(design_cost, 2),
            "install_hours": round(install_hours, 2),
            "install_cost": round(install_cost, 2),
            "finishing_labor_hours": round(finishing_labor_hours, 2),
            "finishing_labor_cost": round(finishing_labor_cost, 2),
            "hardware_keys": hardware_keys_list,
            "hardware_cost": round(hardware_cost, 2),
            "hardware_sell": round(hardware_sell, 2),
            "hardware_labor_cost": round(hardware_labor_cost, 2),
            "hardware_warning": hardware_warning,
            "overhead_cost": round(overhead_cost, 2),
            "use_type": use_type,
            "event_premium_applied": event_premium_applied,
            "quantity_discount_percent": discount_percent,
            "min_sell_per_item": min_sell_per_item,
        },
    )


async def calculate_vehicle_graphics(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate Vehicle Graphics / Wraps pricing using Pricing Foundation defaults.

    Spec-driven flow:
      1. Load defaults + coverage resolution
      2. Compute estimated graphic area (base_sqft × coverage factor, custom % interpolates)
      3. Apply coverage-appropriate waste for material area
      4. Material cost: wrap vinyl + laminate (if required) + window perf (if included)
      5. Labor: base production/prep + design + surface prep + removal + install + seam/difficulty multipliers + second installer
      6. Overhead  7. Suggested price = max(package benchmark (scaled by complexity), cost-plus)
      8. Window perf sell additive  9. Minimum sell  10. Rush  11. Quantity multiplies totals
    """
    cfg = get_category_pricing_config(defaults, "vehicle_wraps")

    # ===== Coverage resolution =====
    vehicle_type = data.vehicle_type or "van_cargo"
    if hasattr(vehicle_type, "value"):
        vehicle_type = vehicle_type.value
    coverage_raw = data.coverage_type or cfg.get("default_coverage_type", "spot")
    if hasattr(coverage_raw, "value"):
        coverage_raw = coverage_raw.value
    coverage_raw = str(coverage_raw).lower()

    coverage_factors = {"spot": 0.10, "partial": 0.25, "half": 0.45, "full": 1.0}
    custom_percent = float(data.custom_coverage_percent or 0)

    is_custom = coverage_raw == "custom"
    if is_custom:
        if custom_percent >= 100:
            coverage_key = "full"
            coverage_factor = 1.0
        elif custom_percent >= 60:
            coverage_key = "full"
            coverage_factor = custom_percent / 100.0
        elif custom_percent >= 35:
            coverage_key = "half"
            coverage_factor = custom_percent / 100.0
        elif custom_percent > 0:
            coverage_key = "partial"
            coverage_factor = custom_percent / 100.0
        else:
            coverage_key = "spot"
            coverage_factor = coverage_factors["spot"]
    else:
        coverage_key = coverage_raw if coverage_raw in coverage_factors else "spot"
        coverage_factor = coverage_factors.get(coverage_key, 0.10)

    # ===== Area estimation =====
    # Look up vehicle base sqft from materials library (category=vehicle_type)
    vehicle_base_sqft = 160.0
    for m in defaults.get("materials", []) or []:
        if (m.get("key") == vehicle_type or m.get("id") == vehicle_type) and m.get("category") == "vehicle_type":
            vehicle_base_sqft = float(m.get("base_sqft", 160) or 160)
            break
    estimated_area_per_vehicle = float(data.estimated_vehicle_sqft or (vehicle_base_sqft * coverage_factor))
    total_area = estimated_area_per_vehicle * quantity

    # ===== Waste =====
    waste_map = cfg.get("waste_by_coverage", {}) or {}
    waste_percent = float(waste_map.get(coverage_key, cfg.get("waste_percentage", 12.0)) or 12.0)
    if is_custom and "custom" in waste_map:
        waste_percent = float(waste_map.get("custom", waste_percent))
    waste_adjusted_area = total_area * (1 + waste_percent / 100.0)

    # ===== Material cost — wrap vinyl =====
    wrap_material_key = data.wrap_material_key or cfg.get("default_wrap_material_key", "wrap_standard_calendared")
    wrap_material = find_material(defaults, wrap_material_key)
    material_warning = ""
    if not wrap_material:
        material_warning = f"Wrap material not found: {wrap_material_key}. Using calendared fallback."
        wrap_material_key = cfg.get("default_wrap_material_key", "wrap_standard_calendared")
        wrap_material = find_material(defaults, wrap_material_key)
    vinyl_cost_per_sqft = get_material_cost_per_sqft(defaults, wrap_material_key) or 1.50
    vinyl_material_cost = waste_adjusted_area * vinyl_cost_per_sqft

    # ===== Laminate (required by default for printed wrap graphics; default off for simple lettering unless user sets it) =====
    lam_required = data.wrap_laminate_required
    if lam_required is None:
        lam_required = bool(cfg.get("default_laminate_required_for_prints", True))
    lam_key = data.wrap_laminate_type_key or cfg.get("default_wrap_laminate_key", "wrap_laminate_gloss")
    laminate_cost_per_sqft = 0.0
    laminate_material_cost = 0.0
    laminate_warning = ""
    if lam_required:
        laminate_cost_per_sqft = get_material_cost_per_sqft(defaults, lam_key)
        if laminate_cost_per_sqft <= 0:
            laminate_warning = f"Laminate not found: {lam_key}."
            laminate_cost_per_sqft = 1.25
        laminate_material_cost = waste_adjusted_area * laminate_cost_per_sqft

    # ===== Window perf =====
    perf_included = data.window_perf_included
    if perf_included is None:
        perf_included = bool(cfg.get("default_window_perf_included", False))
    perf_scope = (data.window_perf_scope or cfg.get("default_window_perf_scope", "rear")).lower()
    perf_key = cfg.get("window_perf_material_key", "wrap_window_perf")
    perf_material_cost = 0.0
    perf_sell = 0.0
    perf_area = 0.0
    if perf_included:
        scope_area_map = cfg.get("window_perf_scope_area_sqft", {"rear": 18.0, "side": 14.0, "full": 40.0})
        perf_area_per_vehicle = float(scope_area_map.get(perf_scope, 18.0) or 18.0)
        perf_area = perf_area_per_vehicle * quantity
        perf_cost_per_sqft = get_material_cost_per_sqft(defaults, perf_key) or 2.50
        perf_material_cost = perf_area * perf_cost_per_sqft * (1 + waste_percent / 100.0)
        if perf_scope == "side":
            sell_rate = float(cfg.get("window_perf_sell_rate_side_per_sqft", 20.0) or 20.0)
        elif perf_scope == "full":
            # combined: rear + side weighted average
            rear_rate = float(cfg.get("window_perf_sell_rate_rear_per_sqft", 18.0) or 18.0)
            side_rate = float(cfg.get("window_perf_sell_rate_side_per_sqft", 20.0) or 20.0)
            sell_rate = (rear_rate + side_rate) / 2.0
        else:
            sell_rate = float(cfg.get("window_perf_sell_rate_rear_per_sqft", 18.0) or 18.0)
        perf_sell = perf_area * sell_rate

    # ===== Labor rates =====
    labor_rates = defaults.get("labor_rates", {}) or {}
    production_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", 28)) or 28)
    design_rate = float(labor_rates.get("design", {}).get("hourly_rate", defaults.get("design_hourly_rate", 85)) or 85)
    install_rate = float(cfg.get("install_rate_per_hour", 75.0) or 75.0)
    install_minimum = float(cfg.get("install_minimum", 125.0) or 125.0)
    helper_rate = float(cfg.get("second_installer_rate_per_hour", 35.0) or 35.0)
    removal_rate = float(labor_rates.get("removal", {}).get("hourly_rate", defaults.get("removal_hourly_rate", 65)) or 65)

    # ===== PRODUCTION / PREP LABOR =====
    # Try new minute-based system first
    labor_minutes, shop_labor_rate, include_labor = get_labor_minutes_and_rate(
        "vehicle_wraps", defaults, cfg, quantity
    )
    
    if labor_minutes > 0:
        # Use new minute-based labor
        production_hours = labor_minutes / 60.0
        if include_labor:
            production_cost = production_hours * shop_labor_rate
        else:
            production_cost = 0  # Track internally only
    else:
        # Fallback to old hours-based system
        base_hrs_per_sqft = float(cfg.get("production_labor_hours_per_sqft", 0.12) or 0.12)
        min_prod_hrs = float(cfg.get("min_production_labor_hours_per_item", 1.0) or 1.0)
        per_piece_prod_hours = max(estimated_area_per_vehicle * base_hrs_per_sqft, min_prod_hrs)
        production_hours = per_piece_prod_hours * quantity
        production_cost = production_hours * production_rate

    # ===== DESIGN LABOR =====
    charge_separately, default_design_rate, included_minutes = get_design_charge_config(defaults)
    design_hours = 0.0
    design_cost = 0.0
    artwork_ready = bool(data.artwork_ready)
    artwork_needed = data.artwork_needed
    
    if artwork_ready:
        design_hours = 0.0
        design_cost = 0.0
    else:
        needed = artwork_needed if artwork_needed is not None else True
        if needed:
            # Calculate design time
            design_time_map = cfg.get("design_time_by_coverage_hours", {}) or {}
            base_design = float(design_time_map.get(coverage_key, design_time_map.get("partial", 1.5)) or 1.5)
            dc = (data.design_complexity or cfg.get("default_design_complexity", "medium")).lower()
            dc_mult = float(cfg.get("design_complexity_multipliers", {}).get(dc, 1.0) or 1.0)
            design_hours = base_design * dc_mult
            
            # Apply new design charge logic
            if charge_separately == "no":
                design_cost = 0  # Design included in price, not charged separately
            else:
                # Deduct included minutes before charging
                design_minutes = design_hours * 60
                billable_design_minutes = max(0, design_minutes - included_minutes)
                billable_design_hours = billable_design_minutes / 60.0
                design_cost = billable_design_hours * default_design_rate

    # ===== Surface prep =====
    prep_scope = (data.surface_prep_level or cfg.get("default_surface_prep", "none")).lower()
    prep_hours_map = cfg.get("surface_prep_hours", {}) or {}
    prep_hours_per_vehicle = float(prep_hours_map.get(prep_scope, 0) or 0)
    prep_hours = prep_hours_per_vehicle * quantity
    prep_cost = prep_hours * production_rate

    # ===== Removal =====
    removal_scope = (data.removal_scope or cfg.get("default_removal_scope", "none")).lower()
    removal_hours_map = cfg.get("removal_hours", {}) or {}
    removal_hours_per_vehicle = float(removal_hours_map.get(removal_scope, 0) or 0)
    removal_hours = removal_hours_per_vehicle * quantity
    removal_cost = removal_hours * removal_rate
    removal_consumables = float(cfg.get("removal_consumables_allowance", 8.0) or 8.0) * quantity if removal_scope != "none" else 0.0

    # ===== Install =====
    install_required = data.install_required if data.install_required is not None else bool(cfg.get("default_install_required", True))
    install_hours = 0.0
    install_labor_cost = 0.0
    helper_cost = 0.0
    install_difficulty_key = (data.install_difficulty_level or cfg.get("default_install_difficulty", "medium")).lower()
    seam_key = (data.seam_complexity or cfg.get("default_seam_complexity", "basic")).lower()
    second_installer = data.second_installer_required
    if second_installer is None:
        second_installer = bool(cfg.get("default_second_installer_required", False))

    if install_required:
        install_map = cfg.get("install_hours_by_vehicle_coverage", {}) or {}
        vehicle_map = install_map.get(vehicle_type, install_map.get("other", {})) or {}
        base_install_hrs_per_vehicle = float(vehicle_map.get(coverage_key, vehicle_map.get("partial", 4.0)) or 4.0)
        # If custom coverage, interpolate between nearest tiers using the custom%
        if is_custom and custom_percent > 0:
            # scale linearly relative to "full" hours
            full_hrs = float(vehicle_map.get("full", base_install_hrs_per_vehicle * 4) or (base_install_hrs_per_vehicle * 4))
            base_install_hrs_per_vehicle = full_hrs * (custom_percent / 100.0)

        diff_mult = float(cfg.get("install_difficulty_multipliers", {}).get(install_difficulty_key, 1.0) or 1.0)
        seam_mult = float(cfg.get("seam_complexity_multipliers", {}).get(seam_key, 1.0) or 1.0)
        install_hrs_per_vehicle = base_install_hrs_per_vehicle * diff_mult * seam_mult
        install_hours = install_hrs_per_vehicle * quantity
        install_raw_cost = install_hours * install_rate
        # Install minimum enforced per vehicle
        install_labor_cost = max(install_minimum * quantity, install_raw_cost)
        if second_installer:
            helper_cost = install_hours * helper_rate

    # ===== Totals =====
    material_cost_total = vinyl_material_cost + laminate_material_cost + perf_material_cost + removal_consumables
    labor_cost_total = (
        production_cost
        + design_cost
        + prep_cost
        + removal_cost
        + install_labor_cost
        + helper_cost
    )
    total_labor_hours = (
        production_hours + design_hours + prep_hours + removal_hours + install_hours + (install_hours if second_installer else 0)
    )

    overhead_cost = calculate_overhead_cost(
        material_cost_total + labor_cost_total,
        total_labor_hours,
        defaults,
        cfg,
    )

    production_cost_total = material_cost_total + labor_cost_total + overhead_cost

    # ===== Suggested selling price =====
    # 1) Cost-plus via markup/margin
    cost_plus_price = resolve_selling_price(
        production_cost_total,
        cfg.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.4)),
        cfg.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 42.0)),
    )
    # 2) Package benchmark
    package_map = cfg.get("package_pricing_by_vehicle_coverage", {}) or {}
    vehicle_pkg = package_map.get(vehicle_type, package_map.get("other", {})) or {}
    package_price_per_vehicle = float(vehicle_pkg.get(coverage_key, vehicle_pkg.get("partial", 0)) or 0)
    if is_custom and custom_percent > 0:
        full_pkg = float(vehicle_pkg.get("full", package_price_per_vehicle * 4) or 0)
        package_price_per_vehicle = full_pkg * (custom_percent / 100.0)

    # Apply install difficulty + seam complexity uplift to package price (reflect install complexity in benchmark)
    if install_required:
        diff_mult = float(cfg.get("install_difficulty_multipliers", {}).get(install_difficulty_key, 1.0) or 1.0)
        seam_mult = float(cfg.get("seam_complexity_multipliers", {}).get(seam_key, 1.0) or 1.0)
        package_price_per_vehicle *= diff_mult * seam_mult

    package_price_total = package_price_per_vehicle * quantity

    sell_method = cfg.get("sell_method", "max_of_package_or_cost_plus")
    if sell_method == "max_of_package_or_cost_plus":
        suggested_price = max(package_price_total, cost_plus_price)
    elif sell_method == "package_only":
        suggested_price = package_price_total if package_price_total > 0 else cost_plus_price
    else:
        suggested_price = cost_plus_price

    # Add window perf sell additive
    suggested_price += perf_sell

    # Minimum sell
    min_sell = float(cfg.get("default_minimum_sell_price", cfg.get("minimum_charge", 150.0)) or 150.0)
    suggested_price = max(suggested_price, min_sell * quantity)

    # Rush
    rush_pct = float(cfg.get("rush_increase_percent", defaults.get("rush_fee_percentage", 30.0)) or 30.0)
    rush_multiplier = 1 + (rush_pct / 100.0)
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order, rush_multiplier)

    # Price override (per vehicle × quantity)
    manual_override_used = False
    if data.override_enabled and data.price_override:
        suggested_price = float(data.price_override) * quantity
        manual_override_used = True

    # ============== PHASE 2D: USE STANDARDIZED RESPONSE ==============
    # Re-bucket costs into standard Phase 2 categories. Overhead math is
    # preserved because the LEGACY local sums (material_cost_total +
    # labor_cost_total) are still what's fed into calculate_overhead_cost above.
    # New mapping:
    #   materials: wrap vinyl + window perf + removal_consumables
    #   finishing: laminate
    #   labor:     production + surface_prep + removal (general production labor)
    #   design:    design hours × design_rate
    #   install:   install labor (with install_minimum floor) + helper labor
    #   setup/hardware/outsourcing: 0 for vehicle_graphics
    materials_list = []
    if vinyl_material_cost > 0:
        wrap_name = (wrap_material.get("name", wrap_material_key) if wrap_material else wrap_material_key)
        materials_list.append({
            "name": wrap_name,
            "quantity": round(waste_adjusted_area, 2),
            "unit": "sqft",
            "unit_cost": vinyl_cost_per_sqft,
            "total_cost": round(vinyl_material_cost, 2),
        })
    if perf_material_cost > 0:
        perf_unit_cost = (perf_material_cost / (perf_area * (1 + waste_percent / 100.0))) if perf_area > 0 else 0
        materials_list.append({
            "name": f"Window Perf ({perf_scope})",
            "quantity": round(perf_area * (1 + waste_percent / 100.0), 2),
            "unit": "sqft",
            "unit_cost": perf_unit_cost,
            "total_cost": round(perf_material_cost, 2),
        })
    if removal_consumables > 0:
        materials_list.append({
            "name": "Removal Consumables",
            "quantity": quantity,
            "unit": "vehicle",
            "unit_cost": float(cfg.get("removal_consumables_allowance", 8.0) or 8.0),
            "total_cost": round(removal_consumables, 2),
        })
    materials_total = vinyl_material_cost + perf_material_cost + removal_consumables

    finishing_list = []
    if laminate_material_cost > 0:
        finishing_list.append({
            "name": f"Laminate ({lam_key})",
            "quantity": round(waste_adjusted_area, 2),
            "unit": "sqft",
            "unit_cost": laminate_cost_per_sqft,
            "total_cost": round(laminate_material_cost, 2),
        })

    labor_list = []
    if production_cost > 0:
        labor_list.append({
            "name": "Production / Prep Labor",
            "quantity": round(production_hours, 2),
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": round(production_cost, 2),
        })
    if prep_cost > 0:
        labor_list.append({
            "name": f"Surface Prep ({prep_scope})",
            "quantity": round(prep_hours, 2),
            "unit": "hours",
            "unit_cost": production_rate,
            "total_cost": round(prep_cost, 2),
        })
    if removal_cost > 0:
        labor_list.append({
            "name": f"Removal Labor ({removal_scope})",
            "quantity": round(removal_hours, 2),
            "unit": "hours",
            "unit_cost": removal_rate,
            "total_cost": round(removal_cost, 2),
        })
    labor_total = production_cost + prep_cost + removal_cost

    design_list = []
    if design_cost > 0:
        design_list.append({
            "name": "Design / Artwork",
            "quantity": round(design_hours, 2),
            "unit": "hours",
            "unit_cost": design_rate,
            "total_cost": round(design_cost, 2),
        })

    install_list = []
    if install_labor_cost > 0:
        effective_install_rate = (install_labor_cost / install_hours) if install_hours > 0 else install_rate
        install_list.append({
            "name": "Vehicle Install Labor",
            "quantity": round(install_hours, 2),
            "unit": "hours",
            "unit_cost": round(effective_install_rate, 2),
            "total_cost": round(install_labor_cost, 2),
            "notes": (
                f"difficulty={install_difficulty_key}; seam={seam_key}; "
                f"install_minimum_floor={install_minimum * quantity}"
            ),
        })
    if helper_cost > 0:
        install_list.append({
            "name": "Second Installer (Helper)",
            "quantity": round(install_hours, 2),
            "unit": "hours",
            "unit_cost": helper_rate,
            "total_cost": round(helper_cost, 2),
        })
    install_total = install_labor_cost + helper_cost

    warnings_list = []
    if material_warning:
        warnings_list.append(material_warning)
    if laminate_warning:
        warnings_list.append(laminate_warning)

    return create_standardized_pricing_result(
        # === ITEMIZED COSTS (Phase 2D mapping) ===
        material_cost=materials_total,
        labor_cost=labor_total,
        design_cost=design_cost,
        setup_cost=0,
        finishing_cost=laminate_material_cost,
        hardware_cost=0,
        install_cost=install_total,
        outsourcing_cost=0,
        overhead_cost=overhead_cost,

        # === PRICING ===
        suggested_price=suggested_price,
        minimum_charge=min_sell * quantity,

        # === METADATA ===
        estimated_labor_minutes=total_labor_hours * 60,
        pricing_method=("manual_override" if manual_override_used else sell_method),
        markup_multiplier=float(cfg.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.4)) or 2.4),
        target_margin_percent=float(cfg.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 42.0)) or 42.0),

        # Overhead explainability (Phase 2D)
        overhead_basis={
            "formula": "(basis_amount * overhead_percentage / 100) + (labor_hours * shop_overhead_per_hour)",
            "basis_amount": round(material_cost_total + labor_cost_total, 2),
            "basis_components": [
                "vinyl_material_cost",
                "laminate_material_cost",
                "perf_material_cost",
                "removal_consumables",
                "production_cost",
                "design_cost",
                "surface_prep_cost",
                "removal_cost",
                "install_labor_cost",
                "helper_cost",
            ],
            "labor_hours": round(total_labor_hours, 2),
            "labor_hours_components": [
                "production_hours",
                "design_hours",
                "prep_hours",
                "removal_hours",
                "install_hours",
                "install_hours (×2 if second_installer)",
            ],
            "overhead_percentage": float(
                cfg.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
            ),
            "shop_overhead_per_hour": float(
                cfg.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
            ),
            "overhead_excludes_setup_cost": True,
            "notes": (
                "Overhead is calculated from the legacy basis: all material costs "
                "(vinyl + laminate + perf + removal consumables) plus all labor costs "
                "(production + design + prep + removal + install + second installer). "
                "Window-perf SELL additive is added after cost-plus and is NOT in this basis. "
                "Phase 2D moves laminate from material_cost to finishing_cost, but overhead "
                "math is preserved exactly as pre-Phase-2D."
            ),
        },

        # === BREAKDOWN ARRAYS ===
        materials_breakdown=materials_list,
        labor_breakdown=labor_list,
        design_breakdown=design_list,
        finishing_breakdown=finishing_list,
        install_breakdown=install_list,

        # === METADATA FIELDS ===
        area_sqft=estimated_area_per_vehicle,
        billable_sqft=total_area,
        quantity=quantity,
        waste_percentage=waste_percent,
        warnings=warnings_list,

        # === LEGACY BREAKDOWN (preserve all existing keys) ===
        legacy_breakdown={
            "vehicle_type": vehicle_type,
            "coverage_type_input": coverage_raw,
            "coverage_resolved": coverage_key,
            "custom_coverage_percent": custom_percent if is_custom else None,
            "coverage_factor": round(coverage_factor, 3),
            "vehicle_base_sqft": vehicle_base_sqft,
            "estimated_area_per_vehicle": round(estimated_area_per_vehicle, 2),
            "total_area": round(total_area, 2),
            "waste_percent": waste_percent,
            "waste_adjusted_area": round(waste_adjusted_area, 2),
            "wrap_material_key": wrap_material_key,
            "wrap_material_warning": material_warning,
            "vinyl_cost_per_sqft": vinyl_cost_per_sqft,
            "vinyl_material_cost": round(vinyl_material_cost, 2),
            "laminate_required": bool(lam_required),
            "laminate_key": lam_key if lam_required else None,
            "laminate_cost_per_sqft": laminate_cost_per_sqft,
            "laminate_material_cost": round(laminate_material_cost, 2),
            "laminate_warning": laminate_warning,
            "window_perf_included": bool(perf_included),
            "window_perf_scope": perf_scope if perf_included else None,
            "window_perf_area": round(perf_area, 2),
            "window_perf_material_cost": round(perf_material_cost, 2),
            "window_perf_sell": round(perf_sell, 2),
            "production_hours": round(production_hours, 2),
            "production_cost": round(production_cost, 2),
            "design_hours": round(design_hours, 2),
            "design_cost": round(design_cost, 2),
            "design_complexity": (data.design_complexity or cfg.get("default_design_complexity", "medium")),
            "surface_prep_level": prep_scope,
            "surface_prep_hours": round(prep_hours, 2),
            "surface_prep_cost": round(prep_cost, 2),
            "removal_scope": removal_scope,
            "removal_hours": round(removal_hours, 2),
            "removal_cost": round(removal_cost, 2),
            "removal_consumables": round(removal_consumables, 2),
            "install_required": bool(install_required),
            "install_difficulty": install_difficulty_key,
            "seam_complexity": seam_key,
            "install_hours": round(install_hours, 2),
            "install_rate": install_rate,
            "install_minimum": install_minimum,
            "install_labor_cost": round(install_labor_cost, 2),
            "second_installer_required": bool(second_installer),
            "helper_rate_per_hour": helper_rate,
            "helper_cost": round(helper_cost, 2),
            "overhead_cost": round(overhead_cost, 2),
            "production_cost_total": round(production_cost_total, 2),
            "cost_plus_price": round(cost_plus_price, 2),
            "package_price_per_vehicle": round(package_price_per_vehicle, 2),
            "package_price_total": round(package_price_total, 2),
            "sell_method": sell_method,
            "min_sell_per_item": min_sell,
            "total_per_vehicle": round(suggested_price / quantity, 2) if quantity > 0 else 0,
            # Phase 2D: preserve legacy meaning for any consumer that read these.
            "legacy_material_cost_total": round(material_cost_total, 2),
            "legacy_labor_cost_total": round(labor_cost_total, 2),
            "manual_override_used": manual_override_used,
            "price_override": data.price_override if manual_override_used else None,
        },
    )


async def calculate_services(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate Services pricing using Pricing Foundation defaults.

    Cost side: labor + travel + equipment + subcontract + permit + overhead
    Sell side: resolved per sell_method (cost_plus | pass_through_plus_markup | max_of_both)
               with service-type minimum, billing-unit math, complexity multipliers, rush.
    """
    cfg = get_category_pricing_config(defaults, "services")

    # ===== Service type resolution =====
    service_types = cfg.get("available_service_types", []) or []
    st_key = data.service_type or cfg.get("default_service_type", "general_labor")
    if hasattr(st_key, "value"):
        st_key = st_key.value
    st_info = next((s for s in service_types if s.get("key") == st_key), None)
    warnings = []
    if not st_info:
        warnings.append(f"Service type '{st_key}' not found. Using general_labor fallback.")
        st_key = "general_labor"
        st_info = next((s for s in service_types if s.get("key") == "general_labor"), {}) or {}

    # ===== Billing unit =====
    billing_unit = (data.services_billing_unit or st_info.get("default_billing_unit") or "hour").lower()

    # ===== Labor role + rates =====
    labor_role = data.services_labor_role or st_info.get("default_labor_role") or cfg.get("default_labor_role", "production")
    labor_roles = cfg.get("labor_roles", {}) or {}
    role_entry = labor_roles.get(labor_role, labor_roles.get("production", {})) or {}
    if labor_role not in labor_roles:
        warnings.append(f"Labor role '{labor_role}' not found. Using production rate.")
    labor_cost_rate = float(role_entry.get("cost_per_hour", 28.0) or 28.0)
    labor_sell_rate = float(role_entry.get("sell_per_hour", 75.0) or 75.0)
    if data.hourly_rate_override and data.hourly_rate_override > 0:
        labor_sell_rate = float(data.hourly_rate_override)

    # ===== Complexity =====
    complexity_key = (data.services_complexity or "medium").lower()
    complexity_mult = float((cfg.get("complexity_multipliers", {}) or {}).get(complexity_key, 1.25))

    # ===== Quantity / hours =====
    qty_raw = float(quantity or 1)
    min_billable_qty = float(cfg.get("default_min_billable_quantity", 1.0) or 1.0)
    minimum_applies = data.services_minimum_applies if data.services_minimum_applies is not None else True
    estimated_hours = float(data.estimated_hours or 0)
    # Apply minimum billable quantity to hour-based billing if minimum applies
    effective_hours = estimated_hours
    if billing_unit == "hour" and minimum_applies and effective_hours > 0 and effective_hours < min_billable_qty:
        effective_hours = min_billable_qty

    # ===== Labor cost + suggested-sell labor portion =====
    labor_cost = 0.0
    labor_sell_baseline = 0.0
    flat_fee = data.services_flat_fee if data.services_flat_fee is not None else st_info.get("default_flat_fee")
    unit_rate = data.services_unit_rate_override if data.services_unit_rate_override is not None else st_info.get("default_suggested_sell_per_hour")
    unit_rate = float(unit_rate or 0)

    # L-10: num_workers must be a positive integer. Fractional values from AI
    # would silently truncate via int(); reject them by rounding to nearest
    # whole worker with a minimum of 1. A bulletproof bound that never lets
    # the multiplier collapse to zero.
    try:
        num_workers_raw = float(data.num_workers if data.num_workers is not None else 1)
    except (TypeError, ValueError):
        num_workers_raw = 1.0
    num_workers = max(int(round(num_workers_raw)), 1)
    # L-7: resolve trip rate / cost once so we don't recompute it inside the
    # Travel block below. Kept here for clarity; used later when trip charge
    # applies or when billing_unit == "trip".
    trip_rate_default = float(cfg.get("trip_charge_default", 45.0) or 0)
    trip_cost_rate = float(cfg.get("trip_charge_cost", 0) or 0)
    trip_count = max(int(data.services_trip_count or 1), 1)

    if billing_unit == "hour":
        effective_hours_workers = effective_hours * num_workers
        labor_cost = effective_hours_workers * labor_cost_rate * complexity_mult
        labor_sell_baseline = effective_hours_workers * (unit_rate if unit_rate > 0 else labor_sell_rate) * complexity_mult
    elif billing_unit == "flat":
        # Flat-fee services: labor cost = est_hours × role rate (if provided) for internal cost tracking
        labor_cost = (effective_hours or 0.5) * num_workers * labor_cost_rate
        flat_value = float(flat_fee if flat_fee is not None else unit_rate)
        labor_sell_baseline = flat_value * qty_raw
    elif billing_unit in ("piece", "sqft", "linear_foot"):
        labor_cost = (effective_hours or 0) * num_workers * labor_cost_rate * complexity_mult
        labor_sell_baseline = qty_raw * (unit_rate if unit_rate > 0 else labor_sell_rate) * complexity_mult
    elif billing_unit == "mile":
        miles = float(data.services_travel_miles or qty_raw or 0)
        labor_cost = miles * float(cfg.get("travel_cost_per_mile", 0.65) or 0)
        labor_sell_baseline = miles * float(cfg.get("travel_sell_rate_per_mile", 1.25) or 0)
    elif billing_unit == "trip":
        # L-7: reuse already-resolved trip_rate_default / trip_cost_rate / trip_count
        trips = max(trip_count, int(qty_raw))
        labor_cost = trips * trip_cost_rate + (effective_hours * num_workers * labor_cost_rate)
        labor_sell_baseline = trips * (unit_rate if unit_rate > 0 else trip_rate_default)
    elif billing_unit == "day":
        days = float(qty_raw or 1)
        day_hours = float(cfg.get("default_day_hours", 8) or 8)
        labor_cost = days * day_hours * num_workers * labor_cost_rate * complexity_mult
        daily_sell = (unit_rate if unit_rate > 0 else labor_sell_rate * day_hours)
        labor_sell_baseline = days * daily_sell * complexity_mult
    else:  # custom
        labor_cost = (effective_hours or 0) * num_workers * labor_cost_rate * complexity_mult
        labor_sell_baseline = qty_raw * (unit_rate if unit_rate > 0 else labor_sell_rate) * complexity_mult

    # ===== Travel =====
    travel_cost = 0.0
    travel_sell = 0.0
    travel_required = data.services_travel_required if data.services_travel_required is not None else bool(st_info.get("requires_travel", cfg.get("default_travel_enabled", False)))
    travel_miles = float(data.services_travel_miles or 0)
    if travel_required and billing_unit != "mile":
        travel_cost = travel_miles * float(cfg.get("travel_cost_per_mile", 0.65) or 0)
        travel_sell = travel_miles * float(cfg.get("travel_sell_rate_per_mile", 1.25) or 0)

    trip_charge_applies = bool(data.services_trip_charge_applies)
    # H-1: when billing_unit is already a travel-based unit (mile or trip), the
    # trip charge is implicit in the unit rate. Adding it again would double-bill
    # the customer for travel. Skip the add-on in those cases.
    travel_native_unit = billing_unit in ("mile", "trip")
    if trip_charge_applies and not travel_native_unit:
        # L-7: reuse resolved trip_rate_default / trip_cost_rate / trip_count
        travel_cost += trip_count * trip_cost_rate
        travel_sell += trip_count * trip_rate_default
        # Enforce minimum_trip_charge floor on travel_sell
        min_trip = float(cfg.get("minimum_trip_charge", 45.0) or 0)
        if travel_sell < min_trip:
            travel_sell = min_trip

    # ===== Equipment =====
    equipment_cost = 0.0
    equipment_sell = 0.0
    equipment_required = data.services_equipment_required if data.services_equipment_required is not None else bool(cfg.get("default_equipment_enabled", False))
    equipment_days = float(data.services_equipment_days or 0)
    equipment_hours = float(data.services_equipment_hours or 0)
    equipment_type = data.services_equipment_type or "custom"
    if equipment_required and (equipment_days > 0 or equipment_hours > 0):
        eq_library = cfg.get("equipment_library", []) or []
        eq_entry = next((e for e in eq_library if e.get("key") == equipment_type), None)
        if not eq_entry:
            warnings.append(f"Equipment type '{equipment_type}' not found. Using generic custom rates.")
            eq_entry = {"cost_per_day": cfg.get("equipment_cost_per_day", 150.0), "sell_per_day": cfg.get("equipment_sell_rate_per_day", 225.0), "cost_per_hour": 25.0, "sell_per_hour": 45.0}
        if equipment_days > 0:
            equipment_cost += equipment_days * float(eq_entry.get("cost_per_day", 150.0) or 0)
            equipment_sell += equipment_days * float(eq_entry.get("sell_per_day", 225.0) or 0)
        if equipment_hours > 0:
            equipment_cost += equipment_hours * float(eq_entry.get("cost_per_hour", 25.0) or 0)
            equipment_sell += equipment_hours * float(eq_entry.get("sell_per_hour", 45.0) or 0)

    # ===== Subcontract =====
    subcontract_cost = 0.0
    subcontract_sell = 0.0
    subcontracted = data.services_subcontracted if data.services_subcontracted is not None else bool(st_info.get("typically_subcontracted", False))
    markup_applies = data.services_subcontract_markup_applies if data.services_subcontract_markup_applies is not None else True
    if subcontracted and data.services_subcontract_cost:
        subcontract_cost = float(data.services_subcontract_cost or 0)
        markup_pct = float(cfg.get("subcontract_markup_percent", 20.0) or 0)
        if markup_applies:
            subcontract_sell = subcontract_cost * (1 + markup_pct / 100.0)
        else:
            subcontract_sell = subcontract_cost

    # ===== Permit / External pass-through =====
    permit_cost = float(data.services_permit_external_fee or 0)
    permit_sell = permit_cost  # default pass-through to sell

    # ===== Subtotal / overhead =====
    material_cost_total = travel_cost + equipment_cost + subcontract_cost + permit_cost  # non-labor direct costs
    # H-3: compute an hours-equivalent for overhead regardless of billing unit.
    # Hour-based units: use estimated_hours × workers (what the shop will actually spend).
    # Day billing:      days × configured day_hours.
    # Trip billing:     trips × 1h minimum + travel round-trip estimate (0 → 0 for hour-less work).
    # Mile billing:     one-way miles / 35mph as a rough drive-time contribution.
    # These give overhead something sensible to multiply against even on
    # pass-through-heavy categories without inflating non-labor jobs.
    hour_like_units = ("hour", "flat", "piece", "sqft", "linear_foot", "custom")
    day_hours = float(cfg.get("default_day_hours", 8) or 8)
    if billing_unit in hour_like_units:
        labor_hours_for_overhead = effective_hours * num_workers
    elif billing_unit == "day":
        labor_hours_for_overhead = float(qty_raw or 0) * day_hours * num_workers
    elif billing_unit == "trip":
        trips_total = max(int(data.services_trip_count or 1), int(qty_raw))
        labor_hours_for_overhead = trips_total * 1.0 * num_workers
    elif billing_unit == "mile":
        labor_hours_for_overhead = (travel_miles / 35.0) * num_workers if travel_miles else 0
    else:
        labor_hours_for_overhead = 0
    overhead_cost = calculate_overhead_cost(
        material_cost_total + labor_cost,
        labor_hours_for_overhead,
        defaults,
        cfg,
    )

    production_cost_total = labor_cost + material_cost_total + overhead_cost

    # ===== Suggested sell price =====
    sell_method = st_info.get("sell_method") or cfg.get("default_sell_method", "max_of_both")
    markup = float(cfg.get("default_markup_multiplier", 1.8) or 1.8)
    target_margin = float(cfg.get("target_profit_margin_percent", 35.0) or 35.0)

    # Cost-plus candidate.
    # Allocate a share of overhead to the labor portion proportional to labor's
    # share of the "allocable" cost base (everything except direct pass-through
    # costs — travel, equipment, subcontract, permit). When allocable_base is
    # zero (e.g. a pure pass-through job), keep all overhead on labor rather
    # than silently dropping it.
    non_allocable = travel_cost + equipment_cost + subcontract_cost + permit_cost
    allocable_base = production_cost_total - non_allocable
    if allocable_base > 0 and labor_cost > 0:
        labor_overhead_share = overhead_cost * (labor_cost / allocable_base)
    else:
        labor_overhead_share = overhead_cost
    cost_plus_labor_sell = resolve_selling_price(labor_cost + labor_overhead_share, markup, target_margin)

    # Baseline candidate (labor_sell_baseline already computed)
    if sell_method == "cost_plus":
        baseline_portion = cost_plus_labor_sell
    elif sell_method == "pass_through_plus_markup":
        baseline_portion = 0.0  # subcontract_sell carries the value
    elif sell_method == "max_of_both":
        baseline_portion = max(labor_sell_baseline, cost_plus_labor_sell)
    else:
        baseline_portion = labor_sell_baseline

    suggested_price = baseline_portion + travel_sell + equipment_sell + subcontract_sell + permit_sell

    # ===== Minimum charge floors =====
    # L-8: Explicit fallback chain. In priority order:
    #   1. services_minimum_override (set by user on this line item)
    #   2. st_info.default_minimum_charge (per-service-type override)
    #   3. cfg.default_minimum_sell_price (category-wide default)
    #   4. 25.0 hard floor (safety net so a missing/corrupt config doesn't zero out minimums)
    per_service_min = float(
        st_info.get("default_minimum_charge")
        or cfg.get("default_minimum_sell_price")
        or 25.0
    )
    min_override = float(data.services_minimum_override or 0)
    effective_min = min_override if min_override > 0 else per_service_min
    # Both the per-service minimum AND the global floor are gated by
    # `services_minimum_applies`. When a shop explicitly turns minimums off
    # (e.g. free consultation, relationship discount) neither floor should
    # silently re-inflate the quote.
    if minimum_applies:
        if effective_min > 0:
            suggested_price = max(suggested_price, effective_min)
        global_min = float(cfg.get("default_minimum_sell_price", 25.0) or 25.0)
        if global_min > 0:
            suggested_price = max(suggested_price, global_min)

    # ===== Rush =====
    # Spec: prefer Pricing Foundation rush default; fallback to services-specific rush_percent.
    # Use `is not None` so a tenant who explicitly sets foundation default_rush_percent=0
    # gets zero rush (not the 25% category fallback).
    foundation_rush_raw = defaults.get("default_rush_percent")
    services_rush_pct = float(cfg.get("rush_percent", 25.0) or 25.0)
    if foundation_rush_raw is not None:
        rush_pct = float(foundation_rush_raw or 0)
        rush_source = "foundation"
    else:
        rush_pct = services_rush_pct
        rush_source = "services_category"
    if data.rush_order:
        suggested_price = suggested_price * (1 + rush_pct / 100.0)

    # ===== Manual override =====
    # Precedence (highest-priority wins, applied last):
    #   1. services_manual_quote_override — Services-specific, set by the user
    #      on this line item.
    #   2. Generic price_override (data.override_enabled + data.price_override)
    #      — legacy category-agnostic override; applied FIRST so that the
    #      Services-specific field can still win when both are set.
    manual_override = None
    if data.override_enabled and data.price_override:
        suggested_price = float(data.price_override)
    if data.services_manual_quote_override and float(data.services_manual_quote_override) > 0:
        manual_override = float(data.services_manual_quote_override)
        suggested_price = manual_override

    # ===== Field provenance (shop_default / ai_estimated / user_entered) =====
    # M-1: AI provenance is trusted ONLY when the HMAC signature from the
    # /services-prefill endpoint verifies. Clients cannot forge "ai_estimated"
    # tags by hand-crafting ai_prefilled_fields — unsigned or invalid claims
    # silently downgrade to "user_entered".
    claimed_ai_fields = list(getattr(data, "ai_prefilled_fields", None) or [])
    signature = getattr(data, "ai_prefill_signature", None)
    tenant_id = getattr(data, "_tenant_id", "") or ""
    user_id = getattr(data, "_user_id", "") or ""
    ai_fields: set = set()
    if claimed_ai_fields and tenant_id and user_id:
        try:
            from routes.ai import verify_prefill_signature
            if verify_prefill_signature(tenant_id, user_id, claimed_ai_fields, signature):
                ai_fields = set(claimed_ai_fields)
        except Exception:
            # If verification throws for any reason, treat all claims as unsigned.
            ai_fields = set()
    def _src(attr: str, was_set: bool) -> str:
        if attr in ai_fields:
            return "ai_estimated"
        return "user_entered" if was_set else "shop_default"

    field_sources = {
        "service_type": _src("service_type", bool(data.service_type)),
        "billing_unit": _src("services_billing_unit", bool(data.services_billing_unit)),
        "labor_role": _src("services_labor_role", bool(data.services_labor_role)),
        "complexity": _src("services_complexity", bool(data.services_complexity)),
        "estimated_hours": _src("estimated_hours", bool(data.estimated_hours)),
        "flat_fee": _src("services_flat_fee", data.services_flat_fee is not None),
        "unit_rate": _src("services_unit_rate_override", data.services_unit_rate_override is not None),
        "minimum_applies": _src("services_minimum_applies", data.services_minimum_applies is not None),
        "minimum_override": _src("services_minimum_override", bool(data.services_minimum_override)),
        "travel_required": _src("services_travel_required", data.services_travel_required is not None),
        "travel_miles": _src("services_travel_miles", bool(data.services_travel_miles)),
        "trip_charge_applies": _src("services_trip_charge_applies", data.services_trip_charge_applies is not None),
        "trip_count": _src("services_trip_count", bool(data.services_trip_count)),
        "equipment_required": _src("services_equipment_required", data.services_equipment_required is not None),
        "equipment_type": _src("services_equipment_type", bool(data.services_equipment_type)),
        "equipment_days": _src("services_equipment_days", bool(data.services_equipment_days)),
        "subcontracted": _src("services_subcontracted", data.services_subcontracted is not None),
        "subcontract_cost": _src("services_subcontract_cost", bool(data.services_subcontract_cost)),
        "subcontract_markup_applies": _src("services_subcontract_markup_applies", data.services_subcontract_markup_applies is not None),
        "permit_cost": _src("services_permit_external_fee", bool(data.services_permit_external_fee)),
        "rush_order": _src("rush_order", bool(data.rush_order)),
        "manual_quote_override": _src("services_manual_quote_override", bool(data.services_manual_quote_override)),
        "rush_percent": rush_source,
    }

    return create_standardized_pricing_result(
        # === ITEMIZED COSTS (Phase 2D mapping) ===
        # Services has no physical materials; direct pass-through costs (travel,
        # equipment, subcontract, permits) go into outsourcing per spec. Labor
        # stays in labor.
        material_cost=0,
        labor_cost=labor_cost,
        design_cost=0,
        setup_cost=0,
        finishing_cost=0,
        hardware_cost=0,
        install_cost=0,
        outsourcing_cost=(travel_cost + equipment_cost + subcontract_cost + permit_cost),
        overhead_cost=overhead_cost,

        # === PRICING ===
        suggested_price=suggested_price,
        minimum_charge=effective_min if minimum_applies else 0,

        # === METADATA ===
        estimated_labor_minutes=round(labor_hours_for_overhead * 60, 0),
        pricing_method=(
            "manual_override"
            if (manual_override is not None) or (data.override_enabled and data.price_override)
            else sell_method
        ),
        markup_multiplier=markup,
        target_margin_percent=target_margin,

        # Overhead explainability (Phase 2D)
        overhead_basis={
            "formula": "(basis_amount * overhead_percentage / 100) + (labor_hours * shop_overhead_per_hour)",
            "basis_amount": round(material_cost_total + labor_cost, 2),
            "basis_components": [
                "labor_cost",
                "travel_cost",
                "equipment_cost",
                "subcontract_cost",
                "permit_cost",
            ],
            "labor_hours": round(labor_hours_for_overhead, 2),
            "labor_hours_source": (
                "estimated_hours × num_workers" if billing_unit in ("hour", "flat", "piece", "sqft", "linear_foot", "custom")
                else f"derived from billing_unit={billing_unit}"
            ),
            "overhead_percentage": float(
                cfg.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
            ),
            "shop_overhead_per_hour": float(
                cfg.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
            ),
            "overhead_excludes_setup_cost": True,
            "notes": (
                "Overhead is calculated from the legacy basis: labor_cost + travel_cost + "
                "equipment_cost + subcontract_cost + permit_cost. In the Phase 2D mapping the "
                "pass-through costs are exposed under outsourcing_cost, but overhead math is "
                "preserved exactly as pre-Phase-2D. labor_hours is derived per billing_unit "
                "(see labor_hours_source)."
            ),
        },

        # === BREAKDOWN ARRAYS ===
        labor_breakdown=([
            {
                "name": f"{(st_info.get('label') if st_info else st_key)} Labor ({labor_role})",
                "quantity": round(effective_hours * num_workers, 2) if billing_unit in ("hour", "flat", "piece", "sqft", "linear_foot", "custom") else round(labor_hours_for_overhead, 2),
                "unit": "hours",
                "unit_cost": labor_cost_rate,
                "total_cost": labor_cost,
                "notes": (
                    f"billing_unit={billing_unit}; complexity={complexity_key}×{complexity_mult}; "
                    f"workers={num_workers}"
                ),
            }
        ] if labor_cost > 0 else []),
        outsourcing_breakdown=(
            ([{
                "name": f"Travel ({travel_miles} mi)" if travel_miles > 0 else "Travel / Trip Charge",
                "quantity": travel_miles if travel_miles > 0 else trip_count,
                "unit": "miles" if travel_miles > 0 else "trips",
                "unit_cost": (
                    float(cfg.get("travel_cost_per_mile", 0.65) or 0)
                    if travel_miles > 0 else trip_cost_rate
                ),
                "total_cost": round(travel_cost, 2),
            }] if travel_cost > 0 else [])
            + ([{
                "name": f"Equipment Rental ({equipment_type})",
                "quantity": equipment_days or equipment_hours,
                "unit": "days" if equipment_days > 0 else "hours",
                "unit_cost": (
                    (equipment_cost / equipment_days) if equipment_days > 0
                    else (equipment_cost / equipment_hours if equipment_hours > 0 else equipment_cost)
                ),
                "total_cost": round(equipment_cost, 2),
            }] if equipment_cost > 0 else [])
            + ([{
                "name": "Subcontract / Vendor",
                "quantity": 1,
                "unit": "job",
                "unit_cost": round(subcontract_cost, 2),
                "total_cost": round(subcontract_cost, 2),
                "notes": f"markup_applies={markup_applies}",
            }] if subcontract_cost > 0 else [])
            + ([{
                "name": "Permits / External Fees",
                "quantity": 1,
                "unit": "job",
                "unit_cost": round(permit_cost, 2),
                "total_cost": round(permit_cost, 2),
            }] if permit_cost > 0 else [])
        ),

        # === METADATA FIELDS ===
        quantity=qty_raw,
        warnings=warnings,

        # === LEGACY BREAKDOWN (preserve all existing keys for backward compat) ===
        legacy_breakdown={
            "service_type": st_key,
            "service_type_label": st_info.get("label") if st_info else st_key,
            "billing_unit": billing_unit,
            "labor_role": labor_role,
            "labor_cost_rate": labor_cost_rate,
            "labor_sell_rate": labor_sell_rate,
            "complexity": complexity_key,
            "complexity_multiplier": complexity_mult,
            "effective_hours": round(effective_hours, 2),
            "num_workers": num_workers,
            "flat_fee": flat_fee,
            "unit_rate": unit_rate,
            "labor_cost": round(labor_cost, 2),
            "labor_sell_baseline": round(labor_sell_baseline, 2),
            "cost_plus_labor_sell": round(cost_plus_labor_sell, 2),
            "travel_required": bool(travel_required),
            "travel_miles": travel_miles,
            "travel_cost": round(travel_cost, 2),
            "travel_sell": round(travel_sell, 2),
            "trip_charge_applies": bool(trip_charge_applies),
            "trip_count": trip_count,
            "equipment_required": bool(equipment_required),
            "equipment_type": equipment_type if equipment_required else None,
            "equipment_days": equipment_days,
            "equipment_hours": equipment_hours,
            "equipment_cost": round(equipment_cost, 2),
            "equipment_sell": round(equipment_sell, 2),
            "subcontracted": bool(subcontracted),
            "subcontract_cost": round(subcontract_cost, 2),
            "subcontract_markup_applies": bool(markup_applies),
            "subcontract_sell": round(subcontract_sell, 2),
            "permit_cost": round(permit_cost, 2),
            "permit_sell": round(permit_sell, 2),
            "overhead_cost": round(overhead_cost, 2),
            "production_cost_total": round(production_cost_total, 2),
            "sell_method": sell_method,
            "per_service_min": per_service_min,
            "effective_min": effective_min,
            "minimum_applied": minimum_applies,
            "rush_percent_applied": rush_pct if data.rush_order else 0,
            "rush_percent_source": rush_source,
            "manual_quote_override": manual_override,
            # Spec-named totals (mirror existing fields for display convenience)
            "total_labor_cost": round(labor_cost, 2),
            "total_travel_cost": round(travel_cost, 2),
            "total_equipment_cost": round(equipment_cost, 2),
            "total_subcontract_cost": round(subcontract_cost, 2),
            "total_permit_cost": round(permit_cost, 2),
            "total_production_cost": round(production_cost_total, 2),
            # Phase 2D: legacy material_cost meaning preserved here (was travel+eq+sub+permit).
            "legacy_material_cost_total": round(material_cost_total, 2),
            "field_sources": field_sources,
        },
    )


async def calculate_custom(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate custom items using tenant cost settings."""
    category_config = get_category_pricing_config(defaults, "custom")
    material_cost_map = get_material_cost_map(defaults)
    unit_material_cost = data.unit_cost or material_cost_map.get("misc_material", 0)
    material_cost = unit_material_cost * quantity

    hourly_rate = data.hourly_rate_override or float(defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75)) or 0)
    labor_hours = data.estimated_hours or (float(category_config.get("default_labor_hours_per_unit", 0.25) or 0.25) * quantity)
    labor_cost = labor_hours * hourly_rate

    pre_overhead_total = material_cost + labor_cost
    overhead_cost = calculate_overhead_cost(pre_overhead_total, labor_hours, defaults, category_config)
    markup_percent = data.markup_percent if data.markup_percent is not None else None
    markup_multiplier = (1 + (markup_percent / 100)) if markup_percent is not None else category_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5))
    suggested_price = resolve_selling_price(
        pre_overhead_total + overhead_cost,
        markup_multiplier,
        category_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40.0)),
    )

    custom_price = data.price_override if data.override_enabled else None
    manual_override_used = False
    if custom_price:
        suggested_price = custom_price * quantity
        manual_override_used = True

    minimum_charge = float(category_config.get("minimum_charge", defaults.get("minimum_order", 0)) or 0)
    suggested_price = max(suggested_price, minimum_charge)
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order)

    # ============== PHASE 2D: USE STANDARDIZED RESPONSE ==============
    # Custom is a simple cost-plus (or manual-override) model.
    # Overhead math basis is preserved from legacy: material_cost + labor_cost.
    materials_list = []
    if material_cost > 0:
        materials_list.append({
            "name": "Custom Item Material",
            "quantity": quantity,
            "unit": "each",
            "unit_cost": unit_material_cost,
            "total_cost": material_cost,
        })

    labor_list = []
    if labor_cost > 0:
        labor_list.append({
            "name": "Custom Labor",
            "quantity": labor_hours,
            "unit": "hours",
            "unit_cost": hourly_rate,
            "total_cost": labor_cost,
        })

    return create_standardized_pricing_result(
        # Costs (itemized by type)
        material_cost=material_cost,
        labor_cost=labor_cost,
        design_cost=0,
        setup_cost=0,
        finishing_cost=0,
        hardware_cost=0,
        install_cost=0,
        outsourcing_cost=0,
        overhead_cost=overhead_cost,

        # Pricing
        suggested_price=suggested_price,
        minimum_charge=minimum_charge,

        # Metadata
        estimated_labor_minutes=labor_hours * 60,
        pricing_method=("manual_override" if manual_override_used else "markup"),
        markup_multiplier=float(markup_multiplier or 1.0),
        target_margin_percent=float(
            category_config.get(
                "target_profit_margin_percent",
                defaults.get("target_profit_margin_percent", 40.0),
            ) or 0
        ),

        # Overhead explainability (Phase 2D)
        overhead_basis={
            "formula": "(basis_amount * overhead_percentage / 100) + (labor_hours * shop_overhead_per_hour)",
            "basis_amount": round(pre_overhead_total, 2),
            "basis_components": [
                "material_cost",
                "labor_cost",
            ],
            "labor_hours": round(labor_hours, 2),
            "overhead_percentage": float(
                category_config.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
            ),
            "shop_overhead_per_hour": float(
                category_config.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
            ),
            "overhead_excludes_setup_cost": True,
            "notes": (
                "Overhead is calculated from the legacy basis: material_cost + labor_cost. "
                "When manual price override is enabled, the selling_price is the override value "
                "(× quantity) and overhead is still computed on this basis for cost reporting only."
            ),
        },

        # Breakdown arrays
        materials_breakdown=materials_list,
        labor_breakdown=labor_list,

        # Metadata fields
        quantity=quantity,
        warnings=[],

        # Legacy breakdown (preserve existing keys for backward compat)
        legacy_breakdown={
            "custom_item": True,
            "labor_hours": labor_hours,
            "hourly_rate": hourly_rate,
            "overhead_cost": round(overhead_cost, 2),
            "manual_override_used": manual_override_used,
            "override_enabled": bool(data.override_enabled),
            "price_override": data.price_override,
            "override_unit_price": (custom_price if manual_override_used else None),
            "markup_multiplier": float(markup_multiplier or 1.0),
            "markup_percent_input": data.markup_percent,
            "minimum_charge": minimum_charge,
            "rush_order": bool(data.rush_order),
        },
    )


async def calculate_apparel(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate Apparel pricing using Pricing Foundation defaults.

    Flow:
      1. Resolve product type, brand/style, placement set, decoration method
      2. Determine quantity tier
      3. For "shop_table" methods: pull per-piece suggested sell from the foundation table
         For non-table methods: cost-plus using per-method config (setup + material + labor)
      4. Add plus-size upcharges, custom names/numbers, specialty finish, patch, bag-and-fold
      5. Add setup/design fees based on artwork state and complexity
      6. Multiply by quantity, apply rush, enforce minimum
      7. Calculate blank + decoration material + labor costs + overhead for margin reporting
    """
    cfg = get_category_pricing_config(defaults, "apparel")

    # ===== Resolve inputs =====
    product_types = cfg.get("available_product_types", []) or []
    product_type_key = data.apparel_product_type or (product_types[0]["key"] if product_types else "short_sleeve_tee")
    product_type_info = next((p for p in product_types if p.get("key") == product_type_key), None) or {}
    is_hat = bool(product_type_info.get("is_hat", False))
    placement_set_kind = product_type_info.get("allowed_placement_set", "garment")

    # Default brand/style = first in brand list for the product type
    brand_styles = (cfg.get("available_brand_styles", {}) or {}).get(product_type_key, []) or []
    brand_key = data.apparel_brand_style_key or (brand_styles[0]["key"] if brand_styles else "")

    # Default placement: garment -> front; hat -> front
    placement_key = data.apparel_placement_set or "front"

    # Decoration method
    avail_methods = cfg.get("available_decoration_methods", ["htv"])
    method_key = data.apparel_decoration_method or cfg.get("default_decoration_method", "htv")
    if method_key not in avail_methods:
        method_key = "htv"

    method_cfg = (cfg.get("method_config", {}) or {}).get(method_key, {}) or {}
    uses_shop_table = method_key in (cfg.get("methods_using_shop_table", []) or []) and bool(method_cfg.get("uses_shop_table", False))

    # ===== Quantity derivation =====
    # Apparel uses summed size breakdown (already handled upstream in _derive_ticket_quantity);
    # here we trust `quantity` as total pieces.
    qty = max(int(round(quantity or 1)), 1)

    # ===== Tier resolution =====
    tiers = cfg.get("quantity_tiers", []) or []
    tier_key = "1_4"
    for t in tiers:
        min_q = int(t.get("min_qty", 0) or 0)
        max_q = t.get("max_qty")
        if qty >= min_q and (max_q is None or qty <= int(max_q)):
            tier_key = t.get("key", "1_4")
            break

    # ===== Blank cost =====
    blank_material = find_material(defaults, brand_key) if brand_key else None
    blank_cost_per_piece = float((blank_material or {}).get("cost_per_unit", 0) or 0)
    if data.blank_cost_override is not None:
        blank_cost_per_piece = float(data.blank_cost_override)
    # Customer-supplied garments -> blank cost is 0 (specs flag handled by setting apparel_brand_style_key to None and override to 0)
    total_blank_cost = blank_cost_per_piece * qty

    # ===== Suggested per-piece sell price =====
    warning = ""
    shop_table = cfg.get("shop_pricing_table", {}) or {}
    per_piece_sell = 0.0
    baseline_source = ""

    if uses_shop_table and brand_key and tier_key and placement_key:
        tier_row = (shop_table.get(brand_key, {}) or {}).get(tier_key, {}) or {}
        per_piece_sell = float(tier_row.get(placement_key, 0) or 0)
        if per_piece_sell > 0:
            baseline_source = f"shop_table:{method_key}"
        else:
            warning = f"Shop table missing row for {brand_key} / {tier_key} / {placement_key}. Falling back to cost-plus."

    if per_piece_sell <= 0:
        # Cost-plus fallback for non-table methods or missing table rows
        setup_fee_per_piece_amortized = 0.0
        setup_fee_flat = float(method_cfg.get("default_setup_fee", cfg.get("default_setup_fee", 10.0)) or 0)
        material_cost = 0.0
        if "material_cost_per_color_per_piece" in method_cfg:
            num_colors = int(data.apparel_num_colors or 1)
            material_cost = float(method_cfg["material_cost_per_color_per_piece"] or 0) * max(num_colors, 1)
        elif "material_cost_per_piece" in method_cfg:
            material_cost = float(method_cfg["material_cost_per_piece"] or 0)
        elif "cost_per_1k_stitches" in method_cfg:
            stitch_count = int(data.apparel_stitch_count or method_cfg.get("default_stitch_count", 6000))
            material_cost = float(method_cfg["cost_per_1k_stitches"] or 0) * (stitch_count / 1000.0)
        elif "material_cost_per_sqin" in method_cfg:
            # Rough default sq in per print
            material_cost = float(method_cfg["material_cost_per_sqin"] or 0) * 80.0
        # amortize setup over quantity
        if qty > 0:
            setup_fee_per_piece_amortized = setup_fee_flat / qty
        # add production labor (minutes)
        labor_minutes = float(cfg.get("apparel_labor_minutes_per_piece", 1.5) or 1.5)
        labor_rates = defaults.get("labor_rates", {}) or {}
        prod_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", 28)) or 28)
        labor_cost_per_piece = (labor_minutes / 60.0) * prod_rate
        cost_per_piece = blank_cost_per_piece + material_cost + labor_cost_per_piece + setup_fee_per_piece_amortized
        # Apply category markup + min
        markup = float(cfg.get("default_markup_multiplier", 2.15) or 2.15)
        per_piece_sell = max(cost_per_piece * markup, float(method_cfg.get("min_sell_per_piece", cfg.get("default_minimum_sell_price", 10.0)) or 10.0))
        baseline_source = f"cost_plus:{method_key}"

    # Retail base floor (no-print retail value acts as an absolute minimum sell per piece)
    retail_base = float((blank_material or {}).get("retail_base_no_print", 0) or 0)
    if retail_base > 0:
        per_piece_sell = max(per_piece_sell, retail_base)

    # Base decoration sell = per-piece × qty
    decoration_sell = per_piece_sell * qty
    # Suggested price starts at blanks + decoration IF using shop table (table already includes blank markup);
    # for cost-plus baseline, blanks are already in cost_per_piece.
    if uses_shop_table and baseline_source.startswith("shop_table"):
        suggested_price = decoration_sell
    else:
        suggested_price = decoration_sell  # already includes blank via cost_per_piece

    # ===== Add-ons =====
    plus_size_count = int(data.apparel_plus_size_count or 0)
    plus_size_rate = float(cfg.get("plus_size_upcharge_per_x", 2.0) or 0)
    plus_size_cost = 0.0
    if not is_hat:
        plus_size_cost = plus_size_count * plus_size_rate
    suggested_price += plus_size_cost

    custom_nn_count = int(data.apparel_custom_name_number_count or 0)
    if data.apparel_custom_name_number:
        nn_rate = float(cfg.get("custom_name_number_hat", 3.0) if is_hat else cfg.get("custom_name_number_garment", 4.0))
        custom_nn_cost = nn_rate * custom_nn_count
    else:
        custom_nn_cost = 0.0
    suggested_price += custom_nn_cost

    specialty_cost = 0.0
    if data.apparel_specialty_finish:
        rate = float(cfg.get("specialty_vinyl_hat", 1.5) if is_hat else cfg.get("specialty_finish_garment", 2.0))
        specialty_cost = rate * qty
    suggested_price += specialty_cost

    two_tone_cost = 0.0
    if is_hat and data.apparel_two_tone_hat_finish:
        two_tone_cost = float(cfg.get("two_tone_hat_finish", 1.5) or 0) * qty
    suggested_price += two_tone_cost

    patch_cost = 0.0
    if is_hat and data.apparel_leather_patch:
        patch_cost = float(cfg.get("leather_patch_hat", 2.5) or 0) * qty
    suggested_price += patch_cost

    bag_fold_cost = 0.0
    if data.apparel_bag_and_fold:
        bag_fold_cost = float(cfg.get("bag_and_fold_each", 1.0) or 0) * qty
    suggested_price += bag_fold_cost

    # ===== Setup / Design =====
    setup_fee = 0.0
    complexity_key = (data.design_complexity or cfg.get("default_design_complexity", "simple")).lower()
    artwork_ready = bool(data.artwork_ready)
    artwork_needed = data.artwork_needed
    if artwork_needed is None:
        artwork_needed = bool(cfg.get("default_artwork_needed", False))
    if not artwork_ready and artwork_needed:
        setup_fees = cfg.get("design_complexity_setup_fees", {}) or {}
        setup_fee = float(setup_fees.get(complexity_key, cfg.get("default_setup_fee", 10.0)) or 10.0)
    # Method-specific setup (only when cost-plus path didn't already amortize it)
    method_setup = 0.0
    if uses_shop_table:
        method_setup = float(method_cfg.get("default_setup_fee", 0) or 0)
        # Shop-table sells often already include minor setup; only add method_setup when not amortized.
        # We keep it additive for transparency (conservative). Can be toggled off by admin via method_config.
        if method_setup > 0 and not method_cfg.get("setup_included_in_table", True):
            setup_fee += method_setup
    suggested_price += setup_fee

    # ===== Rush =====
    rush_percent = float(data.apparel_rush_percent if data.apparel_rush_percent is not None else cfg.get("default_rush_percent", 17.5))
    if data.rush_order:
        suggested_price = suggested_price * (1 + rush_percent / 100.0)

    # ===== Minimum sell per item × qty =====
    min_sell_per_piece = float(cfg.get("default_minimum_sell_price", 10.0) or 10.0)
    suggested_price = max(suggested_price, min_sell_per_piece * qty)

    # ===== Manual override =====
    manual_override = None
    if data.apparel_manual_quote_override is not None and float(data.apparel_manual_quote_override) > 0:
        manual_override = float(data.apparel_manual_quote_override)
        suggested_price = manual_override  # user's manual override takes precedence for display totals
    if data.override_enabled and data.price_override:
        suggested_price = float(data.price_override) * qty

    # ===== Cost tracking (blank cost + decoration material + labor + overhead) =====
    # Decoration material cost per piece (based on method)
    decoration_material_per_piece = 0.0
    if "material_cost_per_color_per_piece" in method_cfg:
        num_colors = int(data.apparel_num_colors or 1)
        decoration_material_per_piece = float(method_cfg["material_cost_per_color_per_piece"] or 0) * max(num_colors, 1)
    elif "material_cost_per_piece" in method_cfg:
        decoration_material_per_piece = float(method_cfg["material_cost_per_piece"] or 0)
    elif "cost_per_1k_stitches" in method_cfg:
        stitch_count = int(data.apparel_stitch_count or method_cfg.get("default_stitch_count", 6000))
        decoration_material_per_piece = float(method_cfg["cost_per_1k_stitches"] or 0) * (stitch_count / 1000.0)
    elif "material_cost_per_sqin" in method_cfg:
        decoration_material_per_piece = float(method_cfg["material_cost_per_sqin"] or 0) * 80.0
    total_decoration_material_cost = decoration_material_per_piece * qty

    # ===== LABOR CALCULATION (PRODUCTION + DESIGN) =====
    labor_rates = defaults.get("labor_rates", {}) or {}
    prod_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", 28)) or 28)
    
    # Try new minute-based system via apparel helper
    labor_minutes = get_apparel_labor_minutes(defaults, cfg, qty)
    if labor_minutes > 0:
        # Use new minute-based labor calculation
        labor_hours = labor_minutes / 60.0
        labor_cost_total = labor_hours * prod_rate
        # For breakdown compatibility (used below)
        labor_minutes_per_piece = labor_minutes / qty if qty > 0 else 0
    else:
        # Fallback to old per-piece calculation
        labor_minutes_per_piece = float(cfg.get("apparel_labor_minutes_per_piece", 1.5) or 1.5) + float(cfg.get("apparel_handling_labor_minutes_per_piece", 0.5) or 0.5)
        labor_hours = (labor_minutes_per_piece * qty) / 60.0
        labor_cost_total = labor_hours * prod_rate

    # ===== DESIGN CHARGE =====
    charge_separately, default_design_rate, included_minutes = get_design_charge_config(defaults)
    design_cost = 0.0
    design_hours = 0.0
    
    if not artwork_ready and artwork_needed:
        # Calculate design time
        design_hours = float({"simple": 0.25, "medium": 0.5, "complex": 1.0, "extreme": 1.5}.get(complexity_key, 0.25))
        
        # Apply new design charge logic
        if charge_separately == "no":
            design_cost = 0  # Design included in price, not charged separately
        else:
            # Deduct included minutes before charging
            design_minutes = design_hours * 60
            billable_design_minutes = max(0, design_minutes - included_minutes)
            billable_design_hours = billable_design_minutes / 60.0
            design_cost = billable_design_hours * default_design_rate
        
        labor_hours += design_hours
    labor_cost_total += design_cost

    material_cost_total = total_blank_cost + total_decoration_material_cost
    overhead_cost = calculate_overhead_cost(
        material_cost_total + labor_cost_total,
        labor_hours,
        defaults,
        cfg,
    )

    return create_standardized_pricing_result(
        # === ITEMIZED COSTS (Phase 2D mapping) ===
        # Blanks → materials
        # Decoration consumable (HTV/DTG/screen ink/embroidery thread) + per-piece
        # add-on upcharges (plus-size, custom name/number, specialty finish,
        # two-tone, leather patch, bag-and-fold) → finishing.
        # NOTE on add-ons: legacy create_pricing_result accepted these as
        # `additional_costs` and added them to production_cost. To preserve
        # production_cost (= true_cost) and profit_amount EXACTLY, they must
        # stay inside base_cost. They sit in `finishing` here for clarity since
        # they all relate to garment decoration/finishing.
        # Production labor → labor; design labor → design; setup fee → setup.
        # Overhead basis stays exactly as legacy: material_cost_total +
        # labor_cost_total (blanks + decoration_material + production_labor +
        # design_cost). Setup fee and per-piece add-ons are intentionally
        # excluded from the overhead basis to preserve pre-Phase-2D math.
        material_cost=total_blank_cost,
        labor_cost=(labor_cost_total - design_cost),  # production labor only
        design_cost=design_cost,
        setup_cost=setup_fee,
        finishing_cost=(
            total_decoration_material_cost
            + plus_size_cost
            + custom_nn_cost
            + specialty_cost
            + two_tone_cost
            + patch_cost
            + bag_fold_cost
        ),
        hardware_cost=0,
        install_cost=0,
        outsourcing_cost=0,
        overhead_cost=overhead_cost,

        # === PRICING ===
        suggested_price=suggested_price,
        minimum_charge=min_sell_per_piece * qty,

        # === METADATA ===
        estimated_labor_minutes=labor_hours * 60,
        pricing_method=(
            "manual_override"
            if (manual_override is not None) or (data.override_enabled and data.price_override)
            else baseline_source or "cost_plus"
        ),
        markup_multiplier=float(cfg.get("default_markup_multiplier", 2.15) or 2.15),
        target_margin_percent=float(cfg.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 0)) or 0),

        # Overhead explainability (Phase 2D)
        overhead_basis={
            "formula": "(basis_amount * overhead_percentage / 100) + (labor_hours * shop_overhead_per_hour)",
            "basis_amount": round(material_cost_total + labor_cost_total, 2),
            "basis_components": [
                "total_blank_cost",
                "total_decoration_material_cost",
                "production_labor_cost",
                "design_cost",
            ],
            "labor_hours": round(labor_hours, 2),
            "labor_hours_components": [
                "production_labor_hours",
                "design_hours (when artwork not ready)",
            ],
            "overhead_percentage": float(
                cfg.get("overhead_percentage", defaults.get("overhead_percentage", 0)) or 0
            ),
            "shop_overhead_per_hour": float(
                cfg.get("shop_overhead_per_hour", defaults.get("shop_overhead_per_hour", 0)) or 0
            ),
            "overhead_excludes_setup_cost": True,
            "notes": (
                "Overhead is calculated from the legacy basis: blanks + decoration material + "
                "production labor + design labor. setup_fee AND per-piece add-on upcharges "
                "(plus_size, custom_name_number, specialty_finish, two_tone, leather_patch, "
                "bag_and_fold) are intentionally excluded from the overhead basis to preserve "
                "pre-Phase-2D math. The add-ons remain inside base_cost (mapped to "
                "finishing_cost) so production_cost and profit_amount equal legacy values."
            ),
        },

        # === BREAKDOWN ARRAYS ===
        materials_breakdown=(
            [{
                "name": ((blank_material or {}).get("name") or brand_key or "Blank Garment"),
                "quantity": qty,
                "unit": "each",
                "unit_cost": round(blank_cost_per_piece, 2),
                "total_cost": round(total_blank_cost, 2),
            }] if total_blank_cost > 0 else []
        ),
        labor_breakdown=(
            [{
                "name": "Production / Pressing Labor",
                "quantity": round((labor_minutes_per_piece * qty) / 60.0, 2),
                "unit": "hours",
                "unit_cost": prod_rate,
                "total_cost": round(labor_cost_total - design_cost, 2),
            }] if (labor_cost_total - design_cost) > 0 else []
        ),
        design_breakdown=(
            [{
                "name": "Design / Artwork",
                "quantity": round(labor_hours - ((labor_minutes_per_piece * qty) / 60.0), 2) if design_cost > 0 else 0,
                "unit": "hours",
                "unit_cost": float(labor_rates.get("design", {}).get("hourly_rate", defaults.get("design_hourly_rate", 85)) or 85),
                "total_cost": round(design_cost, 2),
            }] if design_cost > 0 else []
        ),
        setup_breakdown=(
            [{
                "name": "Apparel Setup Fee",
                "quantity": 1,
                "unit": "job",
                "unit_cost": round(setup_fee, 2),
                "total_cost": round(setup_fee, 2),
            }] if setup_fee > 0 else []
        ),
        finishing_breakdown=(
            ([{
                "name": f"Decoration Consumable ({method_key})",
                "quantity": qty,
                "unit": "each",
                "unit_cost": round(decoration_material_per_piece, 2),
                "total_cost": round(total_decoration_material_cost, 2),
            }] if total_decoration_material_cost > 0 else [])
            + ([{
                "name": "Plus-Size Upcharge",
                "quantity": plus_size_count,
                "unit": "piece",
                "unit_cost": round(plus_size_rate, 2),
                "total_cost": round(plus_size_cost, 2),
            }] if plus_size_cost > 0 else [])
            + ([{
                "name": "Custom Name/Number",
                "quantity": custom_nn_count,
                "unit": "piece",
                "unit_cost": round(custom_nn_cost / custom_nn_count, 2) if custom_nn_count > 0 else 0,
                "total_cost": round(custom_nn_cost, 2),
            }] if custom_nn_cost > 0 else [])
            + ([{
                "name": "Specialty Finish",
                "quantity": qty,
                "unit": "piece",
                "unit_cost": round(specialty_cost / qty, 2) if qty > 0 else 0,
                "total_cost": round(specialty_cost, 2),
            }] if specialty_cost > 0 else [])
            + ([{
                "name": "Two-Tone Hat Finish",
                "quantity": qty,
                "unit": "piece",
                "unit_cost": round(two_tone_cost / qty, 2) if qty > 0 else 0,
                "total_cost": round(two_tone_cost, 2),
            }] if two_tone_cost > 0 else [])
            + ([{
                "name": "Leather Patch",
                "quantity": qty,
                "unit": "piece",
                "unit_cost": round(patch_cost / qty, 2) if qty > 0 else 0,
                "total_cost": round(patch_cost, 2),
            }] if patch_cost > 0 else [])
            + ([{
                "name": "Bag & Fold",
                "quantity": qty,
                "unit": "piece",
                "unit_cost": round(bag_fold_cost / qty, 2) if qty > 0 else 0,
                "total_cost": round(bag_fold_cost, 2),
            }] if bag_fold_cost > 0 else [])
        ),

        # === METADATA FIELDS ===
        quantity=qty,
        warnings=([warning] if warning else []),

        # === LEGACY BREAKDOWN (preserve all existing keys) ===
        legacy_breakdown={
            "product_type": product_type_key,
            "is_hat": is_hat,
            "brand_style_key": brand_key,
            "brand_label": (blank_material or {}).get("name") if blank_material else None,
            "placement_set": placement_key,
            "placement_kind": placement_set_kind,
            "decoration_method": method_key,
            "decoration_subtype": data.apparel_decoration_subtype,
            "method_label": method_cfg.get("label", method_key),
            "uses_shop_table": uses_shop_table,
            "baseline_source": baseline_source,
            "shop_table_warning": warning,
            "quantity_tier": tier_key,
            "per_piece_sell": round(per_piece_sell, 2),
            "blank_cost_per_piece": round(blank_cost_per_piece, 2),
            "retail_base_no_print": retail_base,
            "total_blank_cost": round(total_blank_cost, 2),
            "decoration_material_per_piece": round(decoration_material_per_piece, 2),
            "total_decoration_material_cost": round(total_decoration_material_cost, 2),
            "plus_size_count": plus_size_count,
            "plus_size_cost": round(plus_size_cost, 2),
            "custom_name_number": bool(data.apparel_custom_name_number),
            "custom_name_number_count": custom_nn_count,
            "custom_name_number_cost": round(custom_nn_cost, 2),
            "specialty_finish": bool(data.apparel_specialty_finish),
            "specialty_cost": round(specialty_cost, 2),
            "two_tone_hat_finish": bool(data.apparel_two_tone_hat_finish),
            "two_tone_cost": round(two_tone_cost, 2),
            "leather_patch": bool(data.apparel_leather_patch),
            "patch_cost": round(patch_cost, 2),
            "bag_and_fold": bool(data.apparel_bag_and_fold),
            "bag_fold_cost": round(bag_fold_cost, 2),
            "artwork_ready": artwork_ready,
            "artwork_needed": artwork_needed,
            "design_complexity": complexity_key,
            "setup_fee": round(setup_fee, 2),
            "design_cost": round(design_cost, 2),
            "num_colors": int(data.apparel_num_colors or 1),
            "stitch_count": int(data.apparel_stitch_count or 0),
            "labor_hours": round(labor_hours, 2),
            "labor_cost_total": round(labor_cost_total, 2),
            "rush_percent_applied": round(rush_percent, 2) if data.rush_order else 0,
            "manual_quote_override": manual_override,
            "min_sell_per_piece": min_sell_per_piece,
            # Phase 2D: preserve legacy aggregate values (additional_costs was
            # the sum of all the per-piece add-on upcharges).
            "legacy_material_cost_total": round(material_cost_total, 2),
            "legacy_labor_cost_total": round(labor_cost_total, 2),
            "legacy_additional_costs": round(
                plus_size_cost + custom_nn_cost + specialty_cost
                + two_tone_cost + patch_cost + bag_fold_cost, 2
            ),
        },
    )


async def calculate_pricing(
    category: PricingCategory,
    data: JobItemPricingData,
    quantity: float,
    tenant_id: str,
    user_id: Optional[str] = None,
) -> PricingCalculation:
    """Main pricing calculation dispatcher"""
    defaults = await get_pricing_defaults(tenant_id)
    
    calculators = {
        PricingCategory.PROMOTIONAL: calculate_promotional,
        PricingCategory.CUT_VINYL: calculate_cut_vinyl,
        PricingCategory.SERVICES: calculate_services,
        PricingCategory.DIGITAL_PRINT: calculate_digital_print,
        PricingCategory.RIGID_SIGNS: calculate_rigid_signs,
        PricingCategory.BANNERS: calculate_banners,
        PricingCategory.APPAREL: calculate_apparel,
        PricingCategory.VEHICLE_GRAPHICS: calculate_vehicle_graphics,
        PricingCategory.CUSTOM: calculate_custom,
    }
    
    calculator = calculators.get(category, calculate_custom)
    # Only Services needs user_id (for AI-prefill signature verification).
    # Pass it via a keyword-only attribute on the pricing_data so we don't
    # have to change the signature of every other calculator.
    if category == PricingCategory.SERVICES:
        setattr(data, "_tenant_id", tenant_id)
        setattr(data, "_user_id", user_id or "")
    return await calculator(data, quantity, defaults)


# ============== BASIC ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "SignGuy AI API", "version": "1.0.0"}


@api_router.get("/health")
async def health():
    return {"status": "healthy"}


# ============== TENANT ROUTES ==============

@api_router.get("/tenant")
async def get_tenant_info(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user's tenant information (excludes large logo data)"""
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0, "logo_url": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    # Add a lightweight flag so frontend knows whether a logo exists
    logo_check = await db.tenants.find_one(
        {"id": current_user.tenant_id, "logo_url": {"$ne": None}},
        {"_id": 0, "id": 1}
    )
    tenant["has_logo"] = logo_check is not None
    return tenant


@api_router.get("/tenant/logo")
async def get_tenant_logo(current_user: UserInDB = Depends(get_current_active_user)):
    """Get tenant logo data separately (can be large base64)"""
    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0, "logo_url": 1}
    )
    if not tenant or not tenant.get("logo_url"):
        return {"logo_url": None}
    return {"logo_url": tenant["logo_url"]}


@api_router.put("/tenant")
async def update_tenant_info(
    update_data: TenantUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update current user's tenant information"""
    # Only owners can update tenant settings
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can update tenant settings")
    
    update_dict = {}
    for k, v in update_data.model_dump().items():
        if v is not None:
            # Handle nested Pydantic models
            if hasattr(v, 'model_dump'):
                update_dict[k] = v.model_dump()
            else:
                update_dict[k] = v
    
    if update_dict:
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        await db.tenants.update_one(
            {"id": current_user.tenant_id},
            {"$set": update_dict}
        )
    
    # Return updated tenant (exclude large logo data)
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0, "logo_url": 0})
    logo_check = await db.tenants.find_one(
        {"id": current_user.tenant_id, "logo_url": {"$ne": None}},
        {"_id": 0, "id": 1}
    )
    tenant["has_logo"] = logo_check is not None
    return tenant


@api_router.post("/tenant/upload-logo")
async def upload_tenant_logo(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Upload a logo image for the tenant/company"""
    # Only owners can upload logo
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can upload company logo")
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif", "image/svg+xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Allowed: PNG, JPEG, WebP, GIF, SVG"
        )
    
    # Read file contents
    contents = await file.read()
    
    # Check file size (max 3MB)
    if len(contents) > 3 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 3MB")
    
    # Convert to base64 data URL
    base64_encoded = base64.b64encode(contents).decode('utf-8')
    logo_data_url = f"data:{file.content_type};base64,{base64_encoded}"
    
    # Update tenant with logo
    await db.tenants.update_one(
        {"id": current_user.tenant_id},
        {"$set": {
            "logo_url": logo_data_url,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Logo uploaded for tenant {current_user.tenant_id}")
    
    return {"message": "Logo uploaded successfully", "logo_url": logo_data_url}


@api_router.delete("/tenant/logo")
async def delete_tenant_logo(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Remove the tenant/company logo"""
    # Only owners can delete logo
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete company logo")
    
    # Remove logo from tenant
    await db.tenants.update_one(
        {"id": current_user.tenant_id},
        {"$set": {
            "logo_url": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Logo deleted for tenant {current_user.tenant_id}")
    
    return {"message": "Logo deleted successfully"}


# ============== IMPORT AND INCLUDE ROUTERS ==============
from routes.auth import router as auth_router, users_router, admin_router
from routes.customers import router as customers_router
from routes.quotes import router as quotes_router
from routes.magic_links import router as magic_links_router, preview_router as magic_link_preview_router
from routes.jobs import router as jobs_router, job_items_router, job_notes_router
from routes.invoices import router as invoices_router
from routes.employees import employees_router, timeclock_router, payroll_router
from routes.pricing import router as pricing_router
from routes.portal import router as portal_router
from routes.webstores import webstores_router, products_router, storefront_router
from routes.tiers import router as tiers_router
from routes.billing import router as billing_router, webhook_router
from routes.dashboard import router as dashboard_router
from routes.tasks import router as tasks_router
from routes.employee_portal import router as employee_portal_router
from routes.ai import router as ai_router
from routes.ai_assistant_prefs import router as ai_assistant_prefs_router
from routes.job_time import router as job_time_router
from routes.promo_codes import router as promo_codes_router
from routes.approvals import router as approvals_router
from routes.documents import router as documents_router
from routes.email_templates import router as email_templates_router
from routes.admin_portal import router as admin_portal_router
from routes.production_timeline import router as production_timeline_router
from routes.stripe_connect import router as stripe_connect_router
from routes.webstore_owners import router as webstore_owners_router, public_router as webstore_owner_public_router, portal_router as webstore_owner_portal_router
from routes.plans import router as plans_router
from routes.questionnaires import router as questionnaires_router
from routes.credits import router as credits_router
from routes.dev import router as dev_router
from routes.pricing_setup import router as pricing_setup_router
from routes.profit_analytics import router as profit_analytics_router, financials_router
from routes.admin_analytics import router as admin_analytics_router
from routes.onboarding import router as onboarding_router
from routes.orders import router as shop_orders_router
from routes.job_tickets import router as job_tickets_router
from routes.production_tasks import router as production_tasks_router
from routes.workflow_templates import router as workflow_templates_router
from routes.digest import router as digest_router
from routes.order_drawings import router as order_drawings_router
from routes.signatures import router as signatures_router
from routes.productivity import router as productivity_router
from routes.appointments import router as appointments_router, public_router as appointments_public_router
from routes.meta_integration import router as meta_integration_router
from routes.facebook_messages import router as facebook_messages_router
from routes.wrap import router as wrap_router
from routes.inventory import router as inventory_router
from routes.public_website import router as public_website_router

# Platform Admin
from routes.platform_admin import router as platform_admin_router
from routes.platform_settings import (
    public_router as platform_settings_public_router,
    admin_router as platform_settings_admin_router,
)
from routes.email_deliverability import (
    router as email_deliverability_router,
    sendgrid_webhook_router,
)
from routes.sms import router as sms_router

# Include all routers in the api_router
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)
api_router.include_router(customers_router)
api_router.include_router(quotes_router)
api_router.include_router(magic_links_router)
api_router.include_router(magic_link_preview_router)
api_router.include_router(jobs_router)
api_router.include_router(job_items_router)
api_router.include_router(job_notes_router)
api_router.include_router(invoices_router)
api_router.include_router(employees_router)
api_router.include_router(timeclock_router)
api_router.include_router(payroll_router)
api_router.include_router(pricing_router)
api_router.include_router(portal_router)
api_router.include_router(webstores_router)
api_router.include_router(products_router)
api_router.include_router(storefront_router)  # Public storefront routes
api_router.include_router(tiers_router)
api_router.include_router(billing_router)
api_router.include_router(webhook_router)
api_router.include_router(dashboard_router)
api_router.include_router(tasks_router)
api_router.include_router(employee_portal_router)
api_router.include_router(ai_router)
api_router.include_router(ai_assistant_prefs_router)
api_router.include_router(job_time_router)
api_router.include_router(promo_codes_router)
api_router.include_router(approvals_router)
api_router.include_router(documents_router)
api_router.include_router(email_templates_router)
api_router.include_router(stripe_connect_router)
api_router.include_router(webstore_owners_router)
api_router.include_router(webstore_owner_public_router)
api_router.include_router(webstore_owner_portal_router)

# Assistant tool-calling subsystem (commit endpoints — extracted Feb 2026)
from routes.assistant_tools import router as assistant_tools_router  # noqa: E402
api_router.include_router(assistant_tools_router)
api_router.include_router(plans_router)  # Multi-product plan management
api_router.include_router(questionnaires_router)  # Dynamic form builder
api_router.include_router(credits_router)  # AI Credits system
# Dev / Admin testing panel — only mounted when ENABLE_DEV_PANEL=true so the
# billing- and credit-mutating endpoints can never accidentally be served
# from a production deployment. The /api/dev/enabled probe is always exposed
# (lightweight, no-auth) so the frontend knows whether to render the widget.
if os.environ.get("ENABLE_DEV_PANEL", "").strip().lower() == "true":
    api_router.include_router(dev_router)
else:
    # When disabled, still expose only the lightweight /enabled probe so the
    # frontend Dev Panel widget can hide itself cleanly.
    from fastapi import APIRouter as _AR
    _stub = _AR(prefix="/dev", tags=["dev"])

    @_stub.get("/enabled")
    async def _dev_enabled_probe():  # pragma: no cover - trivial
        return {"enabled": False}
    api_router.include_router(_stub)
api_router.include_router(pricing_setup_router)  # Historical invoice import + pricing setup
api_router.include_router(profit_analytics_router)  # Profit & margin analytics dashboard
api_router.include_router(admin_analytics_router)   # Platform-admin analytics
api_router.include_router(financials_router)  # Financial entries (sales + expenses)
api_router.include_router(onboarding_router)  # Tiered onboarding walkthrough
api_router.include_router(admin_portal_router)  # Admin Portal Communications Hub
api_router.include_router(production_timeline_router)  # Production Timeline Tracking
api_router.include_router(shop_orders_router)  # Shop Order System (Layer 1)
api_router.include_router(job_tickets_router)  # Job Tickets (Layer 2)
api_router.include_router(production_tasks_router)  # Production Tasks (Layer 4)
api_router.include_router(workflow_templates_router)  # Workflow Templates (Admin)
api_router.include_router(digest_router)  # Daily Digest Email
api_router.include_router(order_drawings_router)  # Order Drawings/Signatures
api_router.include_router(signatures_router)  # Structured Signature Requests
api_router.include_router(productivity_router)  # Unified Productivity Layer
api_router.include_router(appointments_router)  # Appointment detail routes
api_router.include_router(appointments_public_router)  # Public tokenized confirm/reject links
api_router.include_router(meta_integration_router)  # Meta/Facebook Messenger integration
api_router.include_router(facebook_messages_router)  # Facebook Leads inbox
api_router.include_router(wrap_router)  # Wrap Command Center (Phase 2A: vehicle info + areas)
api_router.include_router(inventory_router)  # Inventory, job materials, and manual purchasing
api_router.include_router(public_website_router)  # Public website contact/support forms
api_router.include_router(platform_admin_router)  # Platform Admin for tenant impersonation
api_router.include_router(platform_settings_public_router)  # Public banner + maintenance reads
api_router.include_router(platform_settings_admin_router)  # Platform Admin banner + maintenance writes
api_router.include_router(email_deliverability_router)  # Email deliverability endpoints
api_router.include_router(sms_router)  # SMS via Twilio
api_router.include_router(sendgrid_webhook_router)  # Public SendGrid event webhook

# Backup & Restore
from routes.backup import setup_backup_routes
setup_backup_routes(app, db, get_current_active_user, UserInDB)

# Community Hub / Support Board
from routes.community import setup_community_routes
setup_community_routes(app, db, get_current_active_user, UserInDB)

# Include the api_router in the main app
app.include_router(api_router)


# ============== MAINTENANCE MODE MIDDLEWARE ==============

_MAINTENANCE_ALLOW_PREFIXES = (
    "/api/auth/",
    "/api/users/me",
    "/api/platform/",         # public banner + maintenance reads
    "/api/platform-admin/",   # admins keep working
    "/api/webhook/",          # external webhooks (Stripe, SendGrid) must keep flowing
    "/api/health",
)
_MAINTENANCE_BLOCK_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def maintenance_mode_middleware(request, call_next):
    """
    When platform_settings.maintenance.enabled is True, block every mutation
    on /api/* unless the path is on the allowlist. Reads stay open so users
    can still see their data. Platform admins are always allowed (verified by
    the route's own dependency, but we short-circuit on path prefix here).
    """
    try:
        path = request.url.path or ""
        if path.startswith("/api/") and request.method in _MAINTENANCE_BLOCK_METHODS:
            if not any(path.startswith(p) for p in _MAINTENANCE_ALLOW_PREFIXES):
                settings = await db.platform_settings.find_one(
                    {"id": "global"},
                    {"_id": 0, "maintenance": 1},
                )
                if settings and (settings.get("maintenance") or {}).get("enabled") is True:
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=503,
                        content={
                            "detail": {
                                "code": "maintenance_mode",
                                "message": (
                                    settings["maintenance"].get("message")
                                    or "We're doing scheduled maintenance — please try again shortly."
                                ),
                            }
                        },
                    )
    except Exception as e:
        logger.error(f"maintenance_mode_middleware error: {e}")
    return await call_next(request)


# Add CORS middleware.
# A literal wildcard ("*") with allow_credentials=True is rejected by browsers,
# so when no explicit origin list is configured we reflect the request origin
# via allow_origin_regex (valid with credentials) instead of sending "*".
_cors_origins_raw = os.getenv("CORS_ORIGINS", "").strip()
_cors_kwargs = dict(
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if _cors_origins_raw and _cors_origins_raw != "*":
    _cors_kwargs["allow_origins"] = [
        o.strip() for o in _cors_origins_raw.split(",") if o.strip()
    ]
else:
    _cors_kwargs["allow_origin_regex"] = ".*"

app.add_middleware(CORSMiddleware, **_cors_kwargs)


# ============== SHUTDOWN EVENT ==============

async def _run_password_hash_audit():
    """Background audit of stored password hashes.

    bcrypt.checkpw is CPU-bound and blocking. Running this inline during
    FastAPI startup can block the event loop long enough that production
    health checks fail (observed: uvicorn never emits 'Application startup
    complete' on resource-limited containers). We run it off the critical
    path so startup completes immediately.
    """
    import asyncio
    try:
        users = await db.users.find(
            {}, {"_id": 0, "id": 1, "email": 1, "hashed_password": 1}
        ).to_list(100)
        for user in users:
            hp = user.get("hashed_password", "")
            if not hp:
                continue
            try:
                # Offload the blocking bcrypt call to a thread so we don't
                # stall the event loop across many users.
                await asyncio.to_thread(
                    bcrypt.checkpw, b"test", hp.encode("utf-8")
                )
            except (ValueError, TypeError):
                logger.warning(
                    f"User {user.get('email')} has an incompatible password hash. "
                    "They should use forgot-password to reset."
                )
    except Exception as e:
        logger.error(f"Password hash audit error: {e}")


@app.on_event("startup")
async def startup_migrations():
    """Run one-time migrations on startup to fix known production issues."""
    import asyncio

    # Start the digest email scheduler
    try:
        from services.digest_scheduler import start_digest_scheduler
        start_digest_scheduler()
    except Exception as e:
        logger.warning(f"Digest scheduler init deferred: {e}")

    # Initialize object storage
    try:
        init_storage()
    except Exception as e:
        logger.warning(f"Object storage init deferred: {e}")

    # Kick off password hash audit as a background task so it never blocks
    # application startup / readiness.
    try:
        asyncio.create_task(_run_password_hash_audit())
    except Exception as e:
        logger.error(f"Failed to schedule password hash audit: {e}")

    # Ensure the platform creator account has the correct role.
    # PLATFORM_CREATOR_EMAIL in .env identifies the one app developer/creator.
    # This runs on every startup so a redeploy always self-heals the role.
    try:
        creator_email = os.environ.get("PLATFORM_CREATOR_EMAIL", "").strip().lower()
        if creator_email:
            result = await db.users.update_one(
                {"email": creator_email},
                {"$set": {"role": "platform_creator"}}
            )
            if result.modified_count:
                logger.info(f"Platform creator role assigned to {creator_email}")
    except Exception as e:
        logger.warning(f"Platform creator role assignment deferred: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    from services.digest_scheduler import stop_digest_scheduler
    stop_digest_scheduler()
    client.close()
    logger.info("Database connection closed")


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
