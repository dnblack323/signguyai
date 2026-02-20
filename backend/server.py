"""
SignGuy AI - Backend API Server

This file contains the FastAPI application setup and core utilities.
All models are in /models and all routes are in /routes.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends
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
from passlib.context import CryptContext
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
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

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
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


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
    config = await db.pricing_configuration.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if config:
        return config
    
    # Return system defaults if no tenant-specific config
    return PricingDefaults(tenant_id=tenant_id).model_dump()


def get_complexity_multiplier(complexity: int, base: float = 1.0, max_mult: float = 1.5) -> float:
    """Calculate complexity multiplier (1-5 scale) - reduced from 2.0 to 1.5 max"""
    if complexity <= 1:
        return base
    return base + (max_mult - base) * (complexity - 1) / 4


def get_quantity_discount(quantity: float, quantity_breaks: dict) -> float:
    """Calculate quantity discount based on breaks"""
    for qty, discount in sorted(quantity_breaks.items(), key=lambda x: int(x[0]), reverse=True):
        if quantity >= int(qty):
            return discount
    return 0


def create_pricing_result(
    material_cost: float,
    labor_cost: float,
    setup_cost: float,
    additional_costs: float,
    suggested_price: float,
    estimated_labor_minutes: float = 0,
    breakdown: dict = None
) -> PricingCalculation:
    """Create a PricingCalculation with properly calculated profit fields"""
    production_cost = material_cost + labor_cost + setup_cost + additional_costs
    profit_amount = suggested_price - production_cost
    profit_margin_percent = round((profit_amount / suggested_price * 100), 1) if suggested_price > 0 else 0
    
    return PricingCalculation(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost, 2),
        setup_cost=round(setup_cost, 2),
        additional_costs=round(additional_costs, 2),
        production_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        markup_percent=round((suggested_price / production_cost - 1) * 100, 1) if production_cost > 0 else 0,
        profit_margin_percent=profit_margin_percent,
        profit_amount=round(profit_amount, 2),
        estimated_labor_minutes=round(estimated_labor_minutes, 1),
        breakdown=breakdown or {}
    )


async def calculate_promotional(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for promotional products - Setup fee is OPTIONAL"""
    base_cost = data.unit_cost or 0
    product_type = data.promo_product_type
    if product_type == "magnets":
        base_cost = base_cost or 1.50
    elif product_type == "yard_signs":
        base_cost = base_cost or 5.00
    elif product_type == "stickers":
        base_cost = base_cost or 0.25
    elif product_type == "license_plates":
        base_cost = base_cost or 2.00
    elif product_type == "branded_items":
        base_cost = base_cost or 3.00
    else:
        base_cost = base_cost or 2.00
    
    material_cost = base_cost * quantity
    
    # Setup fee is OPTIONAL - only if checkbox is checked
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = 0
    if include_setup:
        setup_fee = data.setup_fee or defaults.get("promo_setup_fee", 15.0)
    
    total_cost = material_cost + setup_fee
    
    # Markup (setup fee not marked up)
    markup = data.markup_percent / 100 if data.markup_percent else defaults.get("default_markup", 1.0)
    if markup < 1:  # If percentage given (e.g., 100 = 100%)
        markup = 1 + markup
    suggested_price = material_cost * markup + setup_fee
    
    # Quantity discount
    discount = get_quantity_discount(quantity, defaults.get("quantity_breaks", {}))
    if discount > 0:
        suggested_price *= (1 - discount)
    
    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=0,
        setup_cost=setup_fee,
        additional_costs=0,
        suggested_price=suggested_price,
        breakdown={
            "product_type": product_type,
            "base_unit_cost": base_cost,
            "quantity": quantity,
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "markup": markup,
            "quantity_discount": discount,
            "price_per_item": round(suggested_price / quantity, 2) if quantity > 0 else 0
        }
    )


async def calculate_cut_vinyl(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for cut vinyl - Industry standard $5-8/sqft final price"""
    width = data.width_inches or 12
    height = data.length_inches or 12
    sqft = (width * height) / 144
    
    # Material costs per sqft (shop cost)
    vinyl_costs = {
        "oracal_651": 0.50,
        "oracal_751": 0.75,
        "oracal_951": 1.00,
        "avery_hp750": 0.85,
        "reflective": 2.50,
        "specialty": 1.50,
        "custom": getattr(data, 'material_cost_override', None) or 1.00
    }
    
    vinyl_type = data.vinyl_type or "oracal_651"
    cost_per_sqft = vinyl_costs.get(vinyl_type, 0.50)
    
    material_cost = sqft * cost_per_sqft * quantity
    
    # Labor: Flat rate approach - simpler and more predictable
    # Base labor: $2/sqft for simple, scales with complexity
    complexity = data.complexity or 1
    labor_per_sqft = 1.50 + (complexity - 1) * 0.50  # $1.50-$6/sqft labor based on complexity
    labor_cost = sqft * labor_per_sqft * quantity
    
    # Setup fee is OPTIONAL - only included if checkbox is checked (include_setup_fee=True)
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = data.setup_fee or 0
    if include_setup and setup_fee == 0:
        setup_fee = defaults.get("default_setup_fee", 15.0)  # Default $15 if checked but no amount specified
    elif not include_setup:
        setup_fee = 0
    
    total_cost = material_cost + labor_cost + setup_fee
    
    # Target final price: $5-8/sqft for simple vinyl (industry standard)
    # Material ~$0.50-1 + Labor ~$1.50-2 = ~$2-3 cost, markup to $5-8
    markup = defaults.get("vinyl_markup", 2.0)
    suggested_price = (material_cost + labor_cost) * markup + setup_fee  # Setup fee not marked up
    
    # Minimum price for very small decals
    min_price = 5.00
    if suggested_price < min_price:
        suggested_price = min_price
    
    # Estimate labor time (for display only)
    estimated_minutes = 3 + (sqft * 2 * complexity)  # 3 min base + 2 min/sqft * complexity
    
    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=0,
        suggested_price=suggested_price,
        estimated_labor_minutes=estimated_minutes * quantity,
        breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "square_feet": round(sqft, 2),
            "vinyl_type": vinyl_type,
            "cost_per_sqft": cost_per_sqft,
            "labor_per_sqft": labor_per_sqft,
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "price_per_sqft": round(suggested_price / sqft, 2) if sqft > 0 else 0
        }
    )


async def calculate_services(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for services (design, installation, etc.) - FIXED"""
    hourly_rate = defaults.get("hourly_rate", 65)  # Was 75
    hours = data.estimated_hours or 1
    
    # Reduced service rate multipliers
    service_rates = {
        "design": hourly_rate * 1.0,       # Was 1.2 - design at base rate
        "installation": hourly_rate * 1.25, # Was 1.5
        "removal": hourly_rate * 1.1,       # Was 1.3
        "site_survey": hourly_rate * 0.75,  # Was 1.0 - site survey is quick
        "consultation": hourly_rate * 0.75, # Was 1.0
        "travel": hourly_rate * 0.5,        # Was 0.75
        "other_labor": hourly_rate
    }
    
    service_type = data.service_type or "other_labor"
    rate = service_rates.get(service_type, hourly_rate)
    
    labor_cost = rate * hours * quantity
    material_cost = getattr(data, 'material_cost_override', None) or 0
    
    total_cost = labor_cost + material_cost
    
    # Service markup is already reasonable at 1.5x
    markup = defaults.get("service_markup", 1.5)
    suggested_price = total_cost * markup
    
    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=0,
        additional_costs=0,
        suggested_price=suggested_price,
        estimated_labor_minutes=hours * 60,
        breakdown={
            "service_type": service_type,
            "hourly_rate": rate,
            "hours": hours,
            "quantity": quantity
        }
    )


async def calculate_digital_print(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for digital prints - Industry standard $4-12/sqft final price"""
    width = data.width_inches or 24
    height = data.length_inches or 36
    sqft = (width * height) / 144
    
    # Material costs per sqft (shop cost)
    material_costs = {
        "banner_13oz": 0.75,
        "banner_18oz": 1.00,
        "vinyl_adhesive": 1.50,
        "poster_paper": 0.50,
        "canvas": 2.50,
        "backlit": 3.00,
        "perforated": 2.50,
        "custom": getattr(data, 'material_cost_override', None) or 1.00
    }
    
    material = data.print_material or "banner_13oz"
    cost_per_sqft = material_costs.get(material, 1.00)
    
    material_cost = sqft * cost_per_sqft * quantity
    
    finishing_cost = 0
    grommets = getattr(data, 'grommets', False)
    hemming = getattr(data, 'hemming', False)
    lamination = data.laminate
    
    if grommets:
        finishing_cost += 1.00 * quantity
    if hemming:
        finishing_cost += 0.50 * quantity
    if lamination:
        material_cost *= 1.25  # 25% increase for lamination
    
    # Labor: Flat rate per sqft approach - more predictable
    labor_per_sqft = 1.00  # $1/sqft base labor for printing
    labor_cost = sqft * labor_per_sqft * quantity
    
    # Setup fee is OPTIONAL - only included if checkbox is checked
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = data.setup_fee or 0
    if include_setup and setup_fee == 0:
        setup_fee = defaults.get("default_setup_fee", 20.0)  # Default $20 for digital print
    elif not include_setup:
        setup_fee = 0
    
    total_cost = material_cost + labor_cost + finishing_cost
    
    # Target: $4-12/sqft final price depending on material
    # Banner ~$4-6/sqft, adhesive vinyl ~$8-10/sqft, specialty ~$10-15/sqft
    markup = defaults.get("print_markup", 2.5)  # 2.5x markup on cost
    suggested_price = total_cost * markup + setup_fee
    
    # Minimum price for small prints
    min_price = 15.00
    if suggested_price < min_price:
        suggested_price = min_price
    
    # Estimate labor time (for display only)
    estimated_minutes = 10 + (sqft * 1.5)  # 10 min setup + 1.5 min/sqft
    
    return create_pricing_result(
        material_cost=material_cost + finishing_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=0,
        suggested_price=suggested_price,
        estimated_labor_minutes=estimated_minutes * quantity,
        breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "square_feet": round(sqft, 2),
            "material": material,
            "cost_per_sqft": cost_per_sqft,
            "finishing_cost": round(finishing_cost, 2),
            "grommets": grommets,
            "hemming": hemming,
            "lamination": lamination,
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "price_per_sqft": round(suggested_price / sqft, 2) if sqft > 0 else 0
        }
    )


async def calculate_rigid_signs(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for rigid signs - Industry standard, optional setup fee"""
    width = data.width_inches or 24
    height = data.length_inches or 18
    sqft = (width * height) / 144
    
    # Substrate costs per sqft
    substrate_costs = {
        "coroplast_4mm": 1.00,
        "coroplast_10mm": 1.50,
        "aluminum_040": 3.00,
        "aluminum_063": 4.50,
        "aluminum_080": 6.00,
        "pvc_3mm": 2.50,
        "pvc_6mm": 3.50,
        "acrylic": 6.00,
        "dibond": 7.00,
        "mdo": 5.00,
        "custom": getattr(data, 'material_cost_override', None) or 3.00
    }
    
    substrate = data.substrate_type or "coroplast_4mm"
    cost_per_sqft = substrate_costs.get(substrate, 2.00)
    
    substrate_cost = sqft * cost_per_sqft * quantity
    
    # Print cost
    print_cost = sqft * 1.50 * quantity
    
    # Finishing costs
    finishing_cost = 0
    if getattr(data, 'rounded_corners', False):
        finishing_cost += 1.00 * quantity
    if getattr(data, 'drill_holes', False):
        finishing_cost += (getattr(data, 'num_holes', 4) or 4) * 0.25 * quantity
    if getattr(data, 'stand', False) or getattr(data, 'stake', False):
        finishing_cost += 3.00 * quantity
    
    # Double-sided adds 75% more material
    if data.double_sided:
        print_cost *= 1.75
    
    # Labor: Flat rate per sqft
    labor_per_sqft = 2.00
    labor_cost = sqft * labor_per_sqft * quantity
    
    # Setup fee is OPTIONAL
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = 0
    if include_setup:
        setup_fee = data.setup_fee or defaults.get("sign_setup_fee", 20.0)
    
    material_cost = substrate_cost + print_cost
    total_cost = material_cost + labor_cost + finishing_cost
    
    # Markup
    markup = defaults.get("sign_markup", 2.0)
    suggested_price = total_cost * markup + setup_fee
    
    # Minimum price
    min_price = 15.00
    if suggested_price < min_price:
        suggested_price = min_price
    
    # Estimate labor time
    estimated_minutes = 10 + (sqft * 3)
    
    return create_pricing_result(
        material_cost=material_cost + finishing_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=0,
        suggested_price=suggested_price,
        estimated_labor_minutes=estimated_minutes * quantity,
        breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "square_feet": round(sqft, 2),
            "substrate": substrate,
            "substrate_cost_per_sqft": cost_per_sqft,
            "print_cost": round(print_cost, 2),
            "finishing_cost": round(finishing_cost, 2),
            "double_sided": data.double_sided,
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "price_per_sqft": round(suggested_price / sqft, 2) if sqft > 0 else 0
        }
    )


async def calculate_apparel(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for apparel decoration - Setup fee is ONE TIME, not per item"""
    garment_costs = {
        "tshirt": 5.00,
        "hoodie": 18.00,
        "hat": 8.00,
        "polo": 12.00,
        "tank": 4.00,
        "longsleeve": 8.00,
        "jacket": 25.00,
        "other": data.blank_cost_override or 10.00
    }
    
    apparel_type = data.apparel_type or "tshirt"
    garment_cost = garment_costs.get(apparel_type, 5.00)
    
    transfer_costs = {
        "htv": 3.00,
        "screen_print": 2.00 if quantity >= 24 else 5.00,
        "dtf": 4.00,
        "sublimation": 5.00,
        "embroidery": 8.00
    }
    
    transfer_type = data.transfer_type or "htv"
    decoration_cost = transfer_costs.get(transfer_type, 3.00)
    
    num_locations = data.num_print_locations or 1
    decoration_cost *= num_locations
    
    # Per-item cost (garment + decoration)
    per_item_cost = garment_cost + decoration_cost
    material_cost = per_item_cost * quantity
    
    # Labor per item (not exponential with quantity)
    time_per_item = 0.1 if transfer_type == "screen_print" else 0.25
    hourly_rate = defaults.get("hourly_rate", 50)  # $50/hr for apparel work
    labor_cost = time_per_item * quantity * hourly_rate
    
    # Setup fee is OPTIONAL and ONE TIME (not per item!)
    # Only add if include_setup_fee checkbox is checked
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = 0
    if include_setup:
        base_setup = data.setup_fee or defaults.get("apparel_setup_fee", 25.0)
        # For screen print, add per-color screen setup
        if transfer_type == "screen_print":
            num_colors = data.num_colors or 1
            base_setup += num_colors * 15  # $15 per screen/color
        setup_fee = base_setup  # ONE TIME - not multiplied by quantity!
    
    total_cost = material_cost + labor_cost + setup_fee
    
    # Markup
    markup = defaults.get("apparel_markup", 1.8)
    suggested_price = (material_cost + labor_cost) * markup + setup_fee  # Setup not marked up
    
    # Quantity discount (larger orders get discount)
    discount = get_quantity_discount(quantity, {"12": 0.05, "24": 0.10, "48": 0.15, "100": 0.20})
    if discount > 0:
        suggested_price *= (1 - discount)
    
    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=0,
        suggested_price=suggested_price,
        estimated_labor_minutes=time_per_item * quantity * 60,
        breakdown={
            "apparel_type": apparel_type,
            "garment_cost": garment_cost,
            "transfer_type": transfer_type,
            "decoration_cost_per_location": transfer_costs.get(transfer_type, 3.00),
            "print_locations": num_locations,
            "per_item_cost": round(per_item_cost, 2),
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "quantity_discount": discount,
            "price_per_item": round(suggested_price / quantity, 2) if quantity > 0 else 0
        }
    )


async def calculate_vehicle_graphics(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for vehicle graphics - Industry standard, optional setup fee"""
    # Vehicle square footage estimates
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
    
    # Material costs per sqft
    material_cost_sqft = 2.50  # Base vinyl
    wrap_type = getattr(data, 'wrap_type', None)
    if wrap_type == "color_change":
        material_cost_sqft = 4.00
    elif wrap_type == "printed":
        material_cost_sqft = 3.50
    
    material_cost = actual_sqft * material_cost_sqft * quantity
    
    # Installation labor - flat rate per sqft
    install_per_sqft = 8.00  # $8/sqft installed (industry standard)
    labor_cost = actual_sqft * install_per_sqft * quantity
    
    # Design cost (optional)
    design_cost = 0
    include_design = getattr(data, 'include_design', False)
    if include_design:
        complexity = data.complexity or 2
        design_cost = 100 * complexity
    
    # Setup fee is OPTIONAL
    include_setup = getattr(data, 'include_setup_fee', False)
    setup_fee = 0
    if include_setup:
        setup_fee = data.setup_fee or defaults.get("vehicle_setup_fee", 50.0)
    
    total_cost = material_cost + labor_cost + design_cost
    
    # Markup - vehicle graphics already include labor, so lower markup
    markup = defaults.get("vehicle_markup", 1.3)
    suggested_price = total_cost * markup + setup_fee + design_cost
    
    # Estimate labor hours
    hours_per_sqft = 0.10
    labor_hours = actual_sqft * hours_per_sqft
    
    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=setup_fee,
        additional_costs=design_cost,
        suggested_price=suggested_price,
        estimated_labor_minutes=labor_hours * 60 * quantity,
        breakdown={
            "vehicle_type": vehicle_type,
            "coverage": coverage,
            "base_sqft": base_sqft,
            "actual_sqft": round(actual_sqft, 2),
            "material_cost_per_sqft": material_cost_sqft,
            "install_per_sqft": install_per_sqft,
            "install_hours": round(labor_hours, 2),
            "design_cost": design_cost,
            "setup_fee": setup_fee,
            "setup_included": include_setup,
            "total_per_vehicle": round(suggested_price / quantity, 2) if quantity > 0 else 0
        }
    )


async def calculate_custom(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for custom items"""
    material_cost = (getattr(data, 'material_cost_override', None) or 0) * quantity
    
    hourly_rate = defaults.get("hourly_rate", 75)
    labor_hours = data.estimated_hours or 1
    labor_cost = labor_hours * hourly_rate * quantity
    
    total_cost = material_cost + labor_cost
    
    markup = defaults.get("default_markup", 2.5)
    suggested_price = total_cost * markup
    
    custom_price = data.price_override if data.override_enabled else None
    if custom_price:
        suggested_price = custom_price * quantity
    
    return create_pricing_result(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=0,
        additional_costs=0,
        suggested_price=suggested_price,
        estimated_labor_minutes=labor_hours * 60,
        breakdown={
            "custom_item": True,
            "labor_hours": labor_hours,
            "hourly_rate": hourly_rate
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
    """Get current user's tenant information"""
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


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
    
    # Return updated tenant
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    return tenant


# ============== IMPORT AND INCLUDE ROUTERS ==============
from routes.auth import router as auth_router, users_router, admin_router
from routes.customers import router as customers_router
from routes.quotes import router as quotes_router
from routes.jobs import router as jobs_router
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

# Include all routers in the api_router
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)
api_router.include_router(customers_router)
api_router.include_router(quotes_router)
api_router.include_router(jobs_router)
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Database connection closed")


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
