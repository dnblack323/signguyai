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
                detail=f"You don't have permission to perform this action"
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
            detail=f"You don't have permission to perform this action"
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


def get_complexity_multiplier(complexity: int, base: float = 1.0, max_mult: float = 2.0) -> float:
    """Calculate complexity multiplier (1-5 scale)"""
    if complexity <= 1:
        return base
    return base + (max_mult - base) * (complexity - 1) / 4


def get_quantity_discount(quantity: float, quantity_breaks: dict) -> float:
    """Calculate quantity discount based on breaks"""
    for qty, discount in sorted(quantity_breaks.items(), key=lambda x: int(x[0]), reverse=True):
        if quantity >= int(qty):
            return discount
    return 0


async def calculate_promotional(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for promotional products"""
    base_cost = data.unit_cost or 0
    if data.product_type == "magnets":
        base_cost = base_cost or 2.50
    elif data.product_type == "yard_signs":
        base_cost = base_cost or 8.00
    elif data.product_type == "stickers":
        base_cost = base_cost or 0.50
    
    setup_fee = data.setup_fee or 25.0
    material_cost = base_cost * quantity
    labor_cost = setup_fee
    total_cost = material_cost + labor_cost
    
    markup = defaults.get("default_markup", 2.5)
    suggested_price = total_cost * markup
    
    complexity_mult = get_complexity_multiplier(data.complexity or 1)
    suggested_price *= complexity_mult
    
    discount = get_quantity_discount(quantity, defaults.get("quantity_breaks", {}))
    if discount > 0:
        suggested_price *= (1 - discount)
    
    return PricingCalculation(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost, 2),
        total_cost=round(total_cost, 2),
        suggested_price=round(suggested_price, 2),
        profit_margin=round((suggested_price - total_cost) / suggested_price * 100, 1) if suggested_price > 0 else 0,
        breakdown={
            "base_unit_cost": base_cost,
            "quantity": quantity,
            "setup_fee": setup_fee,
            "markup": markup,
            "complexity_multiplier": complexity_mult,
            "quantity_discount": discount
        }
    )


async def calculate_cut_vinyl(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for cut vinyl"""
    width = data.width_inches or 12
    height = data.length_inches or 12
    sqft = (width * height) / 144
    
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
    
    hourly_rate = defaults.get("hourly_rate", 75)
    complexity = data.complexity or 1
    labor_hours = (sqft * 0.25 * complexity) * quantity
    labor_cost = labor_hours * hourly_rate
    
    weeding_factor = 1 + (complexity - 1) * 0.2
    labor_cost *= weeding_factor
    
    setup_fee = data.setup_fee or 15.0
    total_cost = material_cost + labor_cost + setup_fee
    
    markup = defaults.get("default_markup", 2.5)
    suggested_price = total_cost * markup
    
    return PricingCalculation(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost + setup_fee, 2),
        total_cost=round(total_cost, 2),
        suggested_price=round(suggested_price, 2),
        profit_margin=round((suggested_price - total_cost) / suggested_price * 100, 1) if suggested_price > 0 else 0,
        breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "square_feet": round(sqft, 2),
            "vinyl_type": vinyl_type,
            "cost_per_sqft": cost_per_sqft,
            "labor_hours": round(labor_hours, 2),
            "weeding_factor": round(weeding_factor, 2),
            "setup_fee": setup_fee
        }
    )


async def calculate_services(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for services (design, installation, etc.)"""
    hourly_rate = defaults.get("hourly_rate", 75)
    hours = data.estimated_hours or 1
    
    service_rates = {
        "design": hourly_rate * 1.2,
        "installation": hourly_rate * 1.5,
        "removal": hourly_rate * 1.3,
        "site_survey": hourly_rate * 1.0,
        "consultation": hourly_rate * 1.0,
        "travel": hourly_rate * 0.75,
        "other_labor": hourly_rate
    }
    
    service_type = data.service_type or "other_labor"
    rate = service_rates.get(service_type, hourly_rate)
    
    labor_cost = rate * hours * quantity
    material_cost = getattr(data, 'material_cost_override', None) or 0
    
    total_cost = labor_cost + material_cost
    
    markup = defaults.get("service_markup", 1.5)
    suggested_price = total_cost * markup
    
    return PricingCalculation(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost, 2),
        total_cost=round(total_cost, 2),
        suggested_price=round(suggested_price, 2),
        profit_margin=round((suggested_price - total_cost) / suggested_price * 100, 1) if suggested_price > 0 else 0,
        breakdown={
            "service_type": service_type,
            "hourly_rate": rate,
            "hours": hours,
            "quantity": quantity
        }
    )


async def calculate_digital_print(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for digital prints"""
    width = data.width_inches or 24
    height = data.length_inches or 36
    sqft = (width * height) / 144
    
    material_costs = {
        "banner_13oz": 1.50,
        "banner_18oz": 2.00,
        "vinyl_adhesive": 3.00,
        "poster_paper": 1.00,
        "canvas": 4.00,
        "backlit": 5.00,
        "perforated": 4.50,
        "custom": getattr(data, 'material_cost_override', None) or 2.00
    }
    
    material = data.print_material or "banner_13oz"
    cost_per_sqft = material_costs.get(material, 2.00)
    
    material_cost = sqft * cost_per_sqft * quantity
    
    finishing_cost = 0
    grommets = getattr(data, 'grommets', False)
    hemming = getattr(data, 'hemming', False)
    lamination = data.laminate
    
    if grommets:
        finishing_cost += 1.50 * quantity
    if hemming:
        finishing_cost += (width + height) * 2 / 12 * 0.50 * quantity
    if lamination:
        material_cost *= 1.4
    
    hourly_rate = defaults.get("hourly_rate", 75)
    setup_time = 0.25
    print_time = sqft * 0.1 * quantity
    labor_cost = (setup_time + print_time) * hourly_rate
    
    total_cost = material_cost + labor_cost + finishing_cost
    
    markup = defaults.get("default_markup", 2.5)
    suggested_price = total_cost * markup
    
    return PricingCalculation(
        material_cost=round(material_cost + finishing_cost, 2),
        labor_cost=round(labor_cost, 2),
        total_cost=round(total_cost, 2),
        suggested_price=round(suggested_price, 2),
        profit_margin=round((suggested_price - total_cost) / suggested_price * 100, 1) if suggested_price > 0 else 0,
        breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "square_feet": round(sqft, 2),
            "material": material,
            "cost_per_sqft": cost_per_sqft,
            "finishing_cost": round(finishing_cost, 2),
            "grommets": grommets,
            "hemming": hemming,
            "lamination": lamination
        }
    )


async def calculate_rigid_signs(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for rigid signs"""
    width = data.width_inches or 24
    height = data.length_inches or 18
    sqft = (width * height) / 144
    
    substrate_costs = {
        "coroplast_4mm": 2.00,
        "coroplast_10mm": 3.00,
        "aluminum_040": 5.00,
        "aluminum_063": 7.00,
        "aluminum_080": 9.00,
        "pvc_3mm": 4.00,
        "pvc_6mm": 6.00,
        "acrylic": 10.00,
        "dibond": 12.00,
        "mdo": 8.00,
        "custom": getattr(data, 'material_cost_override', None) or 5.00
    }
    
    substrate = data.substrate_type or "coroplast_4mm"
    cost_per_sqft = substrate_costs.get(substrate, 3.00)
    
    substrate_cost = sqft * cost_per_sqft * quantity
    
    print_cost = sqft * 3.00 * quantity
    
    finishing_cost = 0
    if getattr(data, 'rounded_corners', False):
        finishing_cost += 2.00 * quantity
    if getattr(data, 'drill_holes', False):
        finishing_cost += (getattr(data, 'num_holes', 4) or 4) * 0.50 * quantity
    if getattr(data, 'stand', False) or getattr(data, 'stake', False):
        finishing_cost += 5.00 * quantity
    
    hourly_rate = defaults.get("hourly_rate", 75)
    labor_hours = 0.25 + (sqft * 0.15) * quantity
    labor_cost = labor_hours * hourly_rate
    
    material_cost = substrate_cost + print_cost
    total_cost = material_cost + labor_cost + finishing_cost
    
    markup = defaults.get("default_markup", 2.5)
    suggested_price = total_cost * markup
    
    return PricingCalculation(
        material_cost=round(material_cost + finishing_cost, 2),
        labor_cost=round(labor_cost, 2),
        total_cost=round(total_cost, 2),
        suggested_price=round(suggested_price, 2),
        profit_margin=round((suggested_price - total_cost) / suggested_price * 100, 1) if suggested_price > 0 else 0,
        breakdown={
            "dimensions": f"{width}\" x {height}\"",
            "square_feet": round(sqft, 2),
            "substrate": substrate,
            "substrate_cost_per_sqft": cost_per_sqft,
            "print_cost": round(print_cost, 2),
            "finishing_cost": round(finishing_cost, 2)
        }
    )


async def calculate_apparel(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for apparel decoration"""
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
    
    material_cost = (garment_cost + decoration_cost) * quantity
    
    hourly_rate = defaults.get("hourly_rate", 75)
    time_per_item = 0.1 if transfer_type == "screen_print" else 0.25
    labor_cost = time_per_item * quantity * hourly_rate
    
    setup_fee = data.setup_fee or 25.0
    if transfer_type == "screen_print":
        setup_fee += (data.num_colors or 1) * 15
    
    total_cost = material_cost + labor_cost + setup_fee
    
    markup = defaults.get("apparel_markup", 2.0)
    suggested_price = total_cost * markup
    
    discount = get_quantity_discount(quantity, {"12": 0.05, "24": 0.10, "48": 0.15, "100": 0.20})
    if discount > 0:
        suggested_price *= (1 - discount)
    
    return PricingCalculation(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost + setup_fee, 2),
        total_cost=round(total_cost, 2),
        suggested_price=round(suggested_price, 2),
        profit_margin=round((suggested_price - total_cost) / suggested_price * 100, 1) if suggested_price > 0 else 0,
        breakdown={
            "apparel_type": apparel_type,
            "garment_cost": garment_cost,
            "transfer_type": transfer_type,
            "decoration_cost_per_location": transfer_costs.get(transfer_type, 3.00),
            "print_locations": num_locations,
            "setup_fee": setup_fee,
            "quantity_discount": discount
        }
    )


async def calculate_vehicle_graphics(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for vehicle graphics"""
    vehicle_sqft = {
        "car_sedan": 150,
        "car_suv": 200,
        "van_mini": 180,
        "van_cargo": 250,
        "van_sprinter": 300,
        "box_truck_12ft": 400,
        "box_truck_16ft": 500,
        "box_truck_24ft": 650,
        "trailer": 800,
        "semi": 1000,
        "other": data.estimated_vehicle_sqft or 200
    }
    
    coverage_multipliers = {
        "spot": 0.15,
        "partial": 0.35,
        "half": 0.50,
        "full": 1.0
    }
    
    vehicle_type = data.vehicle_type or "van_cargo"
    base_sqft = vehicle_sqft.get(vehicle_type, 200)
    
    coverage = data.coverage_type or "partial"
    actual_sqft = base_sqft * coverage_multipliers.get(coverage, 0.35)
    
    material_cost_sqft = 4.00
    wrap_type = getattr(data, 'wrap_type', None)
    if wrap_type == "color_change":
        material_cost_sqft = 6.00
    elif wrap_type == "printed":
        material_cost_sqft = 5.00
    
    material_cost = actual_sqft * material_cost_sqft * quantity
    
    hourly_rate = defaults.get("hourly_rate", 75)
    install_rate = 100
    hours_per_sqft = 0.15
    labor_hours = actual_sqft * hours_per_sqft * quantity
    labor_cost = labor_hours * install_rate
    
    design_cost = 0
    include_design = getattr(data, 'include_design', False)
    if include_design:
        complexity = data.complexity or 2
        design_cost = 150 * complexity
    
    total_cost = material_cost + labor_cost + design_cost
    
    markup = defaults.get("vehicle_markup", 2.0)
    suggested_price = total_cost * markup
    
    return PricingCalculation(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost + design_cost, 2),
        total_cost=round(total_cost, 2),
        suggested_price=round(suggested_price, 2),
        profit_margin=round((suggested_price - total_cost) / suggested_price * 100, 1) if suggested_price > 0 else 0,
        breakdown={
            "vehicle_type": vehicle_type,
            "coverage": coverage,
            "base_sqft": base_sqft,
            "actual_sqft": round(actual_sqft, 2),
            "material_cost_per_sqft": material_cost_sqft,
            "install_hours": round(labor_hours, 2),
            "design_cost": design_cost
        }
    )


async def calculate_custom(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculate pricing for custom items"""
    material_cost = (data.material_cost_override or 0) * quantity
    
    hourly_rate = defaults.get("hourly_rate", 75)
    labor_hours = data.labor_hours or 1
    labor_cost = labor_hours * hourly_rate * quantity
    
    total_cost = material_cost + labor_cost
    
    markup = defaults.get("default_markup", 2.5)
    suggested_price = total_cost * markup
    
    if data.custom_price:
        suggested_price = data.custom_price * quantity
    
    return PricingCalculation(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost, 2),
        total_cost=round(total_cost, 2),
        suggested_price=round(suggested_price, 2),
        profit_margin=round((suggested_price - total_cost) / suggested_price * 100, 1) if suggested_price > 0 else 0,
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


# ============== IMPORT AND INCLUDE ROUTERS ==============
from routes.auth import router as auth_router, users_router, admin_router
from routes.customers import router as customers_router
from routes.quotes import router as quotes_router
from routes.jobs import router as jobs_router
from routes.invoices import router as invoices_router
from routes.employees import employees_router, timeclock_router, payroll_router
from routes.pricing import router as pricing_router
from routes.portal import router as portal_router
from routes.webstores import webstores_router, products_router

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
