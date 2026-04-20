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
from typing import Optional
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
    
    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=0,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        breakdown={
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
            "price_per_item": round(suggested_price / quantity, 2) if quantity > 0 else 0
        }
    )


async def calculate_cut_vinyl(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate cut vinyl using Pricing Foundation defaults."""
    width = data.width_inches or 12
    height = data.length_inches or 12
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

    base_hours_per_sqft = float(category_config.get("production_labor_hours_per_sqft", category_config.get("default_labor_hours_per_sqft", 0.2)) or 0)
    min_prod_hours = float(category_config.get("min_production_labor_hours_per_item", 0.25) or 0)
    per_piece_hours = billable_area_per_piece * base_hours_per_sqft
    per_piece_hours = max(per_piece_hours, min_prod_hours)
    production_hours = per_piece_hours * quantity

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

    production_hours *= color_mult * weeding_mult

    design_hours = 0
    if data.artwork_ready:
        design_hours = 0
    elif data.artwork_needed or data.artwork_needed is None:
        base_design_time = float(category_config.get("default_design_time_hours", 0.5) or 0)
        design_complexity = data.design_complexity or category_config.get("default_design_complexity", "simple")
        design_mult = {
            "simple": 1.0,
            "medium": 1.25,
            "complex": 1.5,
            "extreme": 2.0,
        }.get(design_complexity, 1.0)
        design_hours = base_design_time * design_mult

    labor_rates = defaults.get("labor_rates", {})
    production_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75))) or 0)
    design_rate = float(labor_rates.get("design", {}).get("hourly_rate", defaults.get("design_hourly_rate", 85)) or 0)
    install_rate = float(labor_rates.get("installation", {}).get("hourly_rate", defaults.get("install_hourly_rate", 95)) or 0)

    production_cost = production_hours * production_rate
    design_cost = design_hours * design_rate

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

    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=0,
        additional_costs=file_cleanup_fee,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=(production_hours + design_hours + install_hours) * 60,
        breakdown={
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
        }
    )


async def calculate_digital_print(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate digital print pricing using Pricing Foundation defaults."""
    width = data.width_inches or 24
    height = data.length_inches or 24
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
    laminate_warning = ""
    if laminate_required:
        laminate_cost_per_sqft = get_material_cost_per_sqft(defaults, laminate_key)
        if laminate_cost_per_sqft <= 0:
            laminate_warning = f"Missing laminate type: {laminate_key}."
        laminate_cost = waste_adjusted_area * laminate_cost_per_sqft

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

    base_prod_hours_per_sqft = float(category_config.get("production_labor_hours_per_sqft", category_config.get("default_labor_hours_per_sqft", 0.08)) or 0)
    min_prod_hours = float(category_config.get("min_production_labor_hours_per_item", 0.2) or 0)
    per_piece_prod_hours = billable_area_per_piece * base_prod_hours_per_sqft * quality_mult * contour_mult
    per_piece_prod_hours = max(per_piece_prod_hours, min_prod_hours)
    production_hours = per_piece_prod_hours * quantity

    complexity_mult = get_complexity_multiplier(
        int(data.complexity or 1),
        float(defaults.get("complexity_multiplier_base", 1.0) or 1.0),
        float(defaults.get("complexity_multiplier_max", 1.5) or 1.5)
    )
    production_hours *= complexity_mult

    separation_hours = 0
    if data.piece_separation_required:
        count = max(int(data.separated_piece_count or 0), 0)
        separation_rate = float(category_config.get("piece_separation_hours_per_piece", 0.02) or 0)
        separation_hours = count * separation_rate

    design_hours = 0
    if data.artwork_ready:
        design_hours = 0
    elif data.artwork_needed or data.artwork_needed is None:
        base_design_time = float(category_config.get("default_design_time_hours", 0.5) or 0)
        design_complexity = (data.design_complexity or category_config.get("default_design_complexity", "simple"))
        design_mult = {
            "simple": 1.0,
            "medium": 1.25,
            "complex": 1.5,
            "extreme": 2.0,
        }.get(design_complexity, 1.0)
        design_hours = base_design_time * design_mult

    labor_rates = defaults.get("labor_rates", {})
    production_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75))) or 0)
    design_rate = float(labor_rates.get("design", {}).get("hourly_rate", defaults.get("design_hourly_rate", 85)) or 0)
    install_rate = float(labor_rates.get("installation", {}).get("hourly_rate", defaults.get("install_hourly_rate", 95)) or 0)

    production_labor_cost = production_hours * production_rate
    mounting_labor_cost = mounting_hours * production_rate
    separation_labor_cost = separation_hours * production_rate
    design_cost = design_hours * design_rate

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

    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=file_cleanup_fee + trim_addon,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=(production_hours + mounting_hours + separation_hours + design_hours + install_hours) * 60,
        breakdown={
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
        }
    )


async def calculate_rigid_signs(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate rigid sign pricing using Pricing Foundation defaults."""
    width = data.width_inches or 24
    height = data.length_inches or 24
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

    base_hours_per_sqft = float(category_config.get("production_labor_hours_per_sqft", category_config.get("default_labor_hours_per_sqft", 0.15)) or 0)
    min_prod_hours = float(category_config.get("min_production_labor_hours_per_item", 0.2) or 0)
    per_piece_hours = billable_area_per_piece * base_hours_per_sqft
    per_piece_hours = max(per_piece_hours, min_prod_hours)
    production_hours = per_piece_hours * quantity * thickness_mult * shape_mult * sided_mult

    labor_rates = defaults.get("labor_rates", {})
    production_rate = float(labor_rates.get("production", {}).get("hourly_rate", defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75))) or 0)
    design_rate = float(labor_rates.get("design", {}).get("hourly_rate", defaults.get("design_hourly_rate", 85)) or 0)
    install_rate = float(labor_rates.get("installation", {}).get("hourly_rate", defaults.get("install_hourly_rate", 95)) or 0)

    production_cost = production_hours * production_rate
    mounting_cost = mounting_hours * production_rate

    design_hours = 0
    if data.artwork_ready:
        design_hours = 0
    elif data.artwork_needed or data.artwork_needed is None:
        base_design_time = float(category_config.get("default_design_time_hours", 0.5) or 0)
        design_complexity = data.design_complexity or "simple"
        design_mult = {
            "simple": 1.0,
            "medium": 1.25,
            "complex": 1.5,
            "extreme": 2.0,
        }.get(design_complexity, 1.0)
        design_hours = base_design_time * design_mult
    design_cost = design_hours * design_rate

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

    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=0,
        additional_costs=drill_prep_fee,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=(production_hours + design_hours + install_hours + mounting_hours) * 60,
        breakdown={
            "dimensions": f"{width}" x {height}"",
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


async def calculate_vehicle_graphics(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate vehicle wraps using company cost settings."""
    vehicle_sqft = {
        "car_sedan": 120,
        "car_suv": 160,
        "pickup": 175,
        "van_mini": 140,
        "van_cargo": 200,
        "van_sprinter": 250,
        "box_truck_12ft": 320,
        "box_truck_16ft": 400,
        "box_truck_24ft": 520,
        "trailer": 600,
        "semi": 800,
        "other": data.estimated_vehicle_sqft or 160
    }
    
    coverage_multipliers = {
        "spot": 0.10,      # Spot graphics (logo + phone)
        "partial": 0.25,   # ~quarter of vehicle
        "half": 0.45,
        "full": 1.0
    }
    
    vehicle_type = data.vehicle_type or "van_cargo"
    base_sqft = vehicle_sqft.get(vehicle_type, 200)

    coverage = data.coverage_type or "partial"
    actual_sqft = base_sqft * coverage_multipliers.get(coverage, 0.25)

    category_config = get_category_pricing_config(defaults, "vehicle_wraps")
    material_cost_map = get_material_cost_map(defaults)
    vinyl_cost_per_sqft = material_cost_map.get("vinyl", 1.25)
    laminate_cost_per_sqft = material_cost_map.get("laminate", 0.65)
    ink_cost_per_sqft = material_cost_map.get("ink", 0.35)

    material_cost = actual_sqft * quantity * (vinyl_cost_per_sqft + laminate_cost_per_sqft + ink_cost_per_sqft)

    install_hours = actual_sqft * quantity * float(category_config.get("default_labor_hours_per_sqft", 0.12) or 0)
    installer_rate = float(defaults.get("installer_hourly_rate", defaults.get("install_hourly_rate", 95)) or 0)
    labor_cost = install_hours * installer_rate

    design_cost = 0
    include_design = getattr(data, 'include_design', False)
    design_hours = 0
    if include_design:
        complexity = data.complexity or 2
        design_hours = max(1, complexity * 0.5)
        design_cost = design_hours * float(defaults.get("design_hourly_rate", 85) or 0)

    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = 0
    if include_setup:
        setup_fee = data.setup_fee or defaults.get("minimum_wrap_charge", 50.0)

    pre_overhead_total = material_cost + labor_cost + design_cost  # setup_fee added flat after markup
    overhead_cost = calculate_overhead_cost(pre_overhead_total, install_hours + design_hours, defaults, category_config)
    suggested_price = resolve_selling_price(
        pre_overhead_total + overhead_cost,
        category_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5)),
        category_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40.0)),
    )
    # Setup fee added FLAT — not marked up
    suggested_price += setup_fee
    suggested_price = max(
        suggested_price,
        float(category_config.get("minimum_charge", defaults.get("minimum_wrap_charge", 500.0)) or 500.0),
    )
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order)

    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=design_cost,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=(install_hours + design_hours) * 60,
        breakdown={
            "vehicle_type": vehicle_type,
            "coverage": coverage,
            "base_sqft": base_sqft,
            "actual_sqft": round(actual_sqft, 2),
            "vinyl_cost_per_sqft": vinyl_cost_per_sqft,
            "laminate_cost_per_sqft": laminate_cost_per_sqft,
            "ink_cost_per_sqft": ink_cost_per_sqft,
            "installer_rate": installer_rate,
            "install_hours": round(install_hours, 2),
            "design_hours": round(design_hours, 2),
            "design_cost": design_cost,
            "overhead_cost": round(overhead_cost, 2),
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "total_per_vehicle": round(suggested_price / quantity, 2) if quantity > 0 else 0
        }
    )


async def calculate_services(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate service-based pricing."""
    category_config = get_category_pricing_config(defaults, "services")
    estimated_hours = float(data.estimated_hours or 1)
    num_workers = max(int(data.num_workers or 1), 1)
    labor_hours = estimated_hours * num_workers
    hourly_rate = float(data.hourly_rate_override or defaults.get("hourly_rate", 75) or 0)

    labor_cost = labor_hours * hourly_rate
    travel_cost = float(data.distance_miles or 0) * float(defaults.get("mileage_rate", 0) or 0)
    material_cost = travel_cost

    overhead_cost = calculate_overhead_cost(material_cost + labor_cost, labor_hours, defaults, category_config)
    suggested_price = resolve_selling_price(
        material_cost + labor_cost + overhead_cost,
        category_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5)),
        category_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40.0)),
    )
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order)

    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=0,
        additional_costs=0,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=labor_hours * 60,
        breakdown={
            "estimated_hours": estimated_hours,
            "num_workers": num_workers,
            "hourly_rate": hourly_rate,
            "travel_cost": round(travel_cost, 2),
        }
    )


async def calculate_custom(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate custom items using tenant cost settings."""
    category_config = get_category_pricing_config(defaults, "custom")
    material_cost_map = get_material_cost_map(defaults)
    material_cost = (data.unit_cost or material_cost_map.get("misc_material", 0)) * quantity

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
    if custom_price:
        suggested_price = custom_price * quantity

    suggested_price = max(
        suggested_price,
        float(category_config.get("minimum_charge", defaults.get("minimum_order", 0)) or 0),
    )
    suggested_price = apply_rush_order_multiplier(suggested_price, data.rush_order)

    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=0,
        additional_costs=0,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=labor_hours * 60,
        breakdown={
            "custom_item": True,
            "labor_hours": labor_hours,
            "hourly_rate": hourly_rate,
            "overhead_cost": round(overhead_cost, 2),
        }
    )


async def calculate_pricing(
    category: PricingCategory,
    data: JobItemPricingData,
    quantity: float,
    tenant_id: str
) -> PricingCalculation:
    """Main pricing calculation dispatcher"""
    defaults = await get_pricing_defaults(tenant_id)
    
    calculators = {
        PricingCategory.PROMOTIONAL: calculate_promotional,
        PricingCategory.CUT_VINYL: calculate_cut_vinyl,
        PricingCategory.SERVICES: calculate_services,
        PricingCategory.DIGITAL_PRINT: calculate_digital_print,
        PricingCategory.RIGID_SIGNS: calculate_rigid_signs,
        PricingCategory.APPAREL: calculate_apparel,
        PricingCategory.VEHICLE_GRAPHICS: calculate_vehicle_graphics,
        PricingCategory.CUSTOM: calculate_custom,
    }
    
    calculator = calculators.get(category, calculate_custom)
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
from routes.job_time import router as job_time_router
from routes.promo_codes import router as promo_codes_router
from routes.approvals import router as approvals_router
from routes.documents import router as documents_router
from routes.email_templates import router as email_templates_router
from routes.admin_portal import router as admin_portal_router
from routes.production_timeline import router as production_timeline_router
from routes.stripe_connect import router as stripe_connect_router
from routes.plans import router as plans_router
from routes.questionnaires import router as questionnaires_router
from routes.credits import router as credits_router
from routes.dev import router as dev_router
from routes.pricing_setup import router as pricing_setup_router
from routes.profit_analytics import router as profit_analytics_router, financials_router
from routes.onboarding import router as onboarding_router
from routes.orders import router as shop_orders_router
from routes.job_tickets import router as job_tickets_router
from routes.production_tasks import router as production_tasks_router
from routes.workflow_templates import router as workflow_templates_router
from routes.digest import router as digest_router
from routes.order_drawings import router as order_drawings_router
from routes.signatures import router as signatures_router
from routes.productivity import router as productivity_router
from routes.appointments import router as appointments_router

# Include all routers in the api_router
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)
api_router.include_router(customers_router)
api_router.include_router(quotes_router)
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
api_router.include_router(job_time_router)
api_router.include_router(promo_codes_router)
api_router.include_router(approvals_router)
api_router.include_router(documents_router)
api_router.include_router(email_templates_router)
api_router.include_router(stripe_connect_router)
api_router.include_router(plans_router)  # Multi-product plan management
api_router.include_router(questionnaires_router)  # Dynamic form builder
api_router.include_router(credits_router)  # AI Credits system
api_router.include_router(dev_router)  # Dev/Admin testing panel
api_router.include_router(pricing_setup_router)  # Historical invoice import + pricing setup
api_router.include_router(profit_analytics_router)  # Profit & margin analytics dashboard
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

# Backup & Restore
from routes.backup import setup_backup_routes
setup_backup_routes(app, db, get_current_active_user, UserInDB)

# Community Hub / Support Board
from routes.community import setup_community_routes
setup_community_routes(app, db, get_current_active_user, UserInDB)

# Include the api_router in the main app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== SHUTDOWN EVENT ==============

@app.on_event("startup")
async def startup_migrations():
    """Run one-time migrations on startup to fix known production issues."""
    # Start the digest email scheduler
    from services.digest_scheduler import start_digest_scheduler
    start_digest_scheduler()

    # Initialize object storage
    try:
        init_storage()
    except Exception as e:
        logger.warning(f"Object storage init deferred: {e}")

    try:
        # Fix: Re-hash any passwords that might have been created by old passlib
        # This runs silently and only fixes hashes that fail bcrypt verification
        users = await db.users.find({}, {"_id": 0, "id": 1, "email": 1, "hashed_password": 1}).to_list(100)
        for user in users:
            hp = user.get("hashed_password", "")
            if not hp:
                continue
            try:
                # Test if the hash is valid bcrypt
                bcrypt.checkpw(b"test", hp.encode("utf-8"))
            except (ValueError, TypeError):
                # Hash is corrupt/incompatible — can't fix without knowing the password
                # But we can flag it for the user to reset via forgot-password
                logger.warning(f"User {user.get('email')} has an incompatible password hash. They should use forgot-password to reset.")
    except Exception as e:
        logger.error(f"Startup migration error: {e}")


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
