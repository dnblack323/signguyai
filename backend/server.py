"""
SignGuy AI - Backend API Server

This file contains the FastAPI application setup and core utilities.
All models are in /models and all routes are in /routes.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
import base64
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import secrets
import re

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Auth configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
security = HTTPBearer(auto_error=False)

# Backwards-compatible reference for imports
pwd_context = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="SignGuy AI API")

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


# ============== AUTH HELPER FUNCTIONS ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except (ValueError, TypeError):
        # Handle corrupted or incompatible hash formats
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        raise credentials_exception
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": token_data.user_id}, {"_id": 0})
    if user is None:
        raise credentials_exception
    
    return UserInDB(**user)


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


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

def has_permission(user: UserInDB, permission: Permission) -> bool:
    """Check if a user has a specific permission based on their role"""
    return user_has_permission(user.role, permission)


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

def generate_tenant_slug(name: str) -> str:
    """Generate a URL-friendly slug from tenant name"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]


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
    merged["materials"] = config.get("materials") or base_defaults.get("materials", [])
    merged["category_defaults"] = {
        **base_defaults.get("category_defaults", {}),
        **config.get("category_defaults", {}),
    }
    merged["selling_price_benchmarks"] = {
        **base_defaults.get("selling_price_benchmarks", {}),
        **config.get("selling_price_benchmarks", {}),
    }
    return merged


def get_material_cost_map(defaults: dict) -> dict:
    material_map = {}
    for material in defaults.get("materials", []):
        key = material.get("key") or material.get("id")
        if key:
            material_map[key] = float(material.get("cost_per_unit", 0) or 0)
    return material_map


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
    """Calculate cut vinyl using tenant cost settings."""
    width = data.width_inches or 12
    height = data.length_inches or 12
    sqft = (width * height) / 144

    vinyl_type = data.vinyl_type or "oracal_651"
    material_cost_map = get_material_cost_map(defaults)
    category_config = get_category_pricing_config(defaults, "cut_vinyl")

    vinyl_cost_per_sqft = material_cost_map.get("vinyl", 1.25)
    transfer_tape_cost_per_sqft = material_cost_map.get("transfer_tape", 0)
    color_count = max(data.num_colors or 1, 1)
    material_cost = sqft * quantity * (vinyl_cost_per_sqft + (transfer_tape_cost_per_sqft * color_count))

    complexity = data.complexity or 1
    labor_hours_per_sqft = float(category_config.get("default_labor_hours_per_sqft", 0.1) or 0)
    complexity_multiplier = 1 + max(complexity - 1, 0) * 0.08
    labor_hours = sqft * quantity * labor_hours_per_sqft * complexity_multiplier
    production_rate = float(defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75)) or 0)
    labor_cost = labor_hours * production_rate

    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = data.setup_fee or 0
    if include_setup and setup_fee == 0:
        setup_fee = defaults.get("setup_fee_vinyl", 15.0)
    elif not include_setup:
        setup_fee = 0

    pre_overhead_total = material_cost + labor_cost  # setup_fee added flat after markup
    overhead_cost = calculate_overhead_cost(pre_overhead_total, labor_hours, defaults, category_config)
    suggested_price = resolve_selling_price(
        pre_overhead_total + overhead_cost,
        category_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5)),
        category_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40.0)),
    )
    # Setup fee added FLAT — not marked up
    suggested_price += setup_fee
    suggested_price = max(
        suggested_price,
        float(category_config.get("minimum_charge", defaults.get("minimum_vinyl_charge", 5.0)) or 5.0),
    )

    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=0,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=labor_hours * 60,
        breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "square_feet": round(sqft, 2),
            "vinyl_type": vinyl_type,
            "vinyl_cost_per_sqft": vinyl_cost_per_sqft,
            "transfer_tape_cost_per_sqft": transfer_tape_cost_per_sqft,
            "labor_hours": round(labor_hours, 2),
            "production_rate": production_rate,
            "overhead_cost": round(overhead_cost, 2),
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "price_per_sqft": round(suggested_price / sqft, 2) if sqft > 0 else 0
        }
    )


async def calculate_services(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate services using tenant labor and pricing settings."""
    category_config = get_category_pricing_config(defaults, "services")
    material_cost_map = get_material_cost_map(defaults)
    hours = data.estimated_hours or float(category_config.get("default_labor_hours", 1.0) or 1.0)

    production_rate = float(defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75)) or 0)
    service_rates = {
        "design": float(defaults.get("design_hourly_rate", production_rate) or production_rate),
        "installation": float(defaults.get("installer_hourly_rate", defaults.get("install_hourly_rate", production_rate)) or production_rate),
        "removal": float(defaults.get("installer_hourly_rate", defaults.get("install_hourly_rate", production_rate)) or production_rate),
        "site_survey": float(defaults.get("installer_hourly_rate", defaults.get("install_hourly_rate", production_rate)) or production_rate),
        "consultation": production_rate,
        "travel": float(defaults.get("installer_hourly_rate", defaults.get("install_hourly_rate", production_rate)) or production_rate),
        "other_labor": production_rate,
    }

    service_type = data.service_type or "other_labor"
    rate = data.hourly_rate_override or service_rates.get(service_type, production_rate)

    labor_cost = rate * hours * quantity
    material_cost = (data.unit_cost or 0) * quantity
    if material_cost == 0 and service_type in ["installation", "removal", "other_labor"]:
        material_cost = material_cost_map.get("misc_material", 0)

    pre_overhead_total = material_cost + labor_cost
    overhead_cost = calculate_overhead_cost(pre_overhead_total, hours * quantity, defaults, category_config)
    suggested_price = resolve_selling_price(
        pre_overhead_total + overhead_cost,
        category_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5)),
        category_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40.0)),
    )
    suggested_price = max(
        suggested_price,
        float(category_config.get("minimum_charge", defaults.get("minimum_service_charge", 0)) or 0),
    )

    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=0,
        additional_costs=0,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=hours * 60,
        breakdown={
            "service_type": service_type,
            "hourly_rate": rate,
            "hours": hours,
            "quantity": quantity,
            "overhead_cost": round(overhead_cost, 2),
        }
    )


async def calculate_digital_print(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate banner-first pricing using tenant cost settings."""
    width = data.width_inches or 24
    height = data.length_inches or 36
    sqft = (width * height) / 144

    material = data.print_material or "banner_13oz"
    is_banner_job = material.startswith("banner_")
    category_key = "banners" if is_banner_job else "digital_print"
    category_config = get_category_pricing_config(defaults, category_key)
    material_cost_map = get_material_cost_map(defaults)

    material_cost_per_sqft = material_cost_map.get("banner_material", 0.9) if is_banner_job else material_cost_map.get("vinyl", 1.25)
    ink_cost_per_sqft = material_cost_map.get("ink", 0)
    laminate_cost_per_sqft = material_cost_map.get("laminate", 0) if data.laminate else 0
    material_cost = sqft * quantity * (material_cost_per_sqft + ink_cost_per_sqft + laminate_cost_per_sqft)

    finishing_cost = 0
    grommets = getattr(data, 'grommets', False)
    hemming = getattr(data, 'hemming', False)
    lamination = data.laminate
    
    if grommets:
        finishing_cost += 1.00 * quantity
    if hemming:
        finishing_cost += 0.50 * quantity

    labor_hours = sqft * quantity * float(category_config.get("default_labor_hours_per_sqft", 0.06) or 0)
    production_rate = float(defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75)) or 0)
    labor_cost = labor_hours * production_rate

    # Setup fee is OPTIONAL - only included if checkbox is checked
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = data.setup_fee or 0
    if include_setup and setup_fee == 0:
        setup_fee = defaults.get("setup_fee_print", 20.0)
    elif not include_setup:
        setup_fee = 0

    pre_overhead_total = material_cost + labor_cost + finishing_cost  # setup_fee added flat after markup
    overhead_cost = calculate_overhead_cost(pre_overhead_total, labor_hours, defaults, category_config)
    suggested_price = resolve_selling_price(
        pre_overhead_total + overhead_cost,
        category_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5)),
        category_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40.0)),
    )
    # Setup fee added FLAT — not marked up
    suggested_price += setup_fee
    suggested_price = max(suggested_price, float(category_config.get("minimum_charge", 15.0) or 15.0))

    return create_pricing_result(
        material_cost=material_cost + finishing_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=0,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=labor_hours * 60,
        breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "square_feet": round(sqft, 2),
            "material": material,
            "material_cost_per_sqft": material_cost_per_sqft,
            "ink_cost_per_sqft": ink_cost_per_sqft,
            "laminate_cost_per_sqft": laminate_cost_per_sqft,
            "finishing_cost": round(finishing_cost, 2),
            "grommets": grommets,
            "hemming": hemming,
            "lamination": lamination,
            "labor_hours": round(labor_hours, 2),
            "production_rate": production_rate,
            "overhead_cost": round(overhead_cost, 2),
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "price_per_sqft": round(suggested_price / sqft, 2) if sqft > 0 else 0
        }
    )


async def calculate_rigid_signs(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate rigid signs using company cost settings."""
    width = data.width_inches or 24
    height = data.length_inches or 18
    sqft = (width * height) / 144

    substrate = data.substrate_type or "coroplast_4mm"
    category_config = get_category_pricing_config(defaults, "rigid_signs")
    material_cost_map = get_material_cost_map(defaults)
    substrate_key_map = {
        "coroplast_4mm": "coroplast",
        "coroplast_10mm": "coroplast",
        "aluminum_040": "aluminum_composite",
        "aluminum_063": "aluminum_composite",
        "aluminum_080": "aluminum_composite",
        "dibond": "aluminum_composite",
        "pvc_3mm": "foam_board",
        "pvc_6mm": "foam_board",
        "acrylic": "acrylic_sheet",
        "mdo": "rigid_sign_board",
    }
    material_key = substrate_key_map.get(substrate, "coroplast")
    substrate_cost_per_sqft = material_cost_map.get(material_key, 2.0)
    ink_cost_per_sqft = material_cost_map.get("ink", 0)
    laminate_cost_per_sqft = material_cost_map.get("laminate", 0) if data.laminate else 0

    material_cost = sqft * quantity * (substrate_cost_per_sqft + ink_cost_per_sqft + laminate_cost_per_sqft)

    # Finishing costs
    finishing_cost = 0
    if getattr(data, 'rounded_corners', False):
        finishing_cost += 1.00 * quantity
    if getattr(data, 'drill_holes', False):
        finishing_cost += (getattr(data, 'num_holes', 4) or 4) * 0.25 * quantity
    if getattr(data, 'stand', False) or getattr(data, 'stake', False):
        finishing_cost += 3.00 * quantity

    if data.double_sided:
        material_cost *= 1.75

    labor_hours = sqft * quantity * float(category_config.get("default_labor_hours_per_sqft", 0.08) or 0)
    production_rate = float(defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75)) or 0)
    labor_cost = labor_hours * production_rate

    # Setup fee is OPTIONAL
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = 0
    if include_setup:
        setup_fee = data.setup_fee or defaults.get("minimum_sign_charge", 20.0)

    pre_overhead_total = material_cost + labor_cost + finishing_cost  # setup_fee added flat after markup
    overhead_cost = calculate_overhead_cost(pre_overhead_total, labor_hours, defaults, category_config)
    suggested_price = resolve_selling_price(
        pre_overhead_total + overhead_cost,
        category_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5)),
        category_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40.0)),
    )
    # Setup fee added FLAT — not marked up
    suggested_price += setup_fee
    suggested_price = max(
        suggested_price,
        float(category_config.get("minimum_charge", defaults.get("minimum_sign_charge", 15.0)) or 15.0),
    )

    return create_pricing_result(
        material_cost=material_cost + finishing_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=0,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=labor_hours * 60,
        breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "square_feet": round(sqft, 2),
            "substrate": substrate,
            "substrate_cost_per_sqft": substrate_cost_per_sqft,
            "ink_cost_per_sqft": ink_cost_per_sqft,
            "laminate_cost_per_sqft": laminate_cost_per_sqft,
            "finishing_cost": round(finishing_cost, 2),
            "labor_hours": round(labor_hours, 2),
            "production_rate": production_rate,
            "overhead_cost": round(overhead_cost, 2),
            "double_sided": data.double_sided,
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "price_per_sqft": round(suggested_price / sqft, 2) if sqft > 0 else 0
        }
    )


async def calculate_apparel(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate apparel using tenant cost settings."""
    category_config = get_category_pricing_config(defaults, "apparel")
    material_cost_map = get_material_cost_map(defaults)

    apparel_type = data.apparel_type or "tshirt"
    garment_cost = data.blank_cost_override or material_cost_map.get("apparel_blank", 5.0)

    transfer_type = data.transfer_type or "htv"
    decoration_cost = material_cost_map.get("apparel_decoration", 2.5)
    num_locations = data.num_print_locations or 1
    decoration_cost *= num_locations

    per_item_cost = garment_cost + decoration_cost
    material_cost = per_item_cost * quantity

    time_per_item = float(category_config.get("default_labor_hours_per_unit", 0.08) or 0.08)
    production_rate = float(defaults.get("production_hourly_rate", defaults.get("hourly_rate", 75)) or 0)
    labor_cost = time_per_item * quantity * production_rate

    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = 0
    if include_setup:
        setup_fee = data.setup_fee or (
            defaults.get("setup_fee_apparel_screen", 35.0)
            if transfer_type == "screen_print"
            else defaults.get("setup_fee_apparel_dtf", 20.0)
        )

    pre_overhead_total = material_cost + labor_cost  # setup_fee added flat after markup
    overhead_cost = calculate_overhead_cost(pre_overhead_total, time_per_item * quantity, defaults, category_config)
    suggested_price = resolve_selling_price(
        pre_overhead_total + overhead_cost,
        category_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5)),
        category_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40.0)),
    )
    # Setup fee added FLAT — not marked up
    suggested_price += setup_fee
    
    # Apparel quantity discounts
    apparel_qty_breaks = category_config.get("quantity_breaks", defaults.get("apparel_quantity_breaks", {
        "12": 5, "24": 10, "48": 15, "72": 20, "144": 25
    }))
    discount = get_quantity_discount(quantity, apparel_qty_breaks)
    if discount > 0:
        suggested_price *= (1 - discount)
    
    suggested_price = max(
        suggested_price,
        float(category_config.get("minimum_charge", defaults.get("minimum_order", 0)) or 0),
    )

    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=0,
        overhead_cost=overhead_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=time_per_item * quantity * 60,
        breakdown={
            "apparel_type": apparel_type,
            "garment_cost": garment_cost,
            "transfer_type": transfer_type,
            "decoration_cost_per_location": material_cost_map.get("apparel_decoration", 2.5),
            "print_locations": num_locations,
            "per_item_cost": round(per_item_cost, 2),
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "overhead_cost": round(overhead_cost, 2),
            "quantity_discount": f"{int(discount*100)}%" if discount > 0 else "0%",
            "price_per_item": round(suggested_price / quantity, 2) if quantity > 0 else 0
        }
    )


async def calculate_vehicle_graphics(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate vehicle wraps using company cost settings."""
    vehicle_sqft = {
        "car_sedan": 120,
        "car_suv": 160,
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== SHUTDOWN EVENT ==============

@app.on_event("startup")
async def startup_migrations():
    """Run one-time migrations on startup to fix known production issues."""
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
    
    # Initialize cloud storage service
    try:
        from services.storage import storage_service
        if storage_service.init():
            logger.info("Cloud storage service initialized successfully")
        else:
            logger.warning("Cloud storage service failed to initialize - file uploads will fail")
    except Exception as e:
        logger.error(f"Cloud storage initialization error: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Database connection closed")


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
