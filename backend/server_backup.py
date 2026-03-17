from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, date, timedelta
from enum import Enum
import jwt
from passlib.context import CryptContext
import secrets

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

# Create the main app
app = FastAPI(title="SignGuy AI API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== ENUMS ==============
class CustomerStatus(str, Enum):
    LEAD = "lead"
    ACTIVE = "active"
    INACTIVE = "inactive"

class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    DECLINED = "declined"

class JobStatus(str, Enum):
    QUOTED = "quoted"
    APPROVED = "approved"
    IN_PRODUCTION = "in_production"
    INSTALLED = "installed"
    COMPLETE = "complete"
    ARCHIVED = "archived"

class JobActivityType(str, Enum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    QUOTE_CONVERTED = "quote_converted"
    INVOICE_CREATED = "invoice_created"
    ITEM_ADDED = "item_added"
    ITEM_UPDATED = "item_updated"
    ITEM_DELETED = "item_deleted"
    NOTE_ADDED = "note_added"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    UNARCHIVED = "unarchived"

class JobItemStatus(str, Enum):
    PENDING = "pending"
    IN_PRODUCTION = "in_production"
    DONE = "done"

class JobItemType(str, Enum):
    # Legacy types (kept for backwards compatibility)
    BANNER = "banner"
    YARD_SIGN = "yard_sign"
    DECAL = "decal"
    WRAP = "wrap"
    INSTALL = "install"
    DESIGN = "design"
    VEHICLE_GRAPHICS = "vehicle_graphics"
    WINDOW_GRAPHICS = "window_graphics"
    DIMENSIONAL_LETTERS = "dimensional_letters"
    MONUMENT_SIGN = "monument_sign"
    OTHER = "other"

# ============== PRICING CALCULATOR ENUMS ==============

class PricingCategory(str, Enum):
    PROMOTIONAL = "promotional"
    CUT_VINYL = "cut_vinyl"
    SERVICES = "services"
    DIGITAL_PRINT = "digital_print"
    RIGID_SIGNS = "rigid_signs"
    APPAREL = "apparel"
    VEHICLE_GRAPHICS = "vehicle_graphics"
    CUSTOM = "custom"

class ServiceType(str, Enum):
    DESIGN = "design"
    INSTALLATION = "installation"
    REMOVAL = "removal"
    SITE_SURVEY = "site_survey"
    CONSULTATION = "consultation"
    TRAVEL = "travel"
    OTHER_LABOR = "other_labor"

class ApparelType(str, Enum):
    TSHIRT = "tshirt"
    HOODIE = "hoodie"
    HAT = "hat"
    POLO = "polo"
    TANK = "tank"
    LONGSLEEVE = "longsleeve"
    JACKET = "jacket"
    OTHER = "other"

class TransferType(str, Enum):
    HTV = "htv"
    SCREEN_PRINT = "screen_print"
    DTF = "dtf"
    SUBLIMATION = "sublimation"
    EMBROIDERY = "embroidery"

class VinylType(str, Enum):
    ORACAL_651 = "oracal_651"
    ORACAL_751 = "oracal_751"
    ORACAL_951 = "oracal_951"
    AVERY_HP750 = "avery_hp750"
    REFLECTIVE = "reflective"
    SPECIALTY = "specialty"
    CUSTOM = "custom"

class PrintMaterial(str, Enum):
    BANNER_13OZ = "banner_13oz"
    BANNER_18OZ = "banner_18oz"
    VINYL_ADHESIVE = "vinyl_adhesive"
    POSTER_PAPER = "poster_paper"
    CANVAS = "canvas"
    BACKLIT = "backlit"
    PERFORATED = "perforated"
    CUSTOM = "custom"

class SubstrateType(str, Enum):
    COROPLAST_4MM = "coroplast_4mm"
    COROPLAST_10MM = "coroplast_10mm"
    ALUMINUM_040 = "aluminum_040"
    ALUMINUM_063 = "aluminum_063"
    ALUMINUM_080 = "aluminum_080"
    PVC_3MM = "pvc_3mm"
    PVC_6MM = "pvc_6mm"
    ACRYLIC = "acrylic"
    DIBOND = "dibond"
    MDO = "mdo"
    CUSTOM = "custom"

class VehicleType(str, Enum):
    CAR_SEDAN = "car_sedan"
    CAR_SUV = "car_suv"
    VAN_MINI = "van_mini"
    VAN_CARGO = "van_cargo"
    VAN_SPRINTER = "van_sprinter"
    BOX_TRUCK_12FT = "box_truck_12ft"
    BOX_TRUCK_16FT = "box_truck_16ft"
    BOX_TRUCK_24FT = "box_truck_24ft"
    TRAILER = "trailer"
    SEMI = "semi"
    OTHER = "other"

class CoverageType(str, Enum):
    SPOT = "spot"
    PARTIAL = "partial"
    HALF = "half"
    FULL = "full"

class PromoProductType(str, Enum):
    MAGNETS = "magnets"
    YARD_SIGNS = "yard_signs"
    LICENSE_PLATES = "license_plates"
    STICKERS = "stickers"
    BRANDED_ITEMS = "branded_items"
    CUSTOM = "custom"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"

class PayrollTransactionType(str, Enum):
    EARNINGS = "earnings"
    ADVANCE = "advance"
    PAYMENT = "payment"

class ExpenseCategory(str, Enum):
    MATERIALS = "materials"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    UTILITIES = "utilities"
    RENT = "rent"
    INSURANCE = "insurance"
    CELL_PHONE = "cell_phone"
    GARBAGE = "garbage"
    PRINTING_SUPPLIES = "printing_supplies"
    MEALS = "meals"
    ENTERTAINMENT = "entertainment"
    DONATIONS = "donations"
    OFFICE_SUPPLIES = "office_supplies"
    APPAREL = "apparel"
    VEHICLE = "vehicle"
    ADVERTISING = "advertising"
    LEGAL = "legal"
    REPAIRS = "repairs"
    TAXES = "taxes"
    TRAVEL = "travel"
    OTHER = "other"

# ============== MODELS ==============

# Customer Models
class CustomerBase(BaseModel):
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: CustomerStatus = CustomerStatus.LEAD
    notes: Optional[str] = None
    # Portal-related fields
    profile_image_url: Optional[str] = None
    is_tax_exempt: bool = False
    tax_exempt_document_url: Optional[str] = None
    portal_password_hash: Optional[str] = None  # For portal login
    portal_enabled: bool = False
    notification_preferences: Dict[str, bool] = Field(default_factory=lambda: {
        "email_messages": True,
        "email_orders": True,
        "email_approvals": True,
        "email_payments": True
    })

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[CustomerStatus] = None
    notes: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_tax_exempt: Optional[bool] = None
    tax_exempt_document_url: Optional[str] = None
    notification_preferences: Optional[Dict[str, bool]] = None

class Customer(CustomerBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============== CUSTOMER PORTAL MODELS ==============

class MessageType(str, Enum):
    TEXT = "text"
    FILE = "file"
    APPROVAL_REQUEST = "approval_request"
    SYSTEM = "system"

class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_type: str  # "customer" or "shop"
    sender_id: str
    sender_name: str
    message_type: MessageType = MessageType.TEXT
    content: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    is_read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Conversation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    customer_id: str
    subject: str
    related_job_id: Optional[str] = None
    related_quote_id: Optional[str] = None
    last_message_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_message_preview: str = ""
    unread_customer: int = 0  # Unread count for customer
    unread_shop: int = 0  # Unread count for shop
    is_closed: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProofStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"

class ArtworkProof(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    job_id: str
    customer_id: str
    version: int = 1
    file_url: str
    file_name: str
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    status: ProofStatus = ProofStatus.PENDING
    customer_comment: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CustomerNotification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    customer_id: str
    notification_type: str  # "message", "approval", "order_update", "payment", "appointment"
    title: str
    message: str
    link: Optional[str] = None  # Link to relevant page in portal
    related_id: Optional[str] = None  # Related entity ID
    is_read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    PICKUP = "pickup"
    INSTALLATION = "installation"
    SITE_SURVEY = "site_survey"
    OTHER = "other"

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    customer_id: str
    job_id: Optional[str] = None
    appointment_type: AppointmentType
    title: str
    description: Optional[str] = None
    scheduled_date: str  # ISO date
    scheduled_time: str  # HH:MM
    duration_minutes: int = 60
    location: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============== PRICING CONFIGURATION MODELS ==============

class MaterialConfig(BaseModel):
    """Individual material/product configuration with costs"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # vinyl, substrate, print_material, apparel_brand, etc.
    cost_per_unit: float = 0  # Cost per sqft, per piece, etc.
    unit_type: str = "sqft"  # sqft, piece, yard, each
    is_active: bool = True

class PricingDefaults(BaseModel):
    """Default pricing rates and multipliers for a tenant"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    
    # Labor rates
    hourly_rate: float = 75.0
    design_hourly_rate: float = 85.0
    install_hourly_rate: float = 95.0
    
    # Default markups
    default_markup_percent: float = 100.0
    material_markup_percent: float = 50.0
    
    # Minimum charges
    minimum_order: float = 50.0
    minimum_vinyl_charge: float = 25.0
    minimum_print_charge: float = 35.0
    minimum_sign_charge: float = 50.0
    minimum_service_charge: float = 75.0
    minimum_wrap_charge: float = 500.0
    
    # Complexity multipliers (per complexity point 1-10)
    complexity_multiplier_base: float = 1.0  # At complexity 1
    complexity_multiplier_max: float = 2.0   # At complexity 10
    
    # Setup fees by category
    setup_fee_vinyl: float = 15.0
    setup_fee_print: float = 25.0
    setup_fee_apparel_screen: float = 35.0
    setup_fee_apparel_dtf: float = 20.0
    
    # Quantity break thresholds and discounts
    quantity_breaks: Dict[str, Any] = Field(default_factory=lambda: {
        "break_1": {"min_qty": 10, "discount_percent": 5},
        "break_2": {"min_qty": 25, "discount_percent": 10},
        "break_3": {"min_qty": 50, "discount_percent": 15},
        "break_4": {"min_qty": 100, "discount_percent": 20}
    })
    
    # Per-category time estimates (minutes)
    weeding_time_per_sqft: float = 5.0
    application_time_per_sqft: float = 3.0
    print_time_per_sqft: float = 1.0
    laminate_time_per_sqft: float = 1.5
    
    # Travel
    mileage_rate: float = 0.67
    minimum_travel_charge: float = 50.0
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============== ENHANCED JOB ITEM WITH PRICING CALCULATOR ==============

class PricingCalculation(BaseModel):
    """Detailed pricing breakdown for a job item"""
    # Costs
    material_cost: float = 0
    labor_cost: float = 0
    setup_cost: float = 0
    additional_costs: float = 0
    
    # Totals
    production_cost: float = 0
    suggested_price: float = 0
    
    # Margin info
    markup_percent: float = 0
    profit_margin_percent: float = 0
    profit_amount: float = 0
    
    # Time estimates
    estimated_labor_minutes: float = 0
    
    # Breakdown details (for transparency)
    breakdown: Dict[str, Any] = Field(default_factory=dict)

class JobItemPricingData(BaseModel):
    """Category-specific pricing inputs for a job item"""
    # Common fields
    category: PricingCategory = PricingCategory.CUSTOM
    complexity: int = 5  # 1-10
    
    # Dimensions (for vinyl, print, signs)
    width_inches: Optional[float] = None
    length_inches: Optional[float] = None
    square_footage: Optional[float] = None  # Auto-calculated or manual
    
    # --- Promotional Items ---
    promo_product_type: Optional[PromoProductType] = None
    unit_cost: Optional[float] = None
    markup_percent: Optional[float] = None
    setup_fee: Optional[float] = None
    
    # --- Cut Vinyl ---
    vinyl_type: Optional[VinylType] = None
    vinyl_colors: List[str] = Field(default_factory=list)
    num_colors: int = 1
    
    # --- Digital Print ---
    print_material: Optional[PrintMaterial] = None
    laminate: bool = False
    laminate_type: Optional[str] = None
    
    # --- Rigid Signs ---
    substrate_type: Optional[SubstrateType] = None
    double_sided: bool = False
    
    # --- Services ---
    service_type: Optional[ServiceType] = None
    estimated_hours: Optional[float] = None
    hourly_rate_override: Optional[float] = None
    num_workers: int = 1
    location_address: Optional[str] = None
    distance_miles: Optional[float] = None
    equipment_required: List[str] = Field(default_factory=list)
    
    # --- Apparel ---
    apparel_type: Optional[ApparelType] = None
    apparel_brand: Optional[str] = None
    transfer_type: Optional[TransferType] = None
    print_locations: List[str] = Field(default_factory=list)  # front, back, left_sleeve, etc.
    num_print_locations: int = 1
    ink_colors: List[str] = Field(default_factory=list)
    size_range: str = "S-XL"
    blank_cost_override: Optional[float] = None
    
    # --- Vehicle Graphics ---
    vehicle_type: Optional[VehicleType] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    coverage_type: Optional[CoverageType] = None
    estimated_vehicle_sqft: Optional[float] = None
    install_difficulty: int = 5  # 1-10
    
    # --- Flat price override (always wins) ---
    price_override: Optional[float] = None
    override_enabled: bool = False

class JobItemEnhanced(BaseModel):
    """Enhanced Job Item with full pricing calculator support"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    
    # Basic info
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None
    
    # Pricing category & data
    pricing_category: PricingCategory = PricingCategory.CUSTOM
    pricing_data: Optional[JobItemPricingData] = None
    pricing_calculation: Optional[PricingCalculation] = None
    
    # Final pricing (may be overridden)
    unit_price: float = 0
    line_total: float = 0
    production_cost: float = 0  # For margin tracking
    
    # Artwork & proofs
    artwork_url: Optional[str] = None
    proof_url: Optional[str] = None
    proof_approved: bool = False
    
    # Tax
    is_taxable: bool = True
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class JobItemEnhancedCreate(BaseModel):
    """Create input for enhanced job item"""
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None
    pricing_category: PricingCategory = PricingCategory.CUSTOM
    pricing_data: Optional[JobItemPricingData] = None
    unit_price: Optional[float] = None
    artwork_url: Optional[str] = None
    proof_url: Optional[str] = None
    proof_approved: bool = False
    is_taxable: bool = True

class JobItemEnhancedUpdate(BaseModel):
    """Update input for enhanced job item"""
    item_type: Optional[JobItemType] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    status: Optional[JobItemStatus] = None
    notes: Optional[str] = None
    pricing_category: Optional[PricingCategory] = None
    pricing_data: Optional[JobItemPricingData] = None
    unit_price: Optional[float] = None
    artwork_url: Optional[str] = None
    proof_url: Optional[str] = None
    proof_approved: Optional[bool] = None
    is_taxable: Optional[bool] = None

# Quote Models
class QuoteLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float
    total: float = 0

class QuoteBase(BaseModel):
    customer_id: str
    line_items: List[QuoteLineItem] = []
    notes: Optional[str] = None
    status: QuoteStatus = QuoteStatus.DRAFT

class QuoteCreate(QuoteBase):
    pass

class QuoteUpdate(BaseModel):
    line_items: Optional[List[QuoteLineItem]] = None
    notes: Optional[str] = None
    status: Optional[QuoteStatus] = None

class Quote(QuoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    total: float = 0
    job_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Job Models
class JobBase(BaseModel):
    customer_id: str
    name: str
    description: Optional[str] = None
    status: JobStatus = JobStatus.QUOTED
    due_date: Optional[str] = None

class JobCreate(JobBase):
    quote_id: Optional[str] = None

class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[JobStatus] = None
    due_date: Optional[str] = None

class Job(JobBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    quote_id: Optional[str] = None
    invoice_id: Optional[str] = None
    subtotal: float = 0
    is_archived: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# JobNote Models (Internal Notes)
class JobNoteBase(BaseModel):
    job_id: str
    content: str
    author: Optional[str] = None

class JobNoteCreate(BaseModel):
    content: str
    author: Optional[str] = None

class JobNote(JobNoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# JobActivity Models (Activity Log)
class JobActivity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    activity_type: JobActivityType
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# JobItem Models (Line Items for Jobs)
class JobItemBase(BaseModel):
    job_id: str
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    unit_price: float = 0
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None

class JobItemCreate(BaseModel):
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    unit_price: float = 0
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None

class JobItemUpdate(BaseModel):
    item_type: Optional[JobItemType] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    status: Optional[JobItemStatus] = None
    notes: Optional[str] = None

class JobItem(JobItemBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    line_total: float = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Invoice Models
class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float = 0
    total: float = 0
    job_item_id: Optional[str] = None

class InvoiceBase(BaseModel):
    customer_id: str
    job_id: Optional[str] = None
    line_items: List[InvoiceLineItem] = []
    total: float = 0
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: Optional[str] = None
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    line_items: Optional[List[InvoiceLineItem]] = None
    total: Optional[float] = None
    status: Optional[InvoiceStatus] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None

class Invoice(InvoiceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    amount_paid: float = 0
    paid_date: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Employee Models
class EmployeeBase(BaseModel):
    name: str
    hourly_rate: float
    is_active: bool = True

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    hourly_rate: Optional[float] = None
    is_active: Optional[bool] = None

class Employee(EmployeeBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Time Clock Models
class TimeLogBase(BaseModel):
    employee_id: str
    action: str  # start_work, break_start, break_end, end_work
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TimeLogCreate(BaseModel):
    employee_id: str
    action: str

class TimeLog(TimeLogBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support

class DailyShiftSummary(BaseModel):
    employee_id: str
    date: str
    work_minutes: float = 0
    break_minutes: float = 0
    net_minutes: float = 0

# Payroll Models
class PayrollTransactionBase(BaseModel):
    employee_id: str
    type: PayrollTransactionType
    amount: float
    description: Optional[str] = None
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())

class PayrollTransactionCreate(PayrollTransactionBase):
    pass

class PayrollTransaction(PayrollTransactionBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PayrollBalance(BaseModel):
    employee_id: str
    employee_name: str
    total_earnings: float = 0
    total_advances: float = 0
    total_payments: float = 0
    balance: float = 0  # Positive = employer owes employee

# Financial Models
class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT = "credit"
    CHECK = "check"
    OTHER = "other"

class SalesEntryBase(BaseModel):
    date: str
    amount: float
    tax_amount: float = 0
    payment_method: PaymentMethod = PaymentMethod.CASH
    description: Optional[str] = None

class SalesEntryCreate(SalesEntryBase):
    pass

class SalesEntry(SalesEntryBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ExpenseEntryBase(BaseModel):
    date: str
    amount: float
    category: ExpenseCategory = ExpenseCategory.OTHER
    description: Optional[str] = None

class ExpenseEntryCreate(ExpenseEntryBase):
    pass

class ExpenseEntry(ExpenseEntryBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FinancialSummary(BaseModel):
    total_sales: float = 0
    total_tax: float = 0
    total_expenses: float = 0
    net_income: float = 0

# Task Models
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    job_id: Optional[str] = None
    due_date: Optional[str] = None
    is_complete: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    job_id: Optional[str] = None
    due_date: Optional[str] = None
    is_complete: Optional[bool] = None

class Task(TaskBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# AI Request Models
class AIRequest(BaseModel):
    tool: str
    input_data: Dict[str, Any]

class AIResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    tool: str
    input_data: Dict[str, Any]
    output: str
    job_id: Optional[str] = None
    customer_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============== USER AUTH MODELS ==============

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    STAFF = "staff"

# ============== TENANT MODELS ==============

class TenantPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

class TenantBase(BaseModel):
    name: str  # Company/Organization name
    slug: str  # URL-friendly identifier
    owner_email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "USA"
    website: Optional[str] = None
    logo_url: Optional[str] = None
    plan: TenantPlan = TenantPlan.FREE
    is_active: bool = True

class TenantCreate(BaseModel):
    name: str
    owner_email: EmailStr
    phone: Optional[str] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None

class Tenant(TenantBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    company_name: Optional[str] = None
    is_active: bool = True
    role: UserRole = UserRole.STAFF
    tenant_id: Optional[str] = None  # Links user to their tenant/company

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None
    role: Optional[UserRole] = None  # First user becomes owner, others default to staff

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserInDB(User):
    hashed_password: str

class UserRoleUpdate(BaseModel):
    role: UserRole

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # seconds

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None

class PasswordReset(BaseModel):
    new_password: str

# ============== PERMISSION DEFINITIONS ==============
# Define what each role can do

class Permission(str, Enum):
    # Customer permissions
    CUSTOMERS_VIEW = "customers:view"
    CUSTOMERS_CREATE = "customers:create"
    CUSTOMERS_EDIT = "customers:edit"
    CUSTOMERS_DELETE = "customers:delete"
    
    # Quote permissions
    QUOTES_VIEW = "quotes:view"
    QUOTES_CREATE = "quotes:create"
    QUOTES_EDIT = "quotes:edit"
    QUOTES_DELETE = "quotes:delete"
    QUOTES_CONVERT = "quotes:convert"
    
    # Job permissions
    JOBS_VIEW = "jobs:view"
    JOBS_CREATE = "jobs:create"
    JOBS_EDIT = "jobs:edit"
    JOBS_DELETE = "jobs:delete"
    
    # Invoice permissions
    INVOICES_VIEW = "invoices:view"
    INVOICES_CREATE = "invoices:create"
    INVOICES_EDIT = "invoices:edit"
    INVOICES_DELETE = "invoices:delete"
    
    # Time Clock permissions
    TIMECLOCK_VIEW_OWN = "timeclock:view_own"
    TIMECLOCK_VIEW_ALL = "timeclock:view_all"
    TIMECLOCK_CLOCK_IN = "timeclock:clock_in"
    TIMECLOCK_EDIT = "timeclock:edit"
    
    # Payroll permissions
    PAYROLL_VIEW = "payroll:view"
    PAYROLL_EDIT = "payroll:edit"
    
    # Financial permissions
    FINANCIALS_VIEW = "financials:view"
    FINANCIALS_CREATE = "financials:create"
    FINANCIALS_EDIT = "financials:edit"
    FINANCIALS_DELETE = "financials:delete"
    
    # User management permissions
    USERS_VIEW = "users:view"
    USERS_CREATE = "users:create"
    USERS_EDIT = "users:edit"
    USERS_DELETE = "users:delete"
    USERS_MANAGE_ROLES = "users:manage_roles"
    
    # Webstore permissions
    WEBSTORES_VIEW = "webstores:view"
    WEBSTORES_CREATE = "webstores:create"
    WEBSTORES_EDIT = "webstores:edit"
    WEBSTORES_DELETE = "webstores:delete"
    
    # AI Tools permissions
    AI_TOOLS_USE = "ai_tools:use"
    
    # Settings permissions
    SETTINGS_VIEW = "settings:view"
    SETTINGS_EDIT = "settings:edit"

# Role permission matrix
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.OWNER: list(Permission),  # Owner has ALL permissions
    
    UserRole.ADMIN: [
        # Full access to customers, quotes, jobs, invoices
        Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_CREATE, Permission.CUSTOMERS_EDIT, Permission.CUSTOMERS_DELETE,
        Permission.QUOTES_VIEW, Permission.QUOTES_CREATE, Permission.QUOTES_EDIT, Permission.QUOTES_DELETE, Permission.QUOTES_CONVERT,
        Permission.JOBS_VIEW, Permission.JOBS_CREATE, Permission.JOBS_EDIT, Permission.JOBS_DELETE,
        Permission.INVOICES_VIEW, Permission.INVOICES_CREATE, Permission.INVOICES_EDIT, Permission.INVOICES_DELETE,
        # Full time clock access
        Permission.TIMECLOCK_VIEW_OWN, Permission.TIMECLOCK_VIEW_ALL, Permission.TIMECLOCK_CLOCK_IN, Permission.TIMECLOCK_EDIT,
        # View-only for payroll and financials
        Permission.PAYROLL_VIEW,
        Permission.FINANCIALS_VIEW,
        # View-only for users (no role management)
        Permission.USERS_VIEW,
        # Full webstore access
        Permission.WEBSTORES_VIEW, Permission.WEBSTORES_CREATE, Permission.WEBSTORES_EDIT, Permission.WEBSTORES_DELETE,
        # AI Tools
        Permission.AI_TOOLS_USE,
        # View settings only
        Permission.SETTINGS_VIEW,
    ],
    
    UserRole.STAFF: [
        # View-only for customers, quotes, jobs
        Permission.CUSTOMERS_VIEW,
        Permission.QUOTES_VIEW,
        Permission.JOBS_VIEW,
        # No invoice access
        # Own time clock only
        Permission.TIMECLOCK_VIEW_OWN, Permission.TIMECLOCK_CLOCK_IN,
        # View webstores only
        Permission.WEBSTORES_VIEW,
        # AI Tools
        Permission.AI_TOOLS_USE,
    ],
}

def has_permission(user: UserInDB, permission: Permission) -> bool:
    """Check if a user has a specific permission"""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions

def require_permission(permission: Permission):
    """Dependency to require a specific permission"""
    async def permission_checker(current_user: UserInDB = Depends(get_current_active_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required: {permission.value}"
            )
        return current_user
    return permission_checker

def require_any_permission(*permissions: Permission):
    """Dependency to require any of the specified permissions"""
    async def permission_checker(current_user: UserInDB = Depends(get_current_active_user)):
        for perm in permissions:
            if has_permission(current_user, perm):
                return current_user
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied. Required one of: {[p.value for p in permissions]}"
        )
    return permission_checker

# ============== MAGIC LINK MODELS ==============

class MagicLinkType(str, Enum):
    QUOTE = "quote"
    JOB = "job"
    INVOICE = "invoice"

class MagicLink(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    resource_type: MagicLinkType
    resource_id: str
    customer_email: Optional[str] = None
    expires_at: str  # ISO datetime
    is_used: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MagicLinkCreate(BaseModel):
    resource_type: MagicLinkType
    resource_id: str
    customer_email: Optional[str] = None
    expires_in_days: int = 7  # Default 7 days

# Webstore Models
class FundraiserCampaign(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    goal: float
    start_date: str
    end_date: str
    organizer: str
    payout_rules: Optional[str] = None
    products: List[str] = []
    total_raised: float = 0
    status: str = "active"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FundraiserCampaignCreate(BaseModel):
    name: str
    goal: float
    start_date: str
    end_date: str
    organizer: str
    payout_rules: Optional[str] = None
    products: List[str] = []

class B2BStore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    contact_email: str
    login_password: str
    allowed_products: List[str] = []
    discount_percent: float = 0
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class B2BStoreCreate(BaseModel):
    company_name: str
    contact_email: str
    login_password: str
    allowed_products: List[str] = []
    discount_percent: float = 0

class WebstoreOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_type: str  # fundraiser or b2b
    store_id: str
    items: List[Dict[str, Any]] = []
    total: float = 0
    status: str = "pending"
    job_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WebstoreOrderCreate(BaseModel):
    store_type: str
    store_id: str
    items: List[Dict[str, Any]]
    total: float

# ============== NEW WEBSTORE SYSTEM ==============

class WebstoreType(str, Enum):
    BUSINESS = "business"
    FUNDRAISER = "fundraiser"
    CREATOR = "creator"

class WebstoreStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING = "pending"

class ProductCategory(str, Enum):
    APPAREL = "apparel"
    SIGNS = "signs"
    DECALS = "decals"
    PROMOTIONAL = "promotional"
    OTHER = "other"

# Master Product Catalog - owned by sign shop
class ProductVariant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "Small / Red"
    size: Optional[str] = None
    color: Optional[str] = None
    sku: Optional[str] = None
    additional_cost: float = 0  # Added to base cost for this variant
    is_available: bool = True

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    name: str
    description: Optional[str] = None
    category: ProductCategory = ProductCategory.OTHER
    base_cost: float  # What it costs the shop
    retail_price: float  # Default selling price
    image_url: Optional[str] = None
    has_variants: bool = False
    variants: List[ProductVariant] = []
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: ProductCategory = ProductCategory.OTHER
    base_cost: float
    retail_price: float
    image_url: Optional[str] = None
    has_variants: bool = False
    variants: List[Dict[str, Any]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    base_cost: Optional[float] = None
    retail_price: Optional[float] = None
    image_url: Optional[str] = None
    has_variants: Optional[bool] = None
    variants: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

# Webstore - child of sign shop
class WebstoreBranding(BaseModel):
    logo_url: Optional[str] = None
    primary_color: str = "#0D9488"  # Default teal
    banner_url: Optional[str] = None

class Webstore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    name: str
    store_type: WebstoreType
    owner_name: str  # Business name, organization, or individual
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    description: Optional[str] = None
    status: WebstoreStatus = WebstoreStatus.ACTIVE
    is_public: bool = True
    branding: WebstoreBranding = Field(default_factory=WebstoreBranding)
    # Fundraiser-specific fields
    fundraiser_goal: Optional[float] = None
    fundraiser_start_date: Optional[str] = None
    fundraiser_end_date: Optional[str] = None
    fundraiser_profit_percent: float = 0  # % of profit going to fundraiser
    # Creator-specific fields
    creator_commission_type: str = "percentage"  # "percentage" or "fixed"
    creator_commission_value: float = 0  # % or $ amount
    # Tracking
    total_sales: float = 0
    total_orders: int = 0
    total_profit: float = 0
    payout_owed: float = 0  # Amount owed to fundraiser/creator
    payout_paid: float = 0  # Amount already paid out
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WebstoreCreate(BaseModel):
    name: str
    store_type: WebstoreType
    owner_name: str
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = True
    branding: Optional[Dict[str, Any]] = None
    # Fundraiser fields
    fundraiser_goal: Optional[float] = None
    fundraiser_start_date: Optional[str] = None
    fundraiser_end_date: Optional[str] = None
    fundraiser_profit_percent: float = 0
    # Creator fields
    creator_commission_type: str = "percentage"
    creator_commission_value: float = 0

class WebstoreUpdate(BaseModel):
    name: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WebstoreStatus] = None
    is_public: Optional[bool] = None
    branding: Optional[Dict[str, Any]] = None
    fundraiser_goal: Optional[float] = None
    fundraiser_start_date: Optional[str] = None
    fundraiser_end_date: Optional[str] = None
    fundraiser_profit_percent: Optional[float] = None
    creator_commission_type: Optional[str] = None
    creator_commission_value: Optional[float] = None

# Product assignment to webstore (with optional price override)
class WebstoreProduct(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    webstore_id: str
    product_id: str
    is_enabled: bool = True
    price_override: Optional[float] = None  # If set, overrides retail_price
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WebstoreProductCreate(BaseModel):
    webstore_id: str
    product_id: str
    is_enabled: bool = True
    price_override: Optional[float] = None

# Enhanced order for new system
class WebstoreOrderItem(BaseModel):
    product_id: str
    product_name: str
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    quantity: int
    unit_price: float  # Price charged
    base_cost: float  # Cost to shop
    total: float
    profit: float

class WebstoreOrderV2(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Multi-tenancy support
    webstore_id: str
    webstore_name: str
    store_type: WebstoreType
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    items: List[WebstoreOrderItem] = []
    subtotal: float = 0
    tax: float = 0
    shipping: float = 0
    total: float = 0
    total_cost: float = 0  # Total base cost
    total_profit: float = 0
    shop_profit: float = 0  # Profit kept by shop
    payout_amount: float = 0  # Amount owed to fundraiser/creator
    status: str = "pending"  # pending, processing, production, shipped, completed, cancelled
    job_id: Optional[str] = None
    payment_status: str = "unpaid"  # unpaid, paid, refunded
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WebstoreOrderV2Create(BaseModel):
    webstore_id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    items: List[Dict[str, Any]]
    tax: float = 0
    shipping: float = 0
    notes: Optional[str] = None

# ============== ROUTES ==============

# Root
@api_router.get("/")
async def root():
    return {"message": "SignGuy AI API", "version": "1.0.0"}

# Health Check
@api_router.get("/health")
async def health():
    return {"status": "healthy"}

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

# ============== TENANT HELPER FUNCTIONS ==============

def generate_tenant_slug(name: str) -> str:
    """Generate a URL-friendly slug from tenant name"""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]  # Limit length

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

# -------------- AUTH ROUTES --------------
@api_router.post("/auth/register", response_model=Token)
async def register(input: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": input.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Self-registration always creates a new tenant (company) and the user becomes owner
    # Staff users should be added by the owner/admin, not self-registered
    company_name = input.company_name or f"{input.full_name}'s Sign Shop"
    
    # Create tenant for this user
    tenant = Tenant(
        name=company_name,
        slug=generate_tenant_slug(company_name),
        owner_email=input.email.lower(),
    )
    tenant_doc = tenant.model_dump()
    await db.tenants.insert_one(tenant_doc)
    tenant_id = tenant.id
    logger.info(f"Created new tenant: {tenant.name} ({tenant.id})")
    
    # Self-registering user is always the owner of their tenant
    role = UserRole.OWNER
    
    # Create new user
    hashed_password = get_password_hash(input.password)
    user = UserInDB(
        email=input.email.lower(),
        full_name=input.full_name,
        company_name=input.company_name,
        role=role,
        tenant_id=tenant_id,
        hashed_password=hashed_password
    )
    doc = user.model_dump()
    await db.users.insert_one(doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token)

@api_router.post("/auth/login", response_model=Token)
async def login(input: UserLogin):
    # Find user by email
    user = await db.users.find_one({"email": input.email.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(input.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account is disabled")
    
    # Create access token - extended expiry if "remember me" is checked
    if input.remember_me:
        expires_delta = timedelta(days=30)  # 30 days for "remember me"
        expires_in = 30 * 24 * 60 * 60  # 30 days in seconds
    else:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    access_token = create_access_token(data={"sub": user["id"]}, expires_delta=expires_delta)
    
    return Token(access_token=access_token, expires_in=expires_in)

@api_router.get("/users/me", response_model=User)
async def get_current_user_profile(current_user: UserInDB = Depends(get_current_active_user)):
    # Return user without hashed_password
    return User(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        is_active=current_user.is_active,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@api_router.get("/users/me/permissions")
async def get_current_user_permissions(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all permissions for the current user"""
    permissions = ROLE_PERMISSIONS.get(current_user.role, [])
    return {
        "role": current_user.role.value,
        "permissions": [p.value for p in permissions]
    }

@api_router.put("/users/me", response_model=User)
async def update_current_user_profile(
    full_name: Optional[str] = None,
    company_name: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    update_data = {}
    if full_name is not None:
        update_data["full_name"] = full_name
    if company_name is not None:
        update_data["company_name"] = company_name
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.users.update_one({"id": current_user.id}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    return User(**{k: v for k, v in updated_user.items() if k != "hashed_password"})

# -------------- ADMIN USER MANAGEMENT --------------
@api_router.get("/admin/users", response_model=List[User])
async def list_all_users(current_user: UserInDB = Depends(get_current_active_user)):
    """List all users - requires USERS_VIEW permission"""
    if not has_permission(current_user, Permission.USERS_VIEW):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot view users")
    
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    return [User(**u) for u in users]

@api_router.post("/admin/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    input: PasswordReset,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Admin resets a user's password - requires USERS_EDIT permission"""
    if not has_permission(current_user, Permission.USERS_EDIT):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot reset passwords")
    
    # Find target user
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only owner can reset another owner's password
    if target_user.get("role") == UserRole.OWNER.value and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can reset owner passwords")
    
    # Validate new password
    if len(input.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Hash and update password
    hashed_password = get_password_hash(input.new_password)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Password reset successfully for {target_user['email']}"}

@api_router.put("/admin/users/{user_id}/status")
async def admin_toggle_user_status(
    user_id: str,
    is_active: bool,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Admin enables/disables a user account - requires USERS_EDIT permission"""
    if not has_permission(current_user, Permission.USERS_EDIT):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot modify user status")
    
    # Prevent disabling own account
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account status")
    
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only owner can disable another owner
    if target_user.get("role") == UserRole.OWNER.value and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can modify owner accounts")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    status_text = "enabled" if is_active else "disabled"
    return {"message": f"User {target_user['email']} has been {status_text}"}

@api_router.put("/admin/users/{user_id}/role")
async def admin_update_user_role(
    user_id: str,
    input: UserRoleUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a user's role - requires USERS_MANAGE_ROLES permission (Owner only)"""
    if not has_permission(current_user, Permission.USERS_MANAGE_ROLES):
        raise HTTPException(status_code=403, detail="Permission denied: Only owners can manage roles")
    
    # Prevent changing own role
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own role")
    
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update role
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": input.role.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"User {target_user['email']} role updated to {input.role.value}"}

@api_router.post("/admin/users/create", response_model=User)
async def admin_create_user(
    input: UserCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Admin creates a new user - requires USERS_CREATE permission"""
    if not has_permission(current_user, Permission.USERS_CREATE):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot create users")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": input.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Only owner can create another owner
    if input.role == UserRole.OWNER and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can create owner accounts")
    
    # Create new user with same tenant as current user
    hashed_password = get_password_hash(input.password)
    user = UserInDB(
        email=input.email.lower(),
        full_name=input.full_name,
        company_name=input.company_name,
        role=input.role or UserRole.STAFF,
        tenant_id=current_user.tenant_id,  # Same tenant as creator
        hashed_password=hashed_password
    )
    doc = user.model_dump()
    await db.users.insert_one(doc)
    
    return User(**{k: v for k, v in doc.items() if k != "hashed_password"})

# -------------- TENANT ROUTES --------------
@api_router.get("/tenant/current")
async def get_current_tenant_info(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get the current user's tenant information"""
    if not current_user.tenant_id:
        raise HTTPException(status_code=404, detail="No tenant associated with this user")
    
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant

@api_router.put("/tenant/settings")
async def update_tenant_settings(
    input: TenantUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update tenant settings - requires SETTINGS_EDIT permission or Owner role"""
    if not has_permission(current_user, Permission.SETTINGS_EDIT):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot edit settings")
    
    if not current_user.tenant_id:
        raise HTTPException(status_code=404, detail="No tenant associated with this user")
    
    # Build update dict
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.tenants.update_one(
        {"id": current_user.tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    return tenant

# -------------- MAGIC LINKS (CUSTOMER PORTAL) --------------
@api_router.post("/magic-links", response_model=MagicLink)
async def create_magic_link(
    input: MagicLinkCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a magic link for customer portal access"""
    # Verify the resource exists
    if input.resource_type == MagicLinkType.QUOTE:
        resource = await db.quotes.find_one({"id": input.resource_id}, {"_id": 0})
    elif input.resource_type == MagicLinkType.JOB:
        resource = await db.jobs.find_one({"id": input.resource_id}, {"_id": 0})
    elif input.resource_type == MagicLinkType.INVOICE:
        resource = await db.invoices.find_one({"id": input.resource_id}, {"_id": 0})
    else:
        raise HTTPException(status_code=400, detail="Invalid resource type")
    
    if not resource:
        raise HTTPException(status_code=404, detail=f"{input.resource_type.value.capitalize()} not found")
    
    # Calculate expiry
    expires_at = datetime.now(timezone.utc) + timedelta(days=input.expires_in_days)
    
    # Create magic link
    magic_link = MagicLink(
        resource_type=input.resource_type,
        resource_id=input.resource_id,
        customer_email=input.customer_email,
        expires_at=expires_at.isoformat()
    )
    
    await db.magic_links.insert_one(magic_link.model_dump())
    
    return magic_link

@api_router.get("/magic-links")
async def list_magic_links(
    resource_type: Optional[MagicLinkType] = None,
    resource_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List magic links (optionally filtered)"""
    query = {}
    if resource_type:
        query["resource_type"] = resource_type.value
    if resource_id:
        query["resource_id"] = resource_id
    
    links = await db.magic_links.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return links

@api_router.delete("/magic-links/{link_id}")
async def revoke_magic_link(
    link_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Revoke/delete a magic link"""
    result = await db.magic_links.delete_one({"id": link_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Magic link not found")
    return {"message": "Magic link revoked"}

# Public endpoint - no auth required (Magic Link Access)
@api_router.get("/portal/magic/{token}")
async def access_portal_via_magic_link(token: str):
    """Access customer portal via magic link (public endpoint)"""
    # Find the magic link
    magic_link = await db.magic_links.find_one({"token": token}, {"_id": 0})
    
    if not magic_link:
        raise HTTPException(status_code=404, detail="Invalid or expired link")
    
    # Check expiry
    expires_at = datetime.fromisoformat(magic_link["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=410, detail="This link has expired")
    
    # Get the resource
    resource_type = magic_link["resource_type"]
    resource_id = magic_link["resource_id"]
    
    if resource_type == "quote":
        resource = await db.quotes.find_one({"id": resource_id}, {"_id": 0})
        # Get customer info
        if resource:
            customer = await db.customers.find_one({"id": resource.get("customer_id")}, {"_id": 0})
    elif resource_type == "job":
        resource = await db.jobs.find_one({"id": resource_id}, {"_id": 0})
        if resource:
            customer = await db.customers.find_one({"id": resource.get("customer_id")}, {"_id": 0})
            # Get job items
            job_items = await db.job_items.find({"job_id": resource_id}, {"_id": 0}).to_list(100)
            resource["items"] = job_items
    elif resource_type == "invoice":
        resource = await db.invoices.find_one({"id": resource_id}, {"_id": 0})
        if resource:
            customer = await db.customers.find_one({"id": resource.get("customer_id")}, {"_id": 0})
    else:
        raise HTTPException(status_code=400, detail="Invalid resource type")
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return {
        "resource_type": resource_type,
        "resource": resource,
        "customer": customer,
        "link_expires_at": magic_link["expires_at"]
    }

# -------------- CUSTOMERS --------------
@api_router.post("/customers", response_model=Customer)
async def create_customer(
    input: CustomerCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    customer = Customer(**input.model_dump())
    customer.tenant_id = current_user.tenant_id  # Assign to user's tenant
    doc = customer.model_dump()
    await db.customers.insert_one(doc)
    return customer

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(
    status: Optional[CustomerStatus] = None,
    search: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    query = {"tenant_id": current_user.tenant_id}  # Tenant scoped
    if status:
        query["status"] = status.value
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    customers = await db.customers.find(query, {"_id": 0}).to_list(1000)
    return customers

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    customer = await db.customers.find_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: str, 
    input: CustomerUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.customers.update_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return customer

@api_router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    result = await db.customers.delete_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted"}

# -------------- QUOTES --------------
@api_router.post("/quotes", response_model=Quote)
async def create_quote(
    input: QuoteCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    # Calculate totals for line items
    line_items = []
    total = 0
    for item in input.line_items:
        item_total = item.quantity * item.unit_price
        line_items.append(QuoteLineItem(
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item_total
        ))
        total += item_total
    
    quote = Quote(
        customer_id=input.customer_id,
        line_items=line_items,
        notes=input.notes,
        status=input.status,
        total=total,
        tenant_id=current_user.tenant_id  # Tenant scoped
    )
    doc = quote.model_dump()
    await db.quotes.insert_one(doc)
    return quote

@api_router.get("/quotes", response_model=List[Quote])
async def get_quotes(
    customer_id: Optional[str] = None,
    status: Optional[QuoteStatus] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    query = {"tenant_id": current_user.tenant_id}  # Tenant scoped
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status.value
    quotes = await db.quotes.find(query, {"_id": 0}).to_list(1000)
    return quotes

@api_router.get("/quotes/{quote_id}", response_model=Quote)
async def get_quote(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    quote = await db.quotes.find_one(
        {"id": quote_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@api_router.put("/quotes/{quote_id}", response_model=Quote)
async def update_quote(
    quote_id: str, 
    input: QuoteUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    quote = await db.quotes.find_one(
        {"id": quote_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.get("job_id"):
        raise HTTPException(status_code=400, detail="Cannot update quote that has been converted to job")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    # Recalculate total if line items changed
    if "line_items" in update_data:
        total = 0
        processed_items = []
        for item in update_data["line_items"]:
            item_dict = item.model_dump() if hasattr(item, 'model_dump') else item
            item_total = item_dict["quantity"] * item_dict["unit_price"]
            item_dict["total"] = item_total
            processed_items.append(item_dict)
            total += item_total
        update_data["line_items"] = processed_items
        update_data["total"] = total
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.quotes.update_one({"id": quote_id}, {"$set": update_data})
    updated_quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    return updated_quote

@api_router.post("/quotes/{quote_id}/convert-to-job", response_model=Job)
async def convert_quote_to_job(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    quote = await db.quotes.find_one(
        {"id": quote_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.get("job_id"):
        raise HTTPException(status_code=400, detail="Quote already converted to job")
    
    # Create job from quote
    job = Job(
        customer_id=quote["customer_id"],
        name=f"Job from Quote #{quote_id[:8]}",
        description=quote.get("notes", ""),
        status=JobStatus.APPROVED,
        quote_id=quote_id,
        subtotal=quote.get("total", 0),
        tenant_id=current_user.tenant_id  # Tenant scoped
    )
    job_doc = job.model_dump()
    await db.jobs.insert_one(job_doc)
    
    # Create JobItems from Quote line items
    for item in quote.get("line_items", []):
        job_item = JobItem(
            job_id=job.id,
            item_type=JobItemType.OTHER,
            description=item.get("description", ""),
            quantity=item.get("quantity", 1),
            unit_price=item.get("unit_price", 0),
            line_total=item.get("total", item.get("quantity", 1) * item.get("unit_price", 0)),
            status=JobItemStatus.PENDING
        )
        await db.job_items.insert_one(job_item.model_dump())
    
    # Update quote with job_id
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"job_id": job.id, "status": QuoteStatus.APPROVED.value}}
    )
    
    # Log activity for quote conversion
    activity = JobActivity(
        job_id=job.id,
        activity_type=JobActivityType.QUOTE_CONVERTED,
        description=f"Job created from Quote #{quote_id[:8]}",
        new_value=quote_id
    )
    await db.job_activities.insert_one(activity.model_dump())
    
    return job

# Helper function to log job activity
async def log_job_activity(job_id: str, activity_type: JobActivityType, description: str, old_value: str = None, new_value: str = None):
    activity = JobActivity(
        job_id=job_id,
        activity_type=activity_type,
        description=description,
        old_value=old_value,
        new_value=new_value
    )
    await db.job_activities.insert_one(activity.model_dump())

# -------------- JOBS --------------
@api_router.post("/jobs", response_model=Job)
async def create_job(
    input: JobCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    job = Job(**input.model_dump())
    job.tenant_id = current_user.tenant_id  # Tenant scoped
    doc = job.model_dump()
    await db.jobs.insert_one(doc)
    
    # Log creation
    await log_job_activity(job.id, JobActivityType.CREATED, f"Job '{job.name}' created")
    
    return job

@api_router.get("/jobs", response_model=List[Job])
async def get_jobs(
    customer_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    filter_type: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    query = {"tenant_id": current_user.tenant_id}  # Tenant scoped
    if customer_id:
        query["customer_id"] = customer_id
    
    # Handle filter types
    if filter_type == "active":
        query["status"] = {"$nin": [JobStatus.COMPLETE.value, JobStatus.ARCHIVED.value]}
        query["is_archived"] = {"$ne": True}
    elif filter_type == "completed":
        query["status"] = JobStatus.COMPLETE.value
        query["is_archived"] = {"$ne": True}
    elif filter_type == "archived":
        query["$or"] = [{"is_archived": True}, {"status": JobStatus.ARCHIVED.value}]
    elif status:
        query["status"] = status.value
    
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return jobs

@api_router.get("/jobs/{job_id}", response_model=Job)
async def get_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@api_router.get("/jobs/{job_id}/details")
async def get_job_details(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get comprehensive job details including related data"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get customer
    customer = await db.customers.find_one({"id": job["customer_id"]}, {"_id": 0})
    
    # Get quote if exists
    quote = None
    if job.get("quote_id"):
        quote = await db.quotes.find_one({"id": job["quote_id"]}, {"_id": 0})
    
    # Get invoice if exists
    invoice = None
    if job.get("invoice_id"):
        invoice = await db.invoices.find_one({"id": job["invoice_id"]}, {"_id": 0})
    
    # Get job items
    job_items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    
    # Get job notes
    notes = await db.job_notes.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Get activity log
    activities = await db.job_activities.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Calculate financial snapshot
    quote_total = quote.get("total", 0) if quote else 0
    invoice_total = invoice.get("total", 0) if invoice else 0
    amount_paid = invoice.get("amount_paid", 0) if invoice else 0
    balance_due = invoice_total - amount_paid if invoice else 0
    
    return {
        "job": job,
        "customer": customer,
        "quote": quote,
        "invoice": invoice,
        "job_items": job_items,
        "notes": notes,
        "activities": activities,
        "financial_snapshot": {
            "quote_total": quote_total,
            "invoice_total": invoice_total,
            "invoice_status": invoice.get("status") if invoice else None,
            "amount_paid": amount_paid,
            "balance_due": balance_due
        }
    }

@api_router.put("/jobs/{job_id}", response_model=Job)
async def update_job(
    job_id: str, 
    input: JobUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Log status change
    if input.status and input.status.value != job.get("status"):
        old_status = job.get("status")
        new_status = input.status.value
        
        if new_status == JobStatus.COMPLETE.value:
            await log_job_activity(job_id, JobActivityType.COMPLETED, f"Job marked as complete", old_status, new_status)
        elif new_status == JobStatus.ARCHIVED.value:
            await log_job_activity(job_id, JobActivityType.ARCHIVED, f"Job archived", old_status, new_status)
        else:
            await log_job_activity(job_id, JobActivityType.STATUS_CHANGED, f"Status changed from {old_status} to {new_status}", old_status, new_status)
    
    await db.jobs.update_one({"id": job_id}, {"$set": update_data})
    updated_job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    return updated_job

@api_router.post("/jobs/{job_id}/archive")
async def archive_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.jobs.update_one({"id": job_id}, {"$set": {"is_archived": True, "status": JobStatus.ARCHIVED.value, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await log_job_activity(job_id, JobActivityType.ARCHIVED, "Job archived", job.get("status"), JobStatus.ARCHIVED.value)
    
    return {"message": "Job archived"}

@api_router.post("/jobs/{job_id}/unarchive")
async def unarchive_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.jobs.update_one({"id": job_id}, {"$set": {"is_archived": False, "status": JobStatus.COMPLETE.value, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await log_job_activity(job_id, JobActivityType.UNARCHIVED, "Job unarchived", JobStatus.ARCHIVED.value, JobStatus.COMPLETE.value)
    
    return {"message": "Job unarchived"}

@api_router.post("/jobs/{job_id}/complete")
async def complete_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    old_status = job.get("status")
    await db.jobs.update_one({"id": job_id}, {"$set": {"status": JobStatus.COMPLETE.value, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await log_job_activity(job_id, JobActivityType.COMPLETED, "Job marked as complete", old_status, JobStatus.COMPLETE.value)
    
    return {"message": "Job marked as complete"}

@api_router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    # Also delete related job items, notes, and activities
    await db.job_items.delete_many({"job_id": job_id})
    await db.job_notes.delete_many({"job_id": job_id})
    await db.job_activities.delete_many({"job_id": job_id})
    result = await db.jobs.delete_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted"}

# -------------- JOB NOTES --------------
@api_router.post("/jobs/{job_id}/notes", response_model=JobNote)
async def create_job_note(job_id: str, input: JobNoteCreate):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    note = JobNote(
        job_id=job_id,
        content=input.content,
        author=input.author
    )
    await db.job_notes.insert_one(note.model_dump())
    await log_job_activity(job_id, JobActivityType.NOTE_ADDED, f"Note added{' by ' + input.author if input.author else ''}")
    
    return note

@api_router.get("/jobs/{job_id}/notes", response_model=List[JobNote])
async def get_job_notes(job_id: str):
    notes = await db.job_notes.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notes

@api_router.delete("/job-notes/{note_id}")
async def delete_job_note(note_id: str):
    result = await db.job_notes.delete_one({"id": note_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted"}

# -------------- JOB ACTIVITIES --------------
@api_router.get("/jobs/{job_id}/activities", response_model=List[JobActivity])
async def get_job_activities(job_id: str):
    activities = await db.job_activities.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return activities

# Helper function to recalculate job subtotal
async def recalculate_job_subtotal(job_id: str):
    job_items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    subtotal = sum(item.get("line_total", 0) for item in job_items)
    await db.jobs.update_one({"id": job_id}, {"$set": {"subtotal": subtotal, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return subtotal

# -------------- JOB ITEMS --------------
@api_router.post("/jobs/{job_id}/items", response_model=JobItem)
async def create_job_item(job_id: str, input: JobItemCreate):
    # Verify job exists
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate line total
    line_total = input.quantity * input.unit_price
    
    job_item = JobItem(
        job_id=job_id,
        item_type=input.item_type,
        description=input.description,
        quantity=input.quantity,
        unit_price=input.unit_price,
        line_total=line_total,
        status=input.status,
        notes=input.notes
    )
    doc = job_item.model_dump()
    await db.job_items.insert_one(doc)
    
    # Recalculate job subtotal
    await recalculate_job_subtotal(job_id)
    
    # Log activity
    await log_job_activity(job_id, JobActivityType.ITEM_ADDED, f"Added item: {input.description}")
    
    return job_item

@api_router.get("/jobs/{job_id}/items", response_model=List[JobItem])
async def get_job_items(job_id: str):
    job_items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    return job_items

@api_router.get("/job-items/{item_id}", response_model=JobItem)
async def get_job_item(item_id: str):
    job_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    if not job_item:
        raise HTTPException(status_code=404, detail="Job item not found")
    return job_item

@api_router.put("/job-items/{item_id}", response_model=JobItem)
async def update_job_item(item_id: str, input: JobItemUpdate):
    job_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    if not job_item:
        raise HTTPException(status_code=404, detail="Job item not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    # Recalculate line total if quantity or unit_price changed
    quantity = update_data.get("quantity", job_item.get("quantity", 1))
    unit_price = update_data.get("unit_price", job_item.get("unit_price", 0))
    update_data["line_total"] = quantity * unit_price
    
    await db.job_items.update_one({"id": item_id}, {"$set": update_data})
    
    # Recalculate job subtotal
    await recalculate_job_subtotal(job_item["job_id"])
    
    # Log activity
    await log_job_activity(job_item["job_id"], JobActivityType.ITEM_UPDATED, f"Updated item: {job_item.get('description', 'Unknown')}")
    
    updated_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    return updated_item

@api_router.delete("/job-items/{item_id}")
async def delete_job_item(item_id: str):
    job_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    if not job_item:
        raise HTTPException(status_code=404, detail="Job item not found")
    
    job_id = job_item["job_id"]
    result = await db.job_items.delete_one({"id": item_id})
    
    # Recalculate job subtotal
    await recalculate_job_subtotal(job_id)
    
    # Log activity
    await log_job_activity(job_id, JobActivityType.ITEM_DELETED, f"Deleted item: {job_item.get('description', 'Unknown')}")
    
    return {"message": "Job item deleted"}

# -------------- INVOICES --------------
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(input: InvoiceCreate):
    invoice = Invoice(**input.model_dump())
    doc = invoice.model_dump()
    await db.invoices.insert_one(doc)
    
    # Link invoice to job if job_id provided
    if input.job_id:
        await db.jobs.update_one({"id": input.job_id}, {"$set": {"invoice_id": invoice.id}})
    
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(
    customer_id: Optional[str] = None,
    status: Optional[InvoiceStatus] = None
):
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status.value
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    return invoices

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@api_router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: str, input: InvoiceUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Recalculate total if line items changed
    if "line_items" in update_data:
        total = 0
        processed_items = []
        for item in update_data["line_items"]:
            item_dict = item.model_dump() if hasattr(item, 'model_dump') else item
            item_total = item_dict.get("quantity", 1) * item_dict.get("unit_price", 0)
            item_dict["total"] = item_total
            processed_items.append(item_dict)
            total += item_total
        update_data["line_items"] = processed_items
        update_data["total"] = total
    
    # If marking as paid, set paid_date
    if input.status == InvoiceStatus.PAID:
        update_data["paid_date"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.invoices.update_one({"id": invoice_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    return invoice

@api_router.post("/invoices/from-job/{job_id}", response_model=Invoice)
async def create_invoice_from_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get job items and create invoice line items
    job_items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    
    invoice_line_items = []
    total = 0
    
    if job_items:
        # Create line items from job items
        for item in job_items:
            line_item = InvoiceLineItem(
                description=item.get("description", ""),
                quantity=item.get("quantity", 1),
                unit_price=item.get("unit_price", 0),
                total=item.get("line_total", 0),
                job_item_id=item.get("id")
            )
            invoice_line_items.append(line_item)
            total += item.get("line_total", 0)
    else:
        # Fallback to job subtotal or quote total
        total = job.get("subtotal", 0)
        if total == 0 and job.get("quote_id"):
            quote = await db.quotes.find_one({"id": job["quote_id"]}, {"_id": 0})
            if quote:
                total = quote.get("total", 0)
    
    invoice = Invoice(
        customer_id=job["customer_id"],
        job_id=job_id,
        line_items=invoice_line_items,
        total=total,
        status=InvoiceStatus.DRAFT
    )
    doc = invoice.model_dump()
    await db.invoices.insert_one(doc)
    
    # Update job with invoice_id
    await db.jobs.update_one({"id": job_id}, {"$set": {"invoice_id": invoice.id}})
    
    # Log activity
    await log_job_activity(job_id, JobActivityType.INVOICE_CREATED, f"Invoice created for {total}", new_value=invoice.id)
    
    return invoice

# -------------- EMPLOYEES --------------
@api_router.post("/employees", response_model=Employee)
async def create_employee(input: EmployeeCreate):
    employee = Employee(**input.model_dump())
    doc = employee.model_dump()
    await db.employees.insert_one(doc)
    return employee

@api_router.get("/employees", response_model=List[Employee])
async def get_employees(is_active: Optional[bool] = None):
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    employees = await db.employees.find(query, {"_id": 0}).to_list(1000)
    return employees

@api_router.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str):
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@api_router.put("/employees/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, input: EmployeeUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    result = await db.employees.update_one({"id": employee_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    return employee

# -------------- TIME CLOCK --------------
@api_router.post("/timeclock", response_model=TimeLog)
async def clock_action(input: TimeLogCreate):
    valid_actions = ["start_work", "break_start", "break_end", "end_work"]
    if input.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
    
    # Get today's logs for this employee
    today = datetime.now(timezone.utc).date().isoformat()
    today_logs = await db.timelogs.find({
        "employee_id": input.employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    
    # Validate sequence
    last_action = today_logs[-1]["action"] if today_logs else None
    
    valid_sequences = {
        None: ["start_work"],
        "start_work": ["break_start", "end_work"],
        "break_start": ["break_end"],
        "break_end": ["break_start", "end_work"],
        "end_work": ["start_work"]
    }
    
    if input.action not in valid_sequences.get(last_action, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid sequence. After '{last_action}', valid actions are: {valid_sequences.get(last_action, [])}"
        )
    
    time_log = TimeLog(
        employee_id=input.employee_id,
        action=input.action,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    doc = time_log.model_dump()
    await db.timelogs.insert_one(doc)
    return time_log

@api_router.get("/timeclock/{employee_id}/today")
async def get_today_logs(employee_id: str):
    today = datetime.now(timezone.utc).date().isoformat()
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    return logs

@api_router.get("/timeclock/{employee_id}/summary")
async def get_shift_summary(employee_id: str, date: Optional[str] = None):
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()
    
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{date}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    
    work_minutes = 0
    break_minutes = 0
    work_start = None
    break_start = None
    
    for log in logs:
        ts = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
        action = log["action"]
        
        if action == "start_work":
            work_start = ts
        elif action == "break_start" and work_start:
            break_start = ts
        elif action == "break_end" and break_start:
            break_minutes += (ts - break_start).total_seconds() / 60
            break_start = None
        elif action == "end_work" and work_start:
            work_minutes += (ts - work_start).total_seconds() / 60
            work_start = None
    
    return {
        "employee_id": employee_id,
        "date": date,
        "work_minutes": round(work_minutes, 2),
        "break_minutes": round(break_minutes, 2),
        "net_minutes": round(work_minutes - break_minutes, 2),
        "net_hours": round((work_minutes - break_minutes) / 60, 2)
    }

@api_router.get("/timeclock/{employee_id}/status")
async def get_clock_status(employee_id: str):
    today = datetime.now(timezone.utc).date().isoformat()
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", -1).to_list(1)
    
    if not logs:
        return {"status": "not_started", "last_action": None}
    
    last_log = logs[0]
    status_map = {
        "start_work": "working",
        "break_start": "on_break",
        "break_end": "working",
        "end_work": "finished"
    }
    
    return {
        "status": status_map.get(last_log["action"], "unknown"),
        "last_action": last_log["action"],
        "last_timestamp": last_log["timestamp"]
    }

# -------------- PAYROLL --------------
@api_router.post("/payroll/transactions", response_model=PayrollTransaction)
async def create_payroll_transaction(input: PayrollTransactionCreate):
    transaction = PayrollTransaction(**input.model_dump())
    doc = transaction.model_dump()
    await db.payroll_transactions.insert_one(doc)
    return transaction

@api_router.get("/payroll/transactions", response_model=List[PayrollTransaction])
async def get_payroll_transactions(
    employee_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    
    transactions = await db.payroll_transactions.find(query, {"_id": 0}).to_list(1000)
    return transactions

@api_router.get("/payroll/balance/{employee_id}", response_model=PayrollBalance)
async def get_payroll_balance(employee_id: str):
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    transactions = await db.payroll_transactions.find({"employee_id": employee_id}, {"_id": 0}).to_list(1000)
    
    total_earnings = sum(t["amount"] for t in transactions if t["type"] == "earnings")
    total_advances = sum(t["amount"] for t in transactions if t["type"] == "advance")
    total_payments = sum(t["amount"] for t in transactions if t["type"] == "payment")
    
    # Balance = Earnings - Advances - Payments
    # Positive = employer owes employee
    # Negative = employee overpaid (has advance)
    balance = total_earnings - total_advances - total_payments
    
    return PayrollBalance(
        employee_id=employee_id,
        employee_name=employee["name"],
        total_earnings=total_earnings,
        total_advances=total_advances,
        total_payments=total_payments,
        balance=balance
    )

@api_router.get("/payroll/report")
async def get_payroll_report(start_date: str, end_date: str):
    employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
    report = []
    
    for emp in employees:
        transactions = await db.payroll_transactions.find({
            "employee_id": emp["id"],
            "date": {"$gte": start_date, "$lte": end_date}
        }, {"_id": 0}).to_list(1000)
        
        earnings = sum(t["amount"] for t in transactions if t["type"] == "earnings")
        advances = sum(t["amount"] for t in transactions if t["type"] == "advance")
        payments = sum(t["amount"] for t in transactions if t["type"] == "payment")
        
        report.append({
            "employee_id": emp["id"],
            "employee_name": emp["name"],
            "period_earnings": earnings,
            "period_advances": advances,
            "period_payments": payments,
            "period_balance": earnings - advances - payments
        })
    
    return report

# -------------- FINANCIALS --------------
@api_router.post("/financials/sales", response_model=SalesEntry)
async def create_sales_entry(input: SalesEntryCreate):
    entry = SalesEntry(**input.model_dump())
    doc = entry.model_dump()
    await db.sales_entries.insert_one(doc)
    return entry

@api_router.get("/financials/sales", response_model=List[SalesEntry])
async def get_sales_entries(start_date: Optional[str] = None, end_date: Optional[str] = None):
    query = {}
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    
    entries = await db.sales_entries.find(query, {"_id": 0}).to_list(1000)
    return entries

@api_router.post("/financials/expenses", response_model=ExpenseEntry)
async def create_expense_entry(input: ExpenseEntryCreate):
    entry = ExpenseEntry(**input.model_dump())
    doc = entry.model_dump()
    await db.expense_entries.insert_one(doc)
    return entry

@api_router.get("/financials/expenses", response_model=List[ExpenseEntry])
async def get_expense_entries(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    category: Optional[ExpenseCategory] = None
):
    query = {}
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    if category:
        query["category"] = category.value
    
    entries = await db.expense_entries.find(query, {"_id": 0}).to_list(1000)
    return entries

@api_router.get("/financials/summary", response_model=FinancialSummary)
async def get_financial_summary(start_date: str, end_date: str):
    sales = await db.sales_entries.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(1000)
    
    expenses = await db.expense_entries.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(1000)
    
    total_sales = sum(s["amount"] for s in sales)
    total_tax = sum(s.get("tax_amount", 0) for s in sales)
    total_expenses = sum(e["amount"] for e in expenses)
    
    return FinancialSummary(
        total_sales=total_sales,
        total_tax=total_tax,
        total_expenses=total_expenses,
        net_income=total_sales - total_expenses
    )

# -------------- TASKS --------------
@api_router.post("/tasks", response_model=Task)
async def create_task(input: TaskCreate):
    task = Task(**input.model_dump())
    doc = task.model_dump()
    await db.tasks.insert_one(doc)
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(job_id: Optional[str] = None, is_complete: Optional[bool] = None):
    query = {}
    if job_id:
        query["job_id"] = job_id
    if is_complete is not None:
        query["is_complete"] = is_complete
    tasks = await db.tasks.find(query, {"_id": 0}).to_list(1000)
    return tasks

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, input: TaskUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    result = await db.tasks.update_one({"id": task_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    return task

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}

# -------------- AI TOOLS --------------
@api_router.post("/ai/generate", response_model=AIResponse)
async def generate_ai_content(request: AIRequest):
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Tools that require image analysis (vision)
    vision_tools = ['font_identifier', 'photo_enhancer', 'image_vectorizer']
    
    # Build prompt based on tool type
    tool_prompts = {
        # Design Tools
        "photo_enhancer": """You are a photo enhancement specialist for sign shops.
Input: {input}

Analyze the image and provide:
1. **Quality Assessment**: Current resolution, noise level, lighting issues
2. **Enhancement Recommendations**:
   - Brightness/contrast adjustments needed
   - Noise reduction suggestions
   - Sharpening requirements
   - Color correction needs
3. **Print Readiness**:
   - Minimum recommended print size at 150 DPI
   - Maximum recommended print size at 300 DPI
   - Warning if resolution is too low for large-format
4. **Two Enhancement Profiles**:
   - Standard Enhanced: For digital/web use
   - Print Optimized: Higher contrast, sharpened for vinyl/banner printing
5. **Processing Notes**: Any artifacts or details that cannot be improved

Note: Provide realistic expectations - do not claim to add details not present in the original.""",

        "image_vectorizer": """You are a vector graphics specialist for sign production.
Input: {input}

Provide vectorization guidance:
1. **Image Analysis**:
   - Complexity assessment (simple/moderate/complex)
   - Number of distinct colors/shapes
   - Edge quality evaluation
2. **Vectorization Strategy** based on complexity level:
   - Path simplification recommendations
   - Anchor point optimization
   - Curve smoothing suggestions
3. **Output Specifications**:
   - Recommended SVG settings
   - EPS compatibility notes
   - Color mode (CMYK for print, RGB for digital)
4. **Potential Issues**:
   - Areas that may not vectorize cleanly
   - Gradients or effects that need attention
   - Transparency handling
5. **File Preparation Checklist**:
   - Pre-processing steps needed
   - Post-vectorization cleanup tips""",

        "font_identifier": """You are a typography expert for sign shops.
Input: {input}

Based on the description, provide:
1. **Top 3 Font Matches** with confidence percentages:
   - Font name, foundry, style
   - Confidence level (high/medium/low)
   - Key identifying characteristics
2. **Alternative Fonts** (similar and free options):
   - Google Fonts alternatives
   - Open source alternatives
   - Premium alternatives
3. **Font Classification**:
   - Category (serif, sans-serif, display, script, etc.)
   - Weight and style
   - Era/style period
4. **Usage Recommendations**:
   - Best applications for this font style
   - Pairing suggestions
   - Size recommendations for signage
5. **Licensing Notes**:
   - If font appears custom/proprietary, note this
   - Flag any potential trademark concerns

Note: If the font appears hand-drawn or custom, clearly indicate this is an approximation.""",

        "ai_sign_designer": """You are an expert sign designer for professional sign shops.
Input: {input}

Create comprehensive sign design concepts:

1. **Design Analysis**:
   - Optimal viewing distance calculation
   - Recommended letter heights for readability
   - Color contrast evaluation (WCAG guidelines for signage)

2. **Layout Concepts** (provide 3-4 variations):
   For each concept include:
   - Text hierarchy (primary, secondary, tertiary)
   - Element positioning and spacing
   - Visual weight distribution
   - Design rationale

3. **Typography Recommendations**:
   - Primary font suggestions (with alternatives)
   - Secondary font pairings
   - Size ratios between elements

4. **Color Specifications**:
   - Exact color values (HEX, RGB, CMYK, Pantone)
   - Day and night visibility considerations
   - Material-specific color adjustments

5. **Technical Notes**:
   - Recommended materials
   - Installation considerations
   - Illumination suggestions if applicable

6. **Compliance Reminders**:
   - ADA considerations if applicable
   - Local signage code factors to verify

Prioritize readability over decoration. Warn if too much text is provided.""",

        "ai_banner_designer": """You are a banner design specialist for promotions and events.
Input: {input}

Create optimized banner designs:

1. **Layout Recommendations** (2-3 variations):
   For each layout:
   - Headline placement and sizing
   - Supporting text hierarchy
   - Call-to-action positioning
   - Image/graphic zones

2. **Typography Specifications**:
   - Minimum font sizes for viewing distance:
     * 2x4ft: 2" minimum for body, 4"+ for headlines
     * 3x6ft: 3" minimum for body, 6"+ for headlines
     * 4x8ft: 4" minimum for body, 8"+ for headlines
   - Recommended fonts for impact
   - Letter spacing adjustments

3. **Color Strategy**:
   - High-contrast color combinations
   - Background recommendations
   - Event-appropriate color psychology

4. **Print Specifications**:
   - Bleed requirements (typically 0.5")
   - Safe area margins
   - Resolution requirements (100-150 DPI for large format)

5. **Content Optimization**:
   - Message prioritization
   - What to include vs. omit
   - Readability at distance check

Warn if message will be unreadable at typical viewing distance.""",

        "mockup_creator": """You are a mockup specialist for sign shop presentations.
Input: {input}

Provide mockup creation guidance:

1. **Scene Selection**:
   - Recommended mockup environment
   - Angle and perspective suggestions
   - Lighting conditions (day/night/both)

2. **Artwork Placement Guide**:
   - Scale calculations for realistic sizing
   - Perspective transformation notes
   - Shadow and reflection requirements

3. **Multiple View Recommendations**:
   - Primary view (most impactful angle)
   - Secondary views (different perspectives)
   - Detail views if applicable

4. **Realism Checklist**:
   - Lighting direction consistency
   - Shadow softness and direction
   - Environmental reflections
   - Material texture simulation

5. **Presentation Tips**:
   - Before/after comparison layout
   - Context elements to include
   - Customer approval workflow

6. **Technical Specifications**:
   - Output resolution for presentations
   - File format recommendations
   - Color profile considerations

Label all mockups clearly as previews, not final product representations.""",

        # Branding Tools
        "logo_creator": """You are a logo design consultant for sign shops and their clients.
Input: {input}

Generate comprehensive logo concepts:

1. **Creative Directions** (provide 4-5 distinct concepts):
   For each concept:
   - Concept name and description
   - Design approach (wordmark, symbol, combination, etc.)
   - Key visual elements
   - Design rationale linking to brand values

2. **Typography Suggestions**:
   - Font recommendations for each concept
   - Custom lettering considerations
   - Legibility at various sizes

3. **Color Palette Options**:
   - Primary color recommendations (with HEX codes)
   - Secondary and accent colors
   - Color psychology alignment with brand

4. **Scalability Notes**:
   - Minimum size recommendations
   - Variations needed (horizontal, stacked, icon only)
   - One-color version considerations

5. **Industry Appropriateness**:
   - Alignment with industry conventions
   - Differentiation from competitors
   - Target audience appeal

6. **Usage Guidelines Preview**:
   - Clear space requirements
   - Background variations
   - Do's and don'ts summary

Note: These are concept directions, not final designs. Avoid any trademarked or copyrighted design elements.""",

        "branding_kit_generator": """You are a brand identity specialist.
Input: {input}

Create a comprehensive brand system:

1. **Brand Foundation**:
   - Brand essence summary
   - Core values alignment
   - Personality traits
   - Voice and tone guidelines

2. **Color System**:
   - Primary colors (HEX, RGB, CMYK, Pantone)
   - Secondary palette
   - Accent colors
   - Color usage ratios (60-30-10 rule)

3. **Typography System**:
   - Primary typeface (headings)
   - Secondary typeface (body)
   - Size scale hierarchy
   - Web-safe alternatives

4. **Logo Usage Rules**:
   - Minimum clear space
   - Minimum sizes
   - Acceptable color variations
   - Placement guidelines

5. **Brand Applications**:
   - Signage specifications
   - Vehicle graphics guidelines
   - Print material standards
   - Digital presence guidelines

6. **Brand Assets Checklist**:
   - Required file formats
   - Resolution requirements
   - Naming conventions

Confirm before overwriting any existing brand materials.""",

        # Business Tools
        "business_copywriter": """You are a professional copywriter for sign shops and their clients.
Input: {input}

Generate polished copy:

1. **Primary Copy** (3 versions: short, medium, long):
   - Short: Tweet/tagline length (under 280 characters)
   - Medium: Paragraph length (2-3 sentences)
   - Long: Full description (4-6 sentences)

2. **Headlines/Taglines** (5 options):
   - Benefit-focused option
   - Action-oriented option
   - Emotional appeal option
   - Straightforward/clear option
   - Creative/memorable option

3. **Key Messages**:
   - Primary value proposition
   - Supporting benefits
   - Call-to-action variations

4. **Tone Calibration**:
   - Adjustments based on selected tone
   - Industry-appropriate language
   - Audience-specific vocabulary

5. **SEO Considerations** (if applicable):
   - Keyword suggestions
   - Meta description version
   - Header tag recommendations

6. **Compliance Notes**:
   - Avoid unsubstantiated claims
   - Remove any guarantees without basis
   - Legal disclaimer suggestions if needed

All copy is editable - treat as starting points for refinement.""",

        "document_composer": """You are a business document specialist for sign shops.
Input: {input}

Create a professional {document_type} document:

1. **Document Structure**:
   - Professional header/letterhead placeholder
   - Date and reference numbers
   - Recipient information
   - Subject line

2. **Main Content Sections** (based on document type):
   For Proposals: Executive summary, scope, pricing, timeline, terms
   For Scope of Work: Deliverables, specifications, exclusions, schedule
   For Installation Notes: Site prep, installation steps, safety, sign-off
   For Project Brief: Objectives, requirements, constraints, success criteria
   For Thank You Letters: Appreciation, project recap, future opportunities
   For Warranty Info: Coverage, exclusions, claims process, maintenance tips
   For Maintenance Guide: Cleaning instructions, inspection schedule, repairs
   
   For Late Payment Reminder (first notice):
   - Friendly tone reminding of outstanding balance
   - Invoice number, amount, and original due date
   - Request for payment within 7-14 days
   - Payment methods available
   - Contact info for questions
   
   For Final Payment Notice (second/third notice):
   - Firmer tone emphasizing urgency
   - Outstanding balance with any late fees
   - Warning of service suspension or collections
   - Final deadline for payment
   - Consequences of non-payment
   
   For Collections Letter (final notice):
   - Formal demand for payment
   - Full amount owed including all fees
   - Statement that account will be sent to collections
   - Final opportunity to resolve before legal action
   - Clear deadline (typically 10 days)
   
   For Other/Custom Documents:
   - Follow the custom_document_type description provided
   - Adapt structure to match the document purpose
   - Maintain professional formatting

3. **Tone and Style**:
   - Adjusted for selected formality level
   - Industry-appropriate terminology
   - Clear and professional language

4. **Legal Considerations**:
   - Standard terms and conditions notes
   - Liability disclaimers where appropriate
   - Signature/acceptance blocks

5. **Formatting Guidelines**:
   - Section headers
   - Bullet points for clarity
   - Professional spacing

6. **Document Metadata**:
   - Suggested filename
   - Version tracking note
   - Last updated date

Document can be stored in job history for reference.""",

        "pricing_intelligence": """You are a pricing analyst for sign shops.
Input: {input}

Provide comprehensive pricing analysis:

1. **Cost Breakdown**:
   - Material costs analysis
   - Labor cost calculation (hours × rate)
   - Equipment/overhead allocation
   - Subcontractor costs if applicable
   - Total direct costs

2. **Market Comparison**:
   - Typical market range for this service type
   - Premium vs. budget positioning
   - Geographic considerations
   - Competitor pricing insights

3. **Profit Analysis**:
   - Gross margin calculation
   - Markup percentage
   - Industry standard comparison
   - Profit per hour metric

4. **Pricing Recommendations**:
   - Suggested price range (low/mid/high)
   - Value-based pricing considerations
   - Volume discount opportunities
   - Rush pricing guidelines

5. **Red Flags**:
   - Underpricing warnings
   - Margin concerns
   - Market positioning risks
   - Hidden cost alerts

6. **Optimization Suggestions**:
   - Ways to improve margin
   - Upsell opportunities
   - Package pricing ideas
   - Payment terms recommendations

Present data with clear charts/tables format for easy review.""",

        # Marketing Tools
        "social_job_post": """You are a social media specialist for sign shops.
Input: {input}

Create engaging job showcase posts:

1. **Platform-Specific Captions**:
   
   **Facebook** (optimal 40-80 characters for engagement):
   - Headline hook
   - Brief description
   - Call-to-action
   - Relevant emojis (2-3 max)
   
   **Instagram** (up to 2200 characters):
   - Engaging opening line
   - Project story/details
   - Behind-the-scenes element
   - Call-to-action
   - Hashtag set (20-30 relevant tags)
   
   **LinkedIn** (professional tone):
   - Industry insight angle
   - Business value highlight
   - Professional achievement framing
   - Minimal hashtags (3-5 strategic)

2. **Hashtag Strategy**:
   - Industry hashtags (#signshop, #customsigns, etc.)
   - Location hashtags
   - Project-type hashtags
   - Trending relevant hashtags

3. **Content Variations**:
   - Before/after version
   - Process highlight version
   - Client success story version
   - Team spotlight version

4. **Engagement Boosters**:
   - Question to ask audience
   - Poll ideas
   - User interaction prompts

5. **Best Practices**:
   - Optimal posting times
   - Image/video recommendations
   - Tagging suggestions (with permission)

Avoid false claims. Location tagging optional and with client permission only.""",

        "social_pack_generator": """You are a content strategist for sign shop social media.
Input: {input}

Generate a comprehensive content pack:

1. **Content Mix** (based on pack size):
   - Educational posts (how-to, tips): 30%
   - Promotional posts (services, offers): 25%
   - Behind-the-scenes (process, team): 20%
   - Engagement posts (questions, polls): 15%
   - Testimonial/case study: 10%

2. **Post Templates** (for each post in pack):
   - Post type and objective
   - Caption (platform-optimized)
   - Visual/image direction
   - Hashtag set
   - Best day/time to post
   - Engagement prompt

3. **Content Calendar Suggestions**:
   - Recommended posting schedule
   - Themed content days
   - Special occasion tie-ins

4. **Visual Guidelines**:
   - Image style recommendations
   - Branding consistency tips
   - Photo vs. graphic balance

5. **Performance Tracking**:
   - Key metrics to monitor
   - A/B testing suggestions
   - Engagement benchmarks

6. **Repurposing Ideas**:
   - How to extend content lifespan
   - Cross-platform adaptations
   - Story/Reel variations

Content is editable - customize for your brand voice.""",

        "content_calendar": """You are a content planning strategist for sign shops.
Input: {input}

Create a detailed content calendar:

1. **Calendar Overview**:
   - Time period coverage
   - Total posts planned
   - Platform distribution
   - Content type breakdown

2. **Weekly Themes**:
   - Suggested theme for each week
   - Tie-ins to business goals
   - Seasonal/holiday considerations

3. **Daily Schedule** (for each date):
   - Day and date
   - Platform(s)
   - Content type
   - Topic/prompt
   - Post objective
   - Notes/reminders

4. **Content Pillars**:
   - Educational content themes
   - Promotional content themes
   - Engagement content themes
   - Brand story themes

5. **Key Dates to Remember**:
   - Industry events
   - Local events
   - Holidays relevant to audience
   - Business milestones

6. **Flexibility Built-In**:
   - Open slots for timely content
   - Backup content ideas
   - Weather-related alternatives

7. **Resource Planning**:
   - Photos/videos needed
   - Design assets required
   - Preparation time notes

Calendar format: visual grid view with drag/drop notes.""",

        "campaign_builder": """You are a marketing campaign strategist for sign shops.
Input: {input}

Design a complete marketing campaign:

1. **Campaign Overview**:
   - Campaign name and theme
   - Primary objective (SMART goal)
   - Target audience profile
   - Duration and key dates
   - Budget allocation breakdown

2. **Messaging Framework**:
   - Campaign tagline
   - Key messages (3-5)
   - Value proposition
   - Call-to-action variations

3. **Channel Strategy**:
   For each selected channel:
   - Specific tactics
   - Content types
   - Frequency
   - Budget allocation
   - KPIs to track

4. **Content Sequence**:
   - Launch phase content
   - Momentum phase content
   - Conversion phase content
   - Follow-up phase content

5. **Creative Assets Needed**:
   - Social media graphics
   - Email templates
   - Print materials
   - Signage/displays
   - Landing page requirements

6. **Offer Structure** (if applicable):
   - Primary offer details
   - Urgency elements
   - Terms and conditions
   - Redemption process

7. **Timeline**:
   - Pre-launch activities
   - Launch day checklist
   - Weekly milestones
   - Campaign wrap-up tasks

8. **Success Metrics**:
   - Primary KPIs
   - Secondary metrics
   - Tracking methods
   - Reporting schedule

9. **Contingency Plans**:
   - If underperforming: adjustment tactics
   - If overperforming: scale-up options
   - Risk mitigation strategies

Campaign elements are customizable - adjust based on actual resources and results."""
    }
    
    prompt_template = tool_prompts.get(request.tool)
    if not prompt_template:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")
    
    prompt = prompt_template.format(input=str(request.input_data), **request.input_data)
    
    try:
        # Determine if this tool needs vision (image analysis)
        needs_vision = request.tool in vision_tools
        has_image = request.input_data.get('image_upload')
        
        # Use Gemini for vision tasks (better image analysis)
        if needs_vision and has_image:
            chat = LlmChat(
                api_key=api_key,
                session_id=str(uuid.uuid4()),
                system_message="You are a helpful AI assistant for SignGuy AI, a sign shop management system. You are an expert at analyzing images for sign production and design purposes."
            ).with_model("gemini", "gemini-2.5-flash")
            
            # Extract base64 image data (remove data URL prefix if present)
            image_data = request.input_data.get('image_upload', '')
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Create message with image attachment
            image_content = ImageContent(image_base64=image_data)
            user_message = UserMessage(
                text=prompt,
                file_contents=[image_content]
            )
        else:
            # Use GPT for text-only tasks
            chat = LlmChat(
                api_key=api_key,
                session_id=str(uuid.uuid4()),
                system_message="You are a helpful AI assistant for SignGuy AI, a sign shop management system."
            ).with_model("openai", "gpt-5.2")
            
            user_message = UserMessage(text=prompt)
        
        response = await chat.send_message(user_message)
        
        # Save AI response
        ai_response = AIResponse(
            tool=request.tool,
            input_data=request.input_data,
            output=response,
            job_id=request.input_data.get("job_id"),
            customer_id=request.input_data.get("customer_id")
        )
        doc = ai_response.model_dump()
        await db.ai_responses.insert_one(doc)
        
        return ai_response
    except Exception as e:
        logger.error(f"AI generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

@api_router.get("/ai/history", response_model=List[AIResponse])
async def get_ai_history(
    tool: Optional[str] = None,
    job_id: Optional[str] = None,
    customer_id: Optional[str] = None
):
    query = {}
    if tool:
        query["tool"] = tool
    if job_id:
        query["job_id"] = job_id
    if customer_id:
        query["customer_id"] = customer_id
    
    responses = await db.ai_responses.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return responses

class AIImageRequest(BaseModel):
    tool: str
    input_data: dict
    image_count: int = 3

class AIImageResponse(BaseModel):
    images: List[dict]
    tool: str

@api_router.post("/ai/generate-images")
async def generate_ai_images(request: AIImageRequest):
    """Generate images using AI for design tools like logo creator, banner designer, etc."""
    import base64
    from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Build image prompt based on tool type
    image_prompts = {
        "logo_creator": """Professional logo design for "{business_name}" in the {industry} industry. 
Style: {style_preferences}. Colors: {color_preferences}. 
Logo type: {logo_type}. {tagline}
Clean, vector-style logo suitable for signage and print. High contrast, professional design. White or transparent background.""",
        
        "ai_banner_designer": """Professional promotional banner design, {banner_size} format.
Headline text: "{headline}"
Supporting text: {subtext}
Event type: {event_type}
Style: {style}
Colors: {brand_colors}
Clean, readable banner design optimized for outdoor viewing. Bold typography, clear text hierarchy, eye-catching layout.""",
        
        "ai_sign_designer": """Professional {sign_type} sign design for "{business_name}" ({business_type}).
Size: {size}
Colors: {colors}
Style: {style_preference}
Additional text: {additional_text}
High-quality business signage design with excellent readability and visual impact. Professional typography.""",
        
        "mockup_creator": """Realistic photographic mockup showing {product_type} installed in {environment} environment.
Design shown: {design_description}
Time of day: {time_of_day}
Professional presentation mockup for client approval. Photorealistic scene with proper lighting and perspective.""",
        
        "photo_enhancer": """Enhanced, high-quality version of the described image: {image_description}
Enhancement requirements: {enhancement_notes}
Output optimized for: {output_type}
Professional quality suitable for print and marketing materials.""",
        
        "image_vectorizer": """Clean vector-style illustration based on: {image_description}
Number of colors: {num_colors}
Image type: {image_type}
Clean lines, simplified shapes, suitable for cutting machines and print production."""
    }
    
    prompt_template = image_prompts.get(request.tool)
    if not prompt_template:
        raise HTTPException(status_code=400, detail=f"Image generation not supported for tool: {request.tool}")
    
    # Build the prompt with available data
    prompt_data = {k: v if v else '' for k, v in request.input_data.items()}
    # Set defaults for missing fields
    defaults = {
        'business_name': 'Business',
        'industry': 'general',
        'style_preferences': 'modern',
        'color_preferences': 'professional colors',
        'logo_type': 'combination mark',
        'tagline': '',
        'banner_size': '4x8ft',
        'headline': 'HEADLINE',
        'subtext': '',
        'event_type': 'promotion',
        'style': 'modern',
        'brand_colors': 'brand colors',
        'sign_type': 'wall sign',
        'business_type': 'business',
        'size': '4ft x 8ft',
        'colors': 'professional colors',
        'style_preference': 'modern',
        'additional_text': '',
        'product_type': 'sign',
        'environment': 'outdoor',
        'design_description': 'professional design',
        'time_of_day': 'daytime',
        'image_description': 'image',
        'enhancement_notes': 'enhance quality',
        'output_type': 'print optimized',
        'num_colors': '4-6',
        'image_type': 'standard'
    }
    for key, default in defaults.items():
        if key not in prompt_data or not prompt_data[key]:
            prompt_data[key] = default
    
    try:
        prompt = prompt_template.format(**prompt_data)
    except KeyError as e:
        prompt = prompt_template
    
    # Add modification notes if present
    if request.input_data.get('modification_notes'):
        prompt += f"\n\nModifications requested: {request.input_data['modification_notes']}"
    
    try:
        image_gen = OpenAIImageGeneration(api_key=api_key)
        images = []
        
        for i in range(request.image_count):
            # Add variation to each prompt
            variation_prompt = f"{prompt}\n\nCreate unique design variation {i+1} of {request.image_count}."
            
            # Generate image
            result = await image_gen.generate_images(
                prompt=variation_prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            
            if result and len(result) > 0:
                # Convert bytes to base64
                image_base64 = base64.b64encode(result[0]).decode('utf-8')
                images.append({
                    'url': f"data:image/png;base64,{image_base64}",
                    'index': i,
                    'prompt': variation_prompt[:200]
                })
        
        return AIImageResponse(images=images, tool=request.tool)
    except Exception as e:
        logger.error(f"AI image generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

# -------------- WEBSTORES: FUNDRAISER --------------
@api_router.post("/webstores/fundraiser", response_model=FundraiserCampaign)
async def create_fundraiser(input: FundraiserCampaignCreate):
    campaign = FundraiserCampaign(**input.model_dump())
    doc = campaign.model_dump()
    await db.fundraiser_campaigns.insert_one(doc)
    return campaign

@api_router.get("/webstores/fundraiser", response_model=List[FundraiserCampaign])
async def get_fundraisers(status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    campaigns = await db.fundraiser_campaigns.find(query, {"_id": 0}).to_list(100)
    return campaigns

@api_router.get("/webstores/fundraiser/{campaign_id}", response_model=FundraiserCampaign)
async def get_fundraiser(campaign_id: str):
    campaign = await db.fundraiser_campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@api_router.put("/webstores/fundraiser/{campaign_id}")
async def update_fundraiser(campaign_id: str, update_data: Dict[str, Any]):
    result = await db.fundraiser_campaigns.update_one({"id": campaign_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = await db.fundraiser_campaigns.find_one({"id": campaign_id}, {"_id": 0})
    return campaign

# -------------- WEBSTORES: B2B --------------
@api_router.post("/webstores/b2b", response_model=B2BStore)
async def create_b2b_store(input: B2BStoreCreate):
    store = B2BStore(**input.model_dump())
    doc = store.model_dump()
    await db.b2b_stores.insert_one(doc)
    return store

@api_router.get("/webstores/b2b", response_model=List[B2BStore])
async def get_b2b_stores(is_active: Optional[bool] = None):
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    stores = await db.b2b_stores.find(query, {"_id": 0}).to_list(100)
    return stores

@api_router.get("/webstores/b2b/{store_id}", response_model=B2BStore)
async def get_b2b_store(store_id: str):
    store = await db.b2b_stores.find_one({"id": store_id}, {"_id": 0})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

@api_router.post("/webstores/b2b/{store_id}/login")
async def b2b_store_login(store_id: str, password: str = Query(...)):
    store = await db.b2b_stores.find_one({"id": store_id}, {"_id": 0})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    if store["login_password"] != password:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"message": "Login successful", "store_id": store_id}

# -------------- WEBSTORE ORDERS --------------
@api_router.post("/webstores/orders", response_model=WebstoreOrder)
async def create_webstore_order(input: WebstoreOrderCreate):
    order = WebstoreOrder(**input.model_dump())
    
    # Auto-create job from order
    customer_name = f"Webstore {input.store_type.upper()} Customer"
    
    # Create or find customer
    existing_customer = await db.customers.find_one({"company": customer_name}, {"_id": 0})
    if not existing_customer:
        customer = Customer(name=customer_name, company=customer_name, status=CustomerStatus.ACTIVE)
        await db.customers.insert_one(customer.model_dump())
        customer_id = customer.id
    else:
        customer_id = existing_customer["id"]
    
    # Create job
    job = Job(
        customer_id=customer_id,
        name=f"Webstore Order #{order.id[:8]}",
        description=f"Order from {input.store_type} store {input.store_id}",
        status=JobStatus.APPROVED
    )
    await db.jobs.insert_one(job.model_dump())
    
    order.job_id = job.id
    doc = order.model_dump()
    await db.webstore_orders.insert_one(doc)
    
    # Update fundraiser total if applicable
    if input.store_type == "fundraiser":
        await db.fundraiser_campaigns.update_one(
            {"id": input.store_id},
            {"$inc": {"total_raised": input.total}}
        )
    
    return order

@api_router.get("/webstores/orders", response_model=List[WebstoreOrder])
async def get_webstore_orders(
    store_type: Optional[str] = None,
    store_id: Optional[str] = None
):
    query = {}
    if store_type:
        query["store_type"] = store_type
    if store_id:
        query["store_id"] = store_id
    orders = await db.webstore_orders.find(query, {"_id": 0}).to_list(1000)
    return orders

# ============== NEW WEBSTORE SYSTEM APIs ==============

# -------------- MASTER PRODUCT CATALOG --------------

@api_router.post("/products", response_model=Product)
async def create_product(input: ProductCreate):
    variants = []
    if input.has_variants and input.variants:
        for v in input.variants:
            variant = ProductVariant(
                name=v.get("name", ""),
                size=v.get("size"),
                color=v.get("color"),
                sku=v.get("sku"),
                additional_cost=v.get("additional_cost", 0),
                is_available=v.get("is_available", True)
            )
            variants.append(variant.model_dump())
    
    product = Product(
        name=input.name,
        description=input.description,
        category=input.category,
        base_cost=input.base_cost,
        retail_price=input.retail_price,
        image_url=input.image_url,
        has_variants=input.has_variants,
        variants=variants
    )
    doc = product.model_dump()
    await db.products.insert_one(doc)
    return product

@api_router.get("/products", response_model=List[Product])
async def get_products(
    category: Optional[str] = None,
    is_active: Optional[bool] = None
):
    query = {}
    if category:
        query["category"] = category
    if is_active is not None:
        query["is_active"] = is_active
    products = await db.products.find(query, {"_id": 0}).to_list(500)
    return products

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, input: ProductUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if "variants" in update_data and update_data["variants"]:
        variants = []
        for v in update_data["variants"]:
            if "id" not in v:
                v["id"] = str(uuid.uuid4())
            variants.append(v)
        update_data["variants"] = variants
    
    if update_data:
        await db.products.update_one({"id": product_id}, {"$set": update_data})
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    # Also remove from all webstore assignments
    await db.webstore_products.delete_many({"product_id": product_id})
    return {"message": "Product deleted"}

# -------------- WEBSTORES (NEW SYSTEM) --------------

@api_router.post("/webstores/v2", response_model=Webstore)
async def create_webstore(input: WebstoreCreate):
    branding = WebstoreBranding(**(input.branding or {}))
    webstore = Webstore(
        name=input.name,
        store_type=input.store_type,
        owner_name=input.owner_name,
        owner_email=input.owner_email,
        owner_phone=input.owner_phone,
        description=input.description,
        is_public=input.is_public,
        branding=branding,
        fundraiser_goal=input.fundraiser_goal,
        fundraiser_start_date=input.fundraiser_start_date,
        fundraiser_end_date=input.fundraiser_end_date,
        fundraiser_profit_percent=input.fundraiser_profit_percent,
        creator_commission_type=input.creator_commission_type,
        creator_commission_value=input.creator_commission_value
    )
    doc = webstore.model_dump()
    await db.webstores_v2.insert_one(doc)
    return webstore

@api_router.get("/webstores/v2", response_model=List[Webstore])
async def get_webstores(
    store_type: Optional[str] = None,
    status: Optional[str] = None,
    is_public: Optional[bool] = None
):
    query = {}
    if store_type:
        query["store_type"] = store_type
    if status:
        query["status"] = status
    if is_public is not None:
        query["is_public"] = is_public
    webstores = await db.webstores_v2.find(query, {"_id": 0}).to_list(500)
    return webstores

# -------------- WEBSTORE ORDERS V2 (Must be before {webstore_id} routes) --------------

@api_router.post("/webstores/v2/orders", response_model=WebstoreOrderV2)
async def create_webstore_order_v2(input: WebstoreOrderV2Create):
    # Get webstore
    webstore = await db.webstores_v2.find_one({"id": input.webstore_id}, {"_id": 0})
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    # Process items and calculate totals
    order_items = []
    subtotal = 0
    total_cost = 0
    total_profit = 0
    
    for item in input.items:
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0})
        if not product:
            continue
        
        # Check for price override
        assignment = await db.webstore_products.find_one({
            "webstore_id": input.webstore_id,
            "product_id": item["product_id"]
        }, {"_id": 0})
        
        unit_price = (assignment.get("price_override") if assignment and assignment.get("price_override") 
                      else product["retail_price"])
        base_cost = product["base_cost"]
        
        # Handle variant additional cost
        variant_name = None
        if item.get("variant_id") and product.get("variants"):
            for v in product["variants"]:
                if v["id"] == item["variant_id"]:
                    variant_name = v.get("name")
                    base_cost += v.get("additional_cost", 0)
                    break
        
        quantity = item.get("quantity", 1)
        item_total = unit_price * quantity
        item_cost = base_cost * quantity
        item_profit = item_total - item_cost
        
        order_items.append(WebstoreOrderItem(
            product_id=item["product_id"],
            product_name=product["name"],
            variant_id=item.get("variant_id"),
            variant_name=variant_name,
            quantity=quantity,
            unit_price=unit_price,
            base_cost=base_cost,
            total=item_total,
            profit=item_profit
        ).model_dump())
        
        subtotal += item_total
        total_cost += item_cost
        total_profit += item_profit
    
    # Calculate payout based on store type
    payout_amount = 0
    shop_profit = total_profit
    
    if webstore["store_type"] == "fundraiser":
        payout_percent = webstore.get("fundraiser_profit_percent", 0) / 100
        payout_amount = total_profit * payout_percent
        shop_profit = total_profit - payout_amount
    elif webstore["store_type"] == "creator":
        if webstore.get("creator_commission_type") == "percentage":
            commission_percent = webstore.get("creator_commission_value", 0) / 100
            payout_amount = total_profit * commission_percent
        else:  # fixed
            payout_amount = webstore.get("creator_commission_value", 0) * len(order_items)
        shop_profit = total_profit - payout_amount
    
    total = subtotal + input.tax + input.shipping
    
    # Create order
    order = WebstoreOrderV2(
        webstore_id=input.webstore_id,
        webstore_name=webstore["name"],
        store_type=webstore["store_type"],
        customer_name=input.customer_name,
        customer_email=input.customer_email,
        customer_phone=input.customer_phone,
        shipping_address=input.shipping_address,
        items=order_items,
        subtotal=subtotal,
        tax=input.tax,
        shipping=input.shipping,
        total=total,
        total_cost=total_cost,
        total_profit=total_profit,
        shop_profit=shop_profit,
        payout_amount=payout_amount,
        notes=input.notes
    )
    
    doc = order.model_dump()
    await db.webstore_orders_v2.insert_one(doc)
    
    # Update webstore totals
    await db.webstores_v2.update_one(
        {"id": input.webstore_id},
        {
            "$inc": {
                "total_sales": total,
                "total_orders": 1,
                "total_profit": total_profit,
                "payout_owed": payout_amount
            }
        }
    )
    
    # Send order notification email (non-blocking)
    import asyncio
    asyncio.create_task(send_order_notification_email(order.model_dump(), webstore))
    
    return order

@api_router.get("/webstores/v2/orders", response_model=List[WebstoreOrderV2])
async def get_webstore_orders_v2(
    webstore_id: Optional[str] = None,
    store_type: Optional[str] = None,
    status: Optional[str] = None
):
    query = {}
    if webstore_id:
        query["webstore_id"] = webstore_id
    if store_type:
        query["store_type"] = store_type
    if status:
        query["status"] = status
    orders = await db.webstore_orders_v2.find(query, {"_id": 0}).to_list(1000)
    return orders

@api_router.get("/webstores/v2/orders/{order_id}", response_model=WebstoreOrderV2)
async def get_webstore_order_v2(order_id: str):
    order = await db.webstore_orders_v2.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@api_router.put("/webstores/v2/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, job_id: Optional[str] = None):
    update_data = {"status": status}
    if job_id:
        update_data["job_id"] = job_id
    
    result = await db.webstore_orders_v2.update_one({"id": order_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = await db.webstore_orders_v2.find_one({"id": order_id}, {"_id": 0})
    return order

@api_router.post("/webstores/v2/orders/{order_id}/create-job")
async def create_job_from_order(order_id: str):
    order = await db.webstore_orders_v2.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.get("job_id"):
        raise HTTPException(status_code=400, detail="Job already created for this order")
    
    # Create job
    job = Job(
        name=f"Webstore Order #{order_id[:8]}",
        description=f"Order from {order['webstore_name']} - {order['customer_name']}",
        status="approved",
        customer_id=None,  # Webstore orders may not have existing customer
        subtotal=order["total"]
    )
    job_doc = job.model_dump()
    await db.jobs.insert_one(job_doc)
    
    # Create job items from order items
    for item in order["items"]:
        job_item = JobItem(
            job_id=job.id,
            item_type="webstore_product",
            description=f"{item['product_name']}" + (f" - {item['variant_name']}" if item.get('variant_name') else ""),
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            total=item["total"],
            status="pending"
        )
        await db.job_items.insert_one(job_item.model_dump())
    
    # Update order with job_id
    await db.webstore_orders_v2.update_one(
        {"id": order_id},
        {"$set": {"job_id": job.id, "status": "processing"}}
    )
    
    # Log activity
    activity = JobActivity(
        job_id=job.id,
        type=JobActivityType.CREATED,
        description=f"Job created from webstore order #{order_id[:8]}"
    )
    await db.job_activities.insert_one(activity.model_dump())
    
    return {"job_id": job.id, "message": "Job created successfully"}

# -------------- WEBSTORE BY ID ROUTES --------------

@api_router.get("/webstores/v2/{webstore_id}", response_model=Webstore)
async def get_webstore(webstore_id: str):
    webstore = await db.webstores_v2.find_one({"id": webstore_id}, {"_id": 0})
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    return webstore

@api_router.put("/webstores/v2/{webstore_id}", response_model=Webstore)
async def update_webstore(webstore_id: str, input: WebstoreUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if update_data:
        await db.webstores_v2.update_one({"id": webstore_id}, {"$set": update_data})
    webstore = await db.webstores_v2.find_one({"id": webstore_id}, {"_id": 0})
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    return webstore

@api_router.delete("/webstores/v2/{webstore_id}")
async def delete_webstore(webstore_id: str):
    result = await db.webstores_v2.delete_one({"id": webstore_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webstore not found")
    # Also remove product assignments
    await db.webstore_products.delete_many({"webstore_id": webstore_id})
    return {"message": "Webstore deleted"}

# -------------- WEBSTORE PRODUCT ASSIGNMENTS --------------

@api_router.post("/webstores/v2/{webstore_id}/products")
async def assign_product_to_webstore(webstore_id: str, input: WebstoreProductCreate):
    # Verify webstore exists
    webstore = await db.webstores_v2.find_one({"id": webstore_id})
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    # Verify product exists
    product = await db.products.find_one({"id": input.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if already assigned
    existing = await db.webstore_products.find_one({
        "webstore_id": webstore_id,
        "product_id": input.product_id
    })
    if existing:
        # Update existing assignment
        await db.webstore_products.update_one(
            {"id": existing["id"]},
            {"$set": {"is_enabled": input.is_enabled, "price_override": input.price_override}}
        )
        updated = await db.webstore_products.find_one({"id": existing["id"]}, {"_id": 0})
        return updated
    
    # Create new assignment
    assignment = WebstoreProduct(
        webstore_id=webstore_id,
        product_id=input.product_id,
        is_enabled=input.is_enabled,
        price_override=input.price_override
    )
    doc = assignment.model_dump()
    await db.webstore_products.insert_one(doc)
    return assignment

@api_router.get("/webstores/v2/{webstore_id}/products")
async def get_webstore_products(webstore_id: str, include_disabled: bool = False):
    query = {"webstore_id": webstore_id}
    if not include_disabled:
        query["is_enabled"] = True
    
    assignments = await db.webstore_products.find(query, {"_id": 0}).to_list(500)
    
    # Enrich with product details
    result = []
    for a in assignments:
        product = await db.products.find_one({"id": a["product_id"]}, {"_id": 0})
        if product:
            result.append({
                **a,
                "product": product,
                "effective_price": a.get("price_override") or product.get("retail_price", 0)
            })
    return result

@api_router.delete("/webstores/v2/{webstore_id}/products/{product_id}")
async def remove_product_from_webstore(webstore_id: str, product_id: str):
    result = await db.webstore_products.delete_one({
        "webstore_id": webstore_id,
        "product_id": product_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product assignment not found")
    return {"message": "Product removed from webstore"}

# -------------- WEBSTORE PAYOUTS --------------

@api_router.post("/webstores/v2/{webstore_id}/record-payout")
async def record_payout(webstore_id: str, amount: float, notes: Optional[str] = None):
    webstore = await db.webstores_v2.find_one({"id": webstore_id}, {"_id": 0})
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    if amount > webstore.get("payout_owed", 0):
        raise HTTPException(status_code=400, detail="Payout amount exceeds owed amount")
    
    await db.webstores_v2.update_one(
        {"id": webstore_id},
        {
            "$inc": {
                "payout_owed": -amount,
                "payout_paid": amount
            }
        }
    )
    
    # Record payout transaction
    payout_record = {
        "id": str(uuid.uuid4()),
        "webstore_id": webstore_id,
        "amount": amount,
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.webstore_payouts.insert_one(payout_record)
    
    # Remove MongoDB _id before returning
    payout_record.pop("_id", None)
    
    return {"message": "Payout recorded", "payout": payout_record}

@api_router.get("/webstores/v2/{webstore_id}/payouts")
async def get_webstore_payouts(webstore_id: str):
    payouts = await db.webstore_payouts.find({"webstore_id": webstore_id}, {"_id": 0}).to_list(500)
    return payouts

# -------------- WEBSTORE ANALYTICS --------------
@api_router.get("/webstores/v2/{webstore_id}/analytics")
async def get_webstore_analytics(webstore_id: str):
    """Get comprehensive analytics for a webstore"""
    # Get the webstore
    store = await db.webstores_v2.find_one({"id": webstore_id}, {"_id": 0})
    if not store:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    # Get all orders for this store
    orders = await db.webstore_orders_v2.find({"webstore_id": webstore_id}, {"_id": 0}).to_list(1000)
    
    # Get payouts
    payouts = await db.webstore_payouts.find({"webstore_id": webstore_id}, {"_id": 0}).to_list(500)
    
    # Calculate metrics
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.get("status") in ["completed", "shipped"]])
    pending_orders = len([o for o in orders if o.get("status") == "pending"])
    processing_orders = len([o for o in orders if o.get("status") in ["processing", "production"]])
    
    total_revenue = sum(o.get("total", 0) for o in orders)
    total_profit = sum(o.get("total_profit", 0) for o in orders)
    shop_profit = sum(o.get("shop_profit", 0) for o in orders)
    payout_amount = sum(o.get("payout_amount", 0) for o in orders)
    
    # Calculate paid out amount
    total_paid_out = sum(p.get("amount", 0) for p in payouts)
    balance_owed = payout_amount - total_paid_out
    
    # Average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Sales by day (last 30 days)
    from collections import defaultdict
    sales_by_day = defaultdict(float)
    for order in orders:
        order_date = order.get("created_at", "")[:10]  # Get YYYY-MM-DD
        sales_by_day[order_date] += order.get("total", 0)
    
    # Sort sales by day
    sales_by_day_sorted = sorted(sales_by_day.items())[-30:]  # Last 30 days
    
    # Top products
    product_sales = defaultdict(lambda: {"quantity": 0, "revenue": 0, "name": ""})
    for order in orders:
        for item in order.get("items", []):
            pid = item.get("product_id", "unknown")
            product_sales[pid]["quantity"] += item.get("quantity", 0)
            product_sales[pid]["revenue"] += item.get("total", 0)
            product_sales[pid]["name"] = item.get("product_name", "Unknown")
    
    top_products = sorted(
        [{"product_id": k, **v} for k, v in product_sales.items()],
        key=lambda x: x["revenue"],
        reverse=True
    )[:10]
    
    # Fundraiser-specific metrics
    fundraiser_metrics = None
    if store.get("store_type") == "fundraiser":
        goal = store.get("fundraiser_goal", 0)
        raised = payout_amount
        progress_percent = (raised / goal * 100) if goal > 0 else 0
        
        # Calculate days remaining
        end_date_str = store.get("fundraiser_end_date")
        days_remaining = None
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                days_remaining = max(0, (end_date - now).days)
            except:
                pass
        
        fundraiser_metrics = {
            "goal": goal,
            "raised": raised,
            "progress_percent": min(progress_percent, 100),
            "days_remaining": days_remaining,
            "profit_percent": store.get("fundraiser_profit_percent", 0)
        }
    
    return {
        "store_id": webstore_id,
        "store_name": store.get("name"),
        "store_type": store.get("store_type"),
        "summary": {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "pending_orders": pending_orders,
            "processing_orders": processing_orders,
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "shop_profit": shop_profit,
            "avg_order_value": avg_order_value
        },
        "payout_info": {
            "total_earned": payout_amount,
            "total_paid_out": total_paid_out,
            "balance_owed": balance_owed
        },
        "sales_by_day": [{"date": d, "amount": a} for d, a in sales_by_day_sorted],
        "top_products": top_products,
        "fundraiser_metrics": fundraiser_metrics
    }

# -------------- EMAIL NOTIFICATIONS --------------
async def send_order_notification_email(order: dict, store: dict):
    """Send email notification when a new order is placed"""
    try:
        # Get tenant info for the shop owner email
        tenant = await db.tenants.find_one({}, {"_id": 0})
        if not tenant or not tenant.get("owner_email"):
            logger.warning("No tenant owner email found for order notification")
            return
        
        shop_email = tenant.get("owner_email")
        shop_name = tenant.get("name", "SignGuy AI Shop")
        
        # Build email content
        items_html = ""
        for item in order.get("items", []):
            variant_str = f" - {item.get('variant_name')}" if item.get('variant_name') else ""
            items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{item.get('product_name', 'Product')}{variant_str}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{item.get('quantity', 1)}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">${item.get('total', 0):.2f}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2F8BFB; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .order-details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #f0f0f0; padding: 10px; text-align: left; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛒 New Order Received!</h1>
                </div>
                <div class="content">
                    <p>You have a new order from <strong>{store.get('name', 'Webstore')}</strong>!</p>
                    
                    <div class="order-details">
                        <h3>Order #{order.get('id', '')[:8]}</h3>
                        <p><strong>Customer:</strong> {order.get('customer_name', 'N/A')}</p>
                        <p><strong>Email:</strong> {order.get('customer_email', 'N/A')}</p>
                        <p><strong>Phone:</strong> {order.get('customer_phone', 'N/A')}</p>
                        {f"<p><strong>Shipping Address:</strong> {order.get('shipping_address')}</p>" if order.get('shipping_address') else ""}
                        
                        <h4>Items Ordered:</h4>
                        <table>
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th style="text-align: center;">Qty</th>
                                    <th style="text-align: right;">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items_html}
                            </tbody>
                        </table>
                        
                        <div style="margin-top: 15px; text-align: right;">
                            <p><strong>Subtotal:</strong> ${order.get('subtotal', 0):.2f}</p>
                            <p><strong>Tax:</strong> ${order.get('tax', 0):.2f}</p>
                            <p><strong>Shipping:</strong> ${order.get('shipping', 0):.2f}</p>
                            <p style="font-size: 18px;"><strong>Total:</strong> ${order.get('total', 0):.2f}</p>
                        </div>
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="{os.environ.get('FRONTEND_URL', 'https://sign-shop-suite.preview.emergentagent.com')}/webstores" 
                           style="background: #2F8BFB; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            View Order in Dashboard
                        </a>
                    </p>
                </div>
                <div class="footer">
                    <p>This notification was sent from {shop_name}</p>
                    <p>Powered by SignGuy AI</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Try to send via SendGrid if configured
        sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
        sender_email = os.environ.get("SENDER_EMAIL", "noreply@signguy.ai")
        
        if sendgrid_api_key:
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                
                message = Mail(
                    from_email=sender_email,
                    to_emails=shop_email,
                    subject=f"🛒 New Order from {store.get('name', 'Webstore')} - ${order.get('total', 0):.2f}",
                    html_content=html_content
                )
                
                sg = SendGridAPIClient(sendgrid_api_key)
                response = sg.send(message)
                logger.info(f"Order notification email sent to {shop_email}, status: {response.status_code}")
            except Exception as e:
                logger.error(f"Failed to send order notification via SendGrid: {e}")
        else:
            logger.info(f"SendGrid not configured. Order notification would be sent to: {shop_email}")
            
    except Exception as e:
        logger.error(f"Error sending order notification: {e}")

# ============== PRICING CALCULATOR API ==============

# Helper: Get or create default pricing configuration for tenant
async def get_pricing_defaults(tenant_id: str) -> dict:
    """Get pricing defaults for a tenant, creating if doesn't exist"""
    defaults = await db.pricing_defaults.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not defaults:
        # Create default pricing config
        new_defaults = PricingDefaults(tenant_id=tenant_id)
        await db.pricing_defaults.insert_one(new_defaults.model_dump())
        defaults = new_defaults.model_dump()
    return defaults

# Helper: Calculate complexity multiplier
def get_complexity_multiplier(complexity: int, base: float = 1.0, max_mult: float = 2.0) -> float:
    """Calculate multiplier based on complexity (1-10)"""
    complexity = max(1, min(10, complexity))  # Clamp to 1-10
    # Linear interpolation from base at 1 to max at 10
    return base + (max_mult - base) * (complexity - 1) / 9

# Helper: Calculate quantity discount
def get_quantity_discount(quantity: float, quantity_breaks: dict) -> float:
    """Get discount percentage based on quantity"""
    discount = 0
    for break_name, break_data in quantity_breaks.items():
        if quantity >= break_data.get("min_qty", 0):
            discount = max(discount, break_data.get("discount_percent", 0))
    return discount

# ============== CATEGORY-SPECIFIC CALCULATORS ==============

async def calculate_promotional(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculator for Promotional Items (margin-based)"""
    unit_cost = data.unit_cost or 0
    markup = data.markup_percent if data.markup_percent is not None else defaults.get("default_markup_percent", 100)
    setup_fee = data.setup_fee or 0
    
    # Calculate
    extended_cost = unit_cost * quantity
    markup_amount = extended_cost * (markup / 100)
    suggested_price = extended_cost + markup_amount + setup_fee
    
    production_cost = extended_cost + setup_fee
    profit = suggested_price - production_cost
    margin = (profit / suggested_price * 100) if suggested_price > 0 else 0
    
    return PricingCalculation(
        material_cost=extended_cost,
        setup_cost=setup_fee,
        production_cost=production_cost,
        suggested_price=suggested_price,
        markup_percent=markup,
        profit_margin_percent=round(margin, 1),
        profit_amount=round(profit, 2),
        breakdown={
            "unit_cost": unit_cost,
            "quantity": quantity,
            "extended_cost": round(extended_cost, 2),
            "markup_percent": markup,
            "markup_amount": round(markup_amount, 2),
            "setup_fee": setup_fee
        }
    )

async def calculate_cut_vinyl(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculator for Cut Vinyl (decals, lettering)"""
    # Calculate square footage
    width = data.width_inches or 0
    length = data.length_inches or 0
    sqft = data.square_footage or (width * length / 144)  # Convert sq inches to sq ft
    
    # Material costs based on vinyl type
    vinyl_costs = {
        "oracal_651": 0.50,
        "oracal_751": 0.75,
        "oracal_951": 1.25,
        "avery_hp750": 0.90,
        "reflective": 2.50,
        "specialty": 1.50,
        "custom": 1.00
    }
    vinyl_cost_per_sqft = vinyl_costs.get(data.vinyl_type.value if data.vinyl_type else "oracal_651", 0.75)
    
    # Complexity multiplier
    complexity_mult = get_complexity_multiplier(
        data.complexity, 
        defaults.get("complexity_multiplier_base", 1.0),
        defaults.get("complexity_multiplier_max", 2.0)
    )
    
    # Color multiplier (more colors = more time)
    color_mult = 1 + (data.num_colors - 1) * 0.25
    
    # Calculate costs
    material_cost = sqft * vinyl_cost_per_sqft * data.num_colors * quantity
    weeding_minutes = sqft * defaults.get("weeding_time_per_sqft", 5) * complexity_mult * color_mult
    application_minutes = sqft * defaults.get("application_time_per_sqft", 3)
    total_labor_minutes = (weeding_minutes + application_minutes) * quantity
    labor_cost = (total_labor_minutes / 60) * defaults.get("hourly_rate", 75)
    setup_cost = defaults.get("setup_fee_vinyl", 15)
    
    production_cost = material_cost + labor_cost + setup_cost
    
    # Apply minimum charge
    min_charge = defaults.get("minimum_vinyl_charge", 25)
    production_cost = max(production_cost, min_charge)
    
    # Quantity discount
    qty_discount = get_quantity_discount(quantity, defaults.get("quantity_breaks", {}))
    
    # Suggested price with markup
    markup = defaults.get("default_markup_percent", 100)
    suggested_price = production_cost * (1 + markup / 100) * (1 - qty_discount / 100)
    
    profit = suggested_price - production_cost
    margin = (profit / suggested_price * 100) if suggested_price > 0 else 0
    
    return PricingCalculation(
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost, 2),
        setup_cost=setup_cost,
        production_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        markup_percent=markup,
        profit_margin_percent=round(margin, 1),
        profit_amount=round(profit, 2),
        estimated_labor_minutes=round(total_labor_minutes, 1),
        breakdown={
            "square_footage": round(sqft, 2),
            "vinyl_type": data.vinyl_type.value if data.vinyl_type else "oracal_651",
            "vinyl_cost_per_sqft": vinyl_cost_per_sqft,
            "num_colors": data.num_colors,
            "complexity": data.complexity,
            "complexity_multiplier": round(complexity_mult, 2),
            "weeding_minutes": round(weeding_minutes, 1),
            "application_minutes": round(application_minutes, 1),
            "quantity_discount_percent": qty_discount
        }
    )

async def calculate_services(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculator for Services (labor-based)"""
    hours = data.estimated_hours or 1
    
    # Get hourly rate based on service type
    service_rates = {
        "design": defaults.get("design_hourly_rate", 85),
        "installation": defaults.get("install_hourly_rate", 95),
        "removal": defaults.get("install_hourly_rate", 95),
        "site_survey": defaults.get("hourly_rate", 75),
        "consultation": defaults.get("hourly_rate", 75),
        "travel": defaults.get("hourly_rate", 75),
        "other_labor": defaults.get("hourly_rate", 75)
    }
    hourly_rate = data.hourly_rate_override or service_rates.get(
        data.service_type.value if data.service_type else "other_labor", 
        defaults.get("hourly_rate", 75)
    )
    
    # Complexity multiplier for services
    complexity_mult = get_complexity_multiplier(
        data.complexity,
        defaults.get("complexity_multiplier_base", 1.0),
        1.5  # Services max out at 1.5x
    )
    
    # Number of workers
    workers = max(1, data.num_workers)
    
    # Calculate labor cost
    labor_cost = hours * hourly_rate * workers * complexity_mult * quantity
    
    # Travel cost
    travel_cost = 0
    if data.distance_miles and data.distance_miles > 0:
        mileage_rate = defaults.get("mileage_rate", 0.67)
        travel_cost = max(
            data.distance_miles * mileage_rate * 2,  # Round trip
            defaults.get("minimum_travel_charge", 50)
        )
    
    production_cost = labor_cost + travel_cost
    
    # Apply minimum charge
    min_charge = defaults.get("minimum_service_charge", 75)
    production_cost = max(production_cost, min_charge)
    
    # Suggested price (services typically lower markup)
    markup = 50  # 50% markup on services
    suggested_price = production_cost * (1 + markup / 100)
    
    profit = suggested_price - production_cost
    margin = (profit / suggested_price * 100) if suggested_price > 0 else 0
    
    return PricingCalculation(
        labor_cost=round(labor_cost, 2),
        additional_costs=round(travel_cost, 2),
        production_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        markup_percent=markup,
        profit_margin_percent=round(margin, 1),
        profit_amount=round(profit, 2),
        estimated_labor_minutes=round(hours * 60 * workers * quantity, 1),
        breakdown={
            "service_type": data.service_type.value if data.service_type else "other_labor",
            "hours": hours,
            "hourly_rate": hourly_rate,
            "num_workers": workers,
            "complexity": data.complexity,
            "complexity_multiplier": round(complexity_mult, 2),
            "travel_miles": data.distance_miles or 0,
            "travel_cost": round(travel_cost, 2)
        }
    )

async def calculate_digital_print(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculator for Digital Print (banners, posters)"""
    # Calculate square footage
    width = data.width_inches or 0
    length = data.length_inches or 0
    sqft = data.square_footage or (width * length / 144)
    
    # Material costs
    material_costs = {
        "banner_13oz": 0.75,
        "banner_18oz": 1.10,
        "vinyl_adhesive": 1.25,
        "poster_paper": 0.35,
        "canvas": 2.50,
        "backlit": 2.00,
        "perforated": 1.75,
        "custom": 1.00
    }
    material_cost_per_sqft = material_costs.get(
        data.print_material.value if data.print_material else "banner_13oz", 
        1.00
    )
    
    # Ink cost estimate (approx $0.15-0.30 per sqft)
    ink_cost_per_sqft = 0.20
    
    # Laminate cost
    laminate_cost_per_sqft = 0.40 if data.laminate else 0
    
    # Calculate costs
    material_cost = sqft * material_cost_per_sqft * quantity
    ink_cost = sqft * ink_cost_per_sqft * quantity
    laminate_cost = sqft * laminate_cost_per_sqft * quantity
    
    # Labor
    print_minutes = sqft * defaults.get("print_time_per_sqft", 1)
    laminate_minutes = sqft * defaults.get("laminate_time_per_sqft", 1.5) if data.laminate else 0
    total_labor_minutes = (print_minutes + laminate_minutes) * quantity
    labor_cost = (total_labor_minutes / 60) * defaults.get("hourly_rate", 75)
    
    setup_cost = defaults.get("setup_fee_print", 25)
    
    production_cost = material_cost + ink_cost + laminate_cost + labor_cost + setup_cost
    
    # Apply minimum
    min_charge = defaults.get("minimum_print_charge", 35)
    production_cost = max(production_cost, min_charge)
    
    # Quantity discount
    qty_discount = get_quantity_discount(quantity, defaults.get("quantity_breaks", {}))
    
    # Suggested price
    markup = defaults.get("default_markup_percent", 100)
    suggested_price = production_cost * (1 + markup / 100) * (1 - qty_discount / 100)
    
    profit = suggested_price - production_cost
    margin = (profit / suggested_price * 100) if suggested_price > 0 else 0
    
    return PricingCalculation(
        material_cost=round(material_cost + ink_cost + laminate_cost, 2),
        labor_cost=round(labor_cost, 2),
        setup_cost=setup_cost,
        production_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        markup_percent=markup,
        profit_margin_percent=round(margin, 1),
        profit_amount=round(profit, 2),
        estimated_labor_minutes=round(total_labor_minutes, 1),
        breakdown={
            "square_footage": round(sqft, 2),
            "material_type": data.print_material.value if data.print_material else "banner_13oz",
            "material_cost_per_sqft": material_cost_per_sqft,
            "ink_cost": round(ink_cost, 2),
            "laminated": data.laminate,
            "laminate_cost": round(laminate_cost, 2),
            "quantity_discount_percent": qty_discount
        }
    )

async def calculate_rigid_signs(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculator for Rigid Signs (coroplast, aluminum, PVC)"""
    # Calculate square footage
    width = data.width_inches or 0
    length = data.length_inches or 0
    sqft = data.square_footage or (width * length / 144)
    
    # Substrate costs
    substrate_costs = {
        "coroplast_4mm": 0.45,
        "coroplast_10mm": 0.65,
        "aluminum_040": 1.50,
        "aluminum_063": 2.25,
        "aluminum_080": 3.00,
        "pvc_3mm": 1.00,
        "pvc_6mm": 1.50,
        "acrylic": 4.00,
        "dibond": 3.50,
        "mdo": 2.00,
        "custom": 1.50
    }
    substrate_cost_per_sqft = substrate_costs.get(
        data.substrate_type.value if data.substrate_type else "coroplast_4mm",
        1.00
    )
    
    # Double-sided multiplier
    sides_mult = 2 if data.double_sided else 1
    
    # Vinyl/print cost
    vinyl_cost_per_sqft = 1.25  # Digital print on sign
    
    # Laminate
    laminate_cost_per_sqft = 0.40 if data.laminate else 0
    
    # Calculate
    substrate_cost = sqft * substrate_cost_per_sqft * quantity
    vinyl_cost = sqft * vinyl_cost_per_sqft * sides_mult * quantity
    laminate_cost = sqft * laminate_cost_per_sqft * sides_mult * quantity
    
    # Labor with complexity
    complexity_mult = get_complexity_multiplier(data.complexity, 1.0, 1.75)
    labor_minutes = sqft * 10 * complexity_mult * sides_mult  # ~10 min per sqft base
    total_labor_minutes = labor_minutes * quantity
    labor_cost = (total_labor_minutes / 60) * defaults.get("hourly_rate", 75)
    
    setup_cost = defaults.get("setup_fee_print", 25)
    
    production_cost = substrate_cost + vinyl_cost + laminate_cost + labor_cost + setup_cost
    
    # Minimum
    min_charge = defaults.get("minimum_sign_charge", 50)
    production_cost = max(production_cost, min_charge)
    
    # Quantity discount
    qty_discount = get_quantity_discount(quantity, defaults.get("quantity_breaks", {}))
    
    # Suggested price
    markup = defaults.get("default_markup_percent", 100)
    suggested_price = production_cost * (1 + markup / 100) * (1 - qty_discount / 100)
    
    profit = suggested_price - production_cost
    margin = (profit / suggested_price * 100) if suggested_price > 0 else 0
    
    return PricingCalculation(
        material_cost=round(substrate_cost + vinyl_cost + laminate_cost, 2),
        labor_cost=round(labor_cost, 2),
        setup_cost=setup_cost,
        production_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        markup_percent=markup,
        profit_margin_percent=round(margin, 1),
        profit_amount=round(profit, 2),
        estimated_labor_minutes=round(total_labor_minutes, 1),
        breakdown={
            "square_footage": round(sqft, 2),
            "substrate_type": data.substrate_type.value if data.substrate_type else "coroplast_4mm",
            "substrate_cost": round(substrate_cost, 2),
            "double_sided": data.double_sided,
            "print_cost": round(vinyl_cost, 2),
            "laminate_cost": round(laminate_cost, 2),
            "complexity": data.complexity,
            "quantity_discount_percent": qty_discount
        }
    )

async def calculate_apparel(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculator for Apparel (t-shirts, hoodies, etc.)"""
    # Blank costs by apparel type (base estimates)
    blank_costs = {
        "tshirt": 4.50,
        "hoodie": 18.00,
        "hat": 8.00,
        "polo": 12.00,
        "tank": 4.00,
        "longsleeve": 7.50,
        "jacket": 25.00,
        "other": 6.00
    }
    blank_cost = data.blank_cost_override or blank_costs.get(
        data.apparel_type.value if data.apparel_type else "tshirt",
        6.00
    )
    
    # Transfer costs by type
    transfer_costs = {
        "htv": 0.50,      # per color per location
        "screen_print": 0.35,
        "dtf": 0.75,
        "sublimation": 1.00,
        "embroidery": 2.50
    }
    transfer_cost_per = transfer_costs.get(
        data.transfer_type.value if data.transfer_type else "htv",
        0.50
    )
    
    # Setup fees by transfer type
    setup_fees = {
        "htv": defaults.get("setup_fee_apparel_dtf", 20),
        "screen_print": defaults.get("setup_fee_apparel_screen", 35) * data.num_colors,
        "dtf": defaults.get("setup_fee_apparel_dtf", 20),
        "sublimation": 15,
        "embroidery": 50
    }
    setup_fee = setup_fees.get(
        data.transfer_type.value if data.transfer_type else "htv",
        20
    )
    
    # Calculate costs
    num_locations = max(1, data.num_print_locations)
    num_colors = max(1, data.num_colors)
    
    blanks_cost = blank_cost * quantity
    transfer_cost = transfer_cost_per * num_colors * num_locations * quantity
    
    # Labor: ~3-5 min per piece depending on complexity
    complexity_mult = get_complexity_multiplier(data.complexity, 1.0, 2.0)
    base_minutes_per_piece = 4
    labor_minutes = base_minutes_per_piece * num_locations * complexity_mult * quantity
    labor_cost = (labor_minutes / 60) * defaults.get("hourly_rate", 75)
    
    production_cost = blanks_cost + transfer_cost + labor_cost + setup_fee
    
    # Quantity discount (apparel often has significant qty breaks)
    qty_discount = get_quantity_discount(quantity, defaults.get("quantity_breaks", {}))
    
    # Suggested price
    markup = defaults.get("default_markup_percent", 100)
    suggested_price = production_cost * (1 + markup / 100) * (1 - qty_discount / 100)
    
    profit = suggested_price - production_cost
    margin = (profit / suggested_price * 100) if suggested_price > 0 else 0
    
    return PricingCalculation(
        material_cost=round(blanks_cost + transfer_cost, 2),
        labor_cost=round(labor_cost, 2),
        setup_cost=round(setup_fee, 2),
        production_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        markup_percent=markup,
        profit_margin_percent=round(margin, 1),
        profit_amount=round(profit, 2),
        estimated_labor_minutes=round(labor_minutes, 1),
        breakdown={
            "apparel_type": data.apparel_type.value if data.apparel_type else "tshirt",
            "blank_cost_each": blank_cost,
            "transfer_type": data.transfer_type.value if data.transfer_type else "htv",
            "num_colors": num_colors,
            "num_print_locations": num_locations,
            "print_locations": data.print_locations,
            "transfer_cost_total": round(transfer_cost, 2),
            "complexity": data.complexity,
            "quantity_discount_percent": qty_discount
        }
    )

async def calculate_vehicle_graphics(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculator for Vehicle Graphics & Wraps"""
    # Vehicle base square footage estimates
    vehicle_sqft = {
        "car_sedan": 150,
        "car_suv": 200,
        "van_mini": 180,
        "van_cargo": 250,
        "van_sprinter": 350,
        "box_truck_12ft": 400,
        "box_truck_16ft": 500,
        "box_truck_24ft": 650,
        "trailer": 450,
        "semi": 800,
        "other": 200
    }
    base_sqft = data.estimated_vehicle_sqft or vehicle_sqft.get(
        data.vehicle_type.value if data.vehicle_type else "car_sedan",
        200
    )
    
    # Coverage multiplier
    coverage_mult = {
        "spot": 0.15,
        "partial": 0.40,
        "half": 0.50,
        "full": 1.0
    }
    coverage = coverage_mult.get(
        data.coverage_type.value if data.coverage_type else "partial",
        0.40
    )
    
    actual_sqft = base_sqft * coverage
    
    # Material costs (premium cast vinyl + laminate for wraps)
    vinyl_cost_per_sqft = 2.50  # Cast vinyl
    laminate_cost_per_sqft = 0.75
    material_cost = actual_sqft * (vinyl_cost_per_sqft + laminate_cost_per_sqft) * quantity
    
    # Print cost
    print_cost = actual_sqft * 0.50 * quantity  # Ink
    
    # Design labor (wraps need significant design time)
    design_hours = actual_sqft * 0.02 * get_complexity_multiplier(data.complexity, 1.0, 2.0)  # ~2 min per sqft
    design_cost = design_hours * defaults.get("design_hourly_rate", 85)
    
    # Install labor (most significant cost)
    install_difficulty = get_complexity_multiplier(data.install_difficulty, 1.0, 2.5)
    install_hours = actual_sqft * 0.05 * install_difficulty  # ~3 min per sqft base
    install_cost = install_hours * defaults.get("install_hourly_rate", 95) * quantity
    
    production_cost = material_cost + print_cost + design_cost + install_cost
    
    # Apply minimum
    min_charge = defaults.get("minimum_wrap_charge", 500)
    production_cost = max(production_cost, min_charge)
    
    # Suggested price (wraps typically 80-120% markup)
    markup = 100
    suggested_price = production_cost * (1 + markup / 100)
    
    profit = suggested_price - production_cost
    margin = (profit / suggested_price * 100) if suggested_price > 0 else 0
    
    return PricingCalculation(
        material_cost=round(material_cost + print_cost, 2),
        labor_cost=round(design_cost + install_cost, 2),
        production_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        markup_percent=markup,
        profit_margin_percent=round(margin, 1),
        profit_amount=round(profit, 2),
        estimated_labor_minutes=round((design_hours + install_hours) * 60, 1),
        breakdown={
            "vehicle_type": data.vehicle_type.value if data.vehicle_type else "car_sedan",
            "vehicle_make": data.vehicle_make,
            "vehicle_model": data.vehicle_model,
            "coverage_type": data.coverage_type.value if data.coverage_type else "partial",
            "base_vehicle_sqft": base_sqft,
            "coverage_multiplier": coverage,
            "actual_sqft": round(actual_sqft, 2),
            "material_cost": round(material_cost, 2),
            "design_hours": round(design_hours, 1),
            "design_cost": round(design_cost, 2),
            "install_hours": round(install_hours, 1),
            "install_cost": round(install_cost, 2),
            "install_difficulty": data.install_difficulty
        }
    )

async def calculate_custom(data: JobItemPricingData, quantity: float, defaults: dict) -> PricingCalculation:
    """Calculator for Custom/Other items (simple manual entry)"""
    # Custom items use manual price entry - minimal calculation
    unit_cost = data.unit_cost or 0
    markup = data.markup_percent if data.markup_percent is not None else defaults.get("default_markup_percent", 100)
    
    production_cost = unit_cost * quantity
    suggested_price = production_cost * (1 + markup / 100)
    
    profit = suggested_price - production_cost
    margin = (profit / suggested_price * 100) if suggested_price > 0 else 0
    
    return PricingCalculation(
        production_cost=round(production_cost, 2),
        suggested_price=round(suggested_price, 2),
        markup_percent=markup,
        profit_margin_percent=round(margin, 1),
        profit_amount=round(profit, 2),
        breakdown={
            "type": "custom_manual_entry",
            "unit_cost": unit_cost,
            "quantity": quantity,
            "markup_percent": markup
        }
    )

# Main calculator dispatcher
async def calculate_pricing(
    category: PricingCategory,
    pricing_data: JobItemPricingData,
    quantity: float,
    tenant_id: str
) -> PricingCalculation:
    """Main entry point for pricing calculation"""
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
    return await calculator(pricing_data, quantity, defaults)

# ============== PRICING API ENDPOINTS ==============

class PriceCalculateRequest(BaseModel):
    category: PricingCategory
    pricing_data: JobItemPricingData
    quantity: float = 1

@api_router.post("/pricing/calculate")
async def calculate_price(
    request: PriceCalculateRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Calculate pricing for an item (real-time preview)"""
    try:
        calculation = await calculate_pricing(
            request.category,
            request.pricing_data,
            request.quantity,
            current_user.tenant_id
        )
        return calculation.model_dump()
    except Exception as e:
        logger.error(f"Pricing calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

@api_router.get("/pricing/defaults")
async def get_my_pricing_defaults(current_user: UserInDB = Depends(get_current_active_user)):
    """Get pricing defaults for current tenant"""
    defaults = await get_pricing_defaults(current_user.tenant_id)
    return defaults

@api_router.put("/pricing/defaults")
async def update_pricing_defaults(
    updates: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update pricing defaults for current tenant"""
    tenant_id = current_user.tenant_id
    
    # Ensure defaults exist
    await get_pricing_defaults(tenant_id)
    
    # Update
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.pricing_defaults.update_one(
        {"tenant_id": tenant_id},
        {"$set": updates}
    )
    
    return await get_pricing_defaults(tenant_id)

@api_router.get("/pricing/materials")
async def get_materials(
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get available materials (for dropdowns)"""
    # Return built-in materials organized by category
    materials = {
        "vinyl": [
            {"id": "oracal_651", "name": "Oracal 651 (Intermediate)", "cost_per_sqft": 0.50},
            {"id": "oracal_751", "name": "Oracal 751 (High Performance)", "cost_per_sqft": 0.75},
            {"id": "oracal_951", "name": "Oracal 951 (Premium Cast)", "cost_per_sqft": 1.25},
            {"id": "avery_hp750", "name": "Avery HP750", "cost_per_sqft": 0.90},
            {"id": "reflective", "name": "Reflective Vinyl", "cost_per_sqft": 2.50},
            {"id": "specialty", "name": "Specialty Vinyl", "cost_per_sqft": 1.50},
        ],
        "print_material": [
            {"id": "banner_13oz", "name": "13oz Banner", "cost_per_sqft": 0.75},
            {"id": "banner_18oz", "name": "18oz Banner (Heavy)", "cost_per_sqft": 1.10},
            {"id": "vinyl_adhesive", "name": "Adhesive Vinyl", "cost_per_sqft": 1.25},
            {"id": "poster_paper", "name": "Poster Paper", "cost_per_sqft": 0.35},
            {"id": "canvas", "name": "Canvas", "cost_per_sqft": 2.50},
            {"id": "backlit", "name": "Backlit Film", "cost_per_sqft": 2.00},
            {"id": "perforated", "name": "Perforated Window Film", "cost_per_sqft": 1.75},
        ],
        "substrate": [
            {"id": "coroplast_4mm", "name": "Coroplast 4mm", "cost_per_sqft": 0.45},
            {"id": "coroplast_10mm", "name": "Coroplast 10mm", "cost_per_sqft": 0.65},
            {"id": "aluminum_040", "name": "Aluminum .040", "cost_per_sqft": 1.50},
            {"id": "aluminum_063", "name": "Aluminum .063", "cost_per_sqft": 2.25},
            {"id": "aluminum_080", "name": "Aluminum .080", "cost_per_sqft": 3.00},
            {"id": "pvc_3mm", "name": "PVC 3mm", "cost_per_sqft": 1.00},
            {"id": "pvc_6mm", "name": "PVC 6mm", "cost_per_sqft": 1.50},
            {"id": "acrylic", "name": "Acrylic", "cost_per_sqft": 4.00},
            {"id": "dibond", "name": "Dibond/ACM", "cost_per_sqft": 3.50},
            {"id": "mdo", "name": "MDO Plywood", "cost_per_sqft": 2.00},
        ],
        "apparel": [
            {"id": "tshirt", "name": "T-Shirt", "cost_each": 4.50},
            {"id": "hoodie", "name": "Hoodie", "cost_each": 18.00},
            {"id": "hat", "name": "Hat/Cap", "cost_each": 8.00},
            {"id": "polo", "name": "Polo Shirt", "cost_each": 12.00},
            {"id": "tank", "name": "Tank Top", "cost_each": 4.00},
            {"id": "longsleeve", "name": "Long Sleeve", "cost_each": 7.50},
            {"id": "jacket", "name": "Jacket", "cost_each": 25.00},
        ],
        "transfer_type": [
            {"id": "htv", "name": "HTV (Heat Transfer Vinyl)", "cost_per_color": 0.50},
            {"id": "screen_print", "name": "Screen Print", "cost_per_color": 0.35},
            {"id": "dtf", "name": "DTF (Direct to Film)", "cost_per_color": 0.75},
            {"id": "sublimation", "name": "Sublimation", "cost_per_color": 1.00},
            {"id": "embroidery", "name": "Embroidery", "cost_per_stitch": 0.01},
        ],
        "vehicle_type": [
            {"id": "car_sedan", "name": "Car (Sedan)", "base_sqft": 150},
            {"id": "car_suv", "name": "Car (SUV)", "base_sqft": 200},
            {"id": "van_mini", "name": "Minivan", "base_sqft": 180},
            {"id": "van_cargo", "name": "Cargo Van", "base_sqft": 250},
            {"id": "van_sprinter", "name": "Sprinter Van", "base_sqft": 350},
            {"id": "box_truck_12ft", "name": "Box Truck (12ft)", "base_sqft": 400},
            {"id": "box_truck_16ft", "name": "Box Truck (16ft)", "base_sqft": 500},
            {"id": "box_truck_24ft", "name": "Box Truck (24ft)", "base_sqft": 650},
            {"id": "trailer", "name": "Trailer", "base_sqft": 450},
            {"id": "semi", "name": "Semi Truck", "base_sqft": 800},
        ]
    }
    
    if category:
        return {category: materials.get(category, [])}
    return materials

# ============== PRICING TEMPLATES API ==============

class PricingTemplate(BaseModel):
    """Saved pricing template for quick reuse"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: Optional[str] = None
    category: PricingCategory
    pricing_data: Dict[str, Any]
    quantity: float = 1
    is_favorite: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PricingTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: PricingCategory
    pricing_data: Dict[str, Any]
    quantity: float = 1

@api_router.get("/pricing/templates")
async def get_pricing_templates(
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all pricing templates for the current tenant"""
    query = {"tenant_id": current_user.tenant_id}
    if category:
        query["category"] = category
    
    templates = await db.pricing_templates.find(query, {"_id": 0}).sort("name", 1).to_list(100)
    return templates

@api_router.post("/pricing/templates")
async def create_pricing_template(
    input: PricingTemplateCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Save a new pricing template"""
    template = PricingTemplate(
        tenant_id=current_user.tenant_id,
        name=input.name,
        description=input.description,
        category=input.category,
        pricing_data=input.pricing_data,
        quantity=input.quantity
    )
    await db.pricing_templates.insert_one(template.model_dump())
    return template.model_dump()

@api_router.put("/pricing/templates/{template_id}")
async def update_pricing_template(
    template_id: str,
    updates: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a pricing template"""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.pricing_templates.update_one(
        {"id": template_id, "tenant_id": current_user.tenant_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = await db.pricing_templates.find_one({"id": template_id}, {"_id": 0})
    return template

@api_router.delete("/pricing/templates/{template_id}")
async def delete_pricing_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a pricing template"""
    result = await db.pricing_templates.delete_one(
        {"id": template_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"message": "Template deleted"}

@api_router.put("/pricing/templates/{template_id}/favorite")
async def toggle_template_favorite(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Toggle favorite status of a template"""
    template = await db.pricing_templates.find_one(
        {"id": template_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    new_status = not template.get("is_favorite", False)
    await db.pricing_templates.update_one(
        {"id": template_id},
        {"$set": {"is_favorite": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"is_favorite": new_status}

# ============== CUSTOMER PORTAL API ==============

# Customer Portal Auth Models
class CustomerPortalLogin(BaseModel):
    email: str
    password: str

class CustomerPortalRegister(BaseModel):
    email: str
    password: str

class CustomerPortalToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_id: str
    customer_name: str

class CustomerProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_tax_exempt: Optional[bool] = None
    tax_exempt_document_url: Optional[str] = None
    notification_preferences: Optional[Dict[str, bool]] = None

class ConversationCreate(BaseModel):
    subject: str
    message: str
    related_job_id: Optional[str] = None
    related_quote_id: Optional[str] = None

class MessageCreate(BaseModel):
    content: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None

class ProofResponseCreate(BaseModel):
    status: ProofStatus  # approved, rejected, revision_requested
    comment: Optional[str] = None

# Helper to get current portal customer from JWT
async def get_current_portal_customer(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get customer from portal JWT token"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate portal credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        raise credentials_exception
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        customer_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if customer_id is None or token_type != "portal":
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Portal token has expired")
    except jwt.PyJWTError:
        raise credentials_exception
    
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if customer is None:
        raise credentials_exception
    
    if not customer.get("portal_enabled", False):
        raise HTTPException(status_code=403, detail="Portal access is disabled for this account")
    
    return customer

# -------------- CUSTOMER PORTAL AUTH --------------

@api_router.post("/portal/auth/register", response_model=CustomerPortalToken)
async def portal_register(input: CustomerPortalRegister):
    """Register/enable portal access for an existing customer"""
    # Find customer by email
    customer = await db.customers.find_one({"email": input.email.lower()}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="No customer account found with this email. Please contact the sign shop.")
    
    if customer.get("portal_enabled") and customer.get("portal_password_hash"):
        raise HTTPException(status_code=400, detail="Portal access already enabled. Please login instead.")
    
    # Hash password and enable portal
    hashed_password = get_password_hash(input.password)
    await db.customers.update_one(
        {"id": customer["id"]},
        {"$set": {
            "portal_password_hash": hashed_password,
            "portal_enabled": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Create portal token
    access_token = create_access_token(
        data={"sub": customer["id"], "type": "portal"},
        expires_delta=timedelta(days=30)
    )
    
    return CustomerPortalToken(
        access_token=access_token,
        customer_id=customer["id"],
        customer_name=customer["name"]
    )

@api_router.post("/portal/auth/login", response_model=CustomerPortalToken)
async def portal_login(input: CustomerPortalLogin):
    """Login to customer portal"""
    customer = await db.customers.find_one({"email": input.email.lower()}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not customer.get("portal_enabled"):
        raise HTTPException(status_code=403, detail="Portal access is not enabled for this account")
    
    if not customer.get("portal_password_hash"):
        raise HTTPException(status_code=400, detail="Portal password not set. Please register first.")
    
    if not verify_password(input.password, customer["portal_password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create portal token
    access_token = create_access_token(
        data={"sub": customer["id"], "type": "portal"},
        expires_delta=timedelta(days=30)
    )
    
    return CustomerPortalToken(
        access_token=access_token,
        customer_id=customer["id"],
        customer_name=customer["name"]
    )

# -------------- CUSTOMER PORTAL PROFILE --------------

@api_router.get("/portal/profile")
async def get_portal_profile(customer: dict = Depends(get_current_portal_customer)):
    """Get current customer's profile"""
    # Remove sensitive fields
    safe_customer = {k: v for k, v in customer.items() if k != "portal_password_hash"}
    return safe_customer

@api_router.put("/portal/profile")
async def update_portal_profile(
    input: CustomerProfileUpdate,
    customer: dict = Depends(get_current_portal_customer)
):
    """Update customer profile"""
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.customers.update_one(
        {"id": customer["id"]},
        {"$set": update_data}
    )
    
    updated = await db.customers.find_one({"id": customer["id"]}, {"_id": 0, "portal_password_hash": 0})
    return updated

@api_router.put("/portal/change-password")
async def change_portal_password(
    current_password: str,
    new_password: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Change portal password"""
    if not verify_password(current_password, customer.get("portal_password_hash", "")):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    hashed = get_password_hash(new_password)
    await db.customers.update_one(
        {"id": customer["id"]},
        {"$set": {"portal_password_hash": hashed, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Password changed successfully"}

# -------------- CUSTOMER PORTAL DASHBOARD --------------

@api_router.get("/portal/dashboard")
async def get_portal_dashboard(customer: dict = Depends(get_current_portal_customer)):
    """Get customer portal dashboard data"""
    customer_id = customer["id"]
    
    # Get counts
    total_quotes = await db.quotes.count_documents({"customer_id": customer_id})
    active_jobs = await db.jobs.count_documents({"customer_id": customer_id, "status": {"$nin": ["complete", "archived"]}})
    pending_invoices = await db.invoices.count_documents({"customer_id": customer_id, "status": {"$in": ["sent", "draft"]}})
    pending_proofs = await db.artwork_proofs.count_documents({"customer_id": customer_id, "status": "pending"})
    
    # Get unread message count
    conversations = await db.conversations.find({"customer_id": customer_id}, {"_id": 0}).to_list(100)
    unread_messages = sum(c.get("unread_customer", 0) for c in conversations)
    
    # Get unread notifications
    unread_notifications = await db.customer_notifications.count_documents({"customer_id": customer_id, "is_read": False})
    
    # Get upcoming appointments
    today = datetime.now(timezone.utc).date().isoformat()
    upcoming_appointments = await db.appointments.find(
        {"customer_id": customer_id, "scheduled_date": {"$gte": today}, "status": {"$in": ["scheduled", "confirmed"]}},
        {"_id": 0}
    ).sort("scheduled_date", 1).limit(5).to_list(5)
    
    # Get recent jobs
    recent_jobs = await db.jobs.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Get recent invoices
    recent_invoices = await db.invoices.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "stats": {
            "total_quotes": total_quotes,
            "active_jobs": active_jobs,
            "pending_invoices": pending_invoices,
            "pending_proofs": pending_proofs,
            "unread_messages": unread_messages,
            "unread_notifications": unread_notifications
        },
        "upcoming_appointments": upcoming_appointments,
        "recent_jobs": recent_jobs,
        "recent_invoices": recent_invoices
    }

# -------------- CUSTOMER PORTAL ORDERS/JOBS --------------

@api_router.get("/portal/orders")
async def get_portal_orders(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's orders (jobs)"""
    query = {"customer_id": customer["id"]}
    if status:
        query["status"] = status
    
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with items
    for job in jobs:
        items = await db.job_items.find({"job_id": job["id"]}, {"_id": 0}).to_list(50)
        job["items"] = items
    
    return jobs

@api_router.get("/portal/orders/{job_id}")
async def get_portal_order_detail(
    job_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get single order detail"""
    job = await db.jobs.find_one({"id": job_id, "customer_id": customer["id"]}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get items
    items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(50)
    job["items"] = items
    
    # Get associated quote if any
    if job.get("quote_id"):
        quote = await db.quotes.find_one({"id": job["quote_id"]}, {"_id": 0})
        job["quote"] = quote
    
    # Get associated invoice if any
    if job.get("invoice_id"):
        invoice = await db.invoices.find_one({"id": job["invoice_id"]}, {"_id": 0})
        job["invoice"] = invoice
    
    # Get artwork proofs
    proofs = await db.artwork_proofs.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(20)
    job["proofs"] = proofs
    
    return job

@api_router.get("/portal/quotes")
async def get_portal_quotes(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's quotes"""
    query = {"customer_id": customer["id"]}
    if status:
        query["status"] = status
    
    quotes = await db.quotes.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return quotes

@api_router.get("/portal/invoices")
async def get_portal_invoices(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's invoices"""
    query = {"customer_id": customer["id"]}
    if status:
        query["status"] = status
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return invoices

# -------------- CUSTOMER PORTAL MESSAGING --------------

@api_router.get("/portal/conversations")
async def get_portal_conversations(customer: dict = Depends(get_current_portal_customer)):
    """Get all conversations for the customer"""
    conversations = await db.conversations.find(
        {"customer_id": customer["id"]},
        {"_id": 0}
    ).sort("last_message_at", -1).to_list(100)
    return conversations

@api_router.post("/portal/conversations")
async def create_portal_conversation(
    input: ConversationCreate,
    customer: dict = Depends(get_current_portal_customer)
):
    """Start a new conversation"""
    conversation = Conversation(
        customer_id=customer["id"],
        tenant_id=customer.get("tenant_id"),
        subject=input.subject,
        related_job_id=input.related_job_id,
        related_quote_id=input.related_quote_id,
        last_message_preview=input.message[:100],
        unread_shop=1
    )
    
    await db.conversations.insert_one(conversation.model_dump())
    
    # Create first message
    message = ConversationMessage(
        conversation_id=conversation.id,
        sender_type="customer",
        sender_id=customer["id"],
        sender_name=customer["name"],
        content=input.message
    )
    await db.conversation_messages.insert_one(message.model_dump())
    
    return conversation.model_dump()

@api_router.get("/portal/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get messages in a conversation"""
    # Verify conversation belongs to customer
    conv = await db.conversations.find_one({"id": conversation_id, "customer_id": customer["id"]}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    messages = await db.conversation_messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    # Mark as read
    await db.conversation_messages.update_many(
        {"conversation_id": conversation_id, "sender_type": "shop", "is_read": False},
        {"$set": {"is_read": True}}
    )
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"unread_customer": 0}}
    )
    
    return {"conversation": conv, "messages": messages}

@api_router.post("/portal/conversations/{conversation_id}/messages")
async def send_portal_message(
    conversation_id: str,
    input: MessageCreate,
    customer: dict = Depends(get_current_portal_customer)
):
    """Send a message in a conversation"""
    # Verify conversation belongs to customer
    conv = await db.conversations.find_one({"id": conversation_id, "customer_id": customer["id"]}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.get("is_closed"):
        raise HTTPException(status_code=400, detail="This conversation is closed")
    
    # Create message
    message = ConversationMessage(
        conversation_id=conversation_id,
        sender_type="customer",
        sender_id=customer["id"],
        sender_name=customer["name"],
        content=input.content,
        file_url=input.file_url,
        file_name=input.file_name,
        message_type=MessageType.FILE if input.file_url else MessageType.TEXT
    )
    await db.conversation_messages.insert_one(message.model_dump())
    
    # Update conversation
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {
            "last_message_at": datetime.now(timezone.utc).isoformat(),
            "last_message_preview": input.content[:100]
        }, "$inc": {"unread_shop": 1}}
    )
    
    return message.model_dump()

# -------------- CUSTOMER PORTAL ARTWORK PROOFS --------------

@api_router.get("/portal/proofs")
async def get_portal_proofs(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get all artwork proofs for the customer"""
    query = {"customer_id": customer["id"]}
    if status:
        query["status"] = status
    
    proofs = await db.artwork_proofs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with job info
    for proof in proofs:
        job = await db.jobs.find_one({"id": proof["job_id"]}, {"_id": 0, "id": 1, "name": 1})
        proof["job"] = job
    
    return proofs

@api_router.get("/portal/proofs/{proof_id}")
async def get_portal_proof_detail(
    proof_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get single proof detail"""
    proof = await db.artwork_proofs.find_one({"id": proof_id, "customer_id": customer["id"]}, {"_id": 0})
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    
    # Get job info
    job = await db.jobs.find_one({"id": proof["job_id"]}, {"_id": 0})
    proof["job"] = job
    
    return proof

@api_router.post("/portal/proofs/{proof_id}/respond")
async def respond_to_proof(
    proof_id: str,
    input: ProofResponseCreate,
    customer: dict = Depends(get_current_portal_customer)
):
    """Approve, reject, or request revision on a proof"""
    proof = await db.artwork_proofs.find_one({"id": proof_id, "customer_id": customer["id"]}, {"_id": 0})
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    
    if proof.get("status") != "pending":
        raise HTTPException(status_code=400, detail="This proof has already been responded to")
    
    update_data = {
        "status": input.status.value,
        "customer_comment": input.comment
    }
    
    if input.status == ProofStatus.APPROVED:
        update_data["approved_at"] = datetime.now(timezone.utc).isoformat()
    elif input.status == ProofStatus.REJECTED:
        update_data["rejected_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.artwork_proofs.update_one({"id": proof_id}, {"$set": update_data})
    
    # Create notification for shop (could trigger email too)
    status_text = "approved" if input.status == ProofStatus.APPROVED else "rejected" if input.status == ProofStatus.REJECTED else "requested revisions on"
    notification = CustomerNotification(
        tenant_id=customer.get("tenant_id"),
        customer_id=customer["id"],
        notification_type="approval",
        title=f"Proof {status_text}",
        message=f"{customer['name']} has {status_text} proof for job {proof.get('job_id', '')[:8]}",
        related_id=proof_id
    )
    await db.customer_notifications.insert_one(notification.model_dump())
    
    updated = await db.artwork_proofs.find_one({"id": proof_id}, {"_id": 0})
    return updated

# -------------- CUSTOMER PORTAL NOTIFICATIONS --------------

@api_router.get("/portal/notifications")
async def get_portal_notifications(
    unread_only: bool = False,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer notifications"""
    query = {"customer_id": customer["id"]}
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.customer_notifications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return notifications

@api_router.put("/portal/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Mark notification as read"""
    result = await db.customer_notifications.update_one(
        {"id": notification_id, "customer_id": customer["id"]},
        {"$set": {"is_read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Marked as read"}

@api_router.put("/portal/notifications/read-all")
async def mark_all_notifications_read(customer: dict = Depends(get_current_portal_customer)):
    """Mark all notifications as read"""
    await db.customer_notifications.update_many(
        {"customer_id": customer["id"], "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All notifications marked as read"}

# -------------- CUSTOMER PORTAL APPOINTMENTS --------------

@api_router.get("/portal/appointments")
async def get_portal_appointments(
    upcoming_only: bool = False,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's appointments"""
    query = {"customer_id": customer["id"]}
    if upcoming_only:
        today = datetime.now(timezone.utc).date().isoformat()
        query["scheduled_date"] = {"$gte": today}
        query["status"] = {"$in": ["scheduled", "confirmed"]}
    
    appointments = await db.appointments.find(query, {"_id": 0}).sort("scheduled_date", 1).to_list(100)
    return appointments

@api_router.get("/portal/appointments/{appointment_id}")
async def get_portal_appointment_detail(
    appointment_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get appointment detail"""
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "customer_id": customer["id"]},
        {"_id": 0}
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Get linked job if any
    if appointment.get("job_id"):
        job = await db.jobs.find_one({"id": appointment["job_id"]}, {"_id": 0, "id": 1, "name": 1, "status": 1})
        appointment["job"] = job
    
    return appointment

# -------------- SHOP-SIDE PORTAL MANAGEMENT --------------
# These endpoints are for the shop to manage portal-related items

@api_router.post("/customers/{customer_id}/enable-portal")
async def enable_customer_portal(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Enable portal access for a customer (sends invite)"""
    customer = await db.customers.find_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.get("email"):
        raise HTTPException(status_code=400, detail="Customer must have an email address")
    
    # Enable portal (customer will set password on first login)
    await db.customers.update_one(
        {"id": customer_id},
        {"$set": {"portal_enabled": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Portal access enabled for {customer['name']}. Customer can now register at the portal."}

@api_router.post("/customers/{customer_id}/disable-portal")
async def disable_customer_portal(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Disable portal access for a customer"""
    result = await db.customers.update_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id},
        {"$set": {"portal_enabled": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {"message": "Portal access disabled"}

@api_router.get("/shop/conversations")
async def get_shop_conversations(
    unread_only: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all conversations for the shop"""
    query = {"tenant_id": current_user.tenant_id}
    if unread_only:
        query["unread_shop"] = {"$gt": 0}
    
    conversations = await db.conversations.find(query, {"_id": 0}).sort("last_message_at", -1).to_list(100)
    
    # Enrich with customer info
    for conv in conversations:
        customer = await db.customers.find_one({"id": conv["customer_id"]}, {"_id": 0, "id": 1, "name": 1, "email": 1, "company": 1})
        conv["customer"] = customer
    
    return conversations

@api_router.get("/shop/conversations/{conversation_id}/messages")
async def get_shop_conversation_messages(
    conversation_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get messages for a conversation (shop side)"""
    conv = await db.conversations.find_one(
        {"id": conversation_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await db.conversation_messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    # Mark shop messages as read
    await db.conversation_messages.update_many(
        {"conversation_id": conversation_id, "sender_type": "customer", "is_read": False},
        {"$set": {"is_read": True}}
    )
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"unread_shop": 0}}
    )
    
    # Get customer info
    customer = await db.customers.find_one({"id": conv["customer_id"]}, {"_id": 0, "id": 1, "name": 1, "email": 1, "company": 1})
    
    return {"conversation": conv, "messages": messages, "customer": customer}

@api_router.post("/shop/conversations/{conversation_id}/messages")
async def send_shop_message(
    conversation_id: str,
    input: MessageCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Send message from shop to customer"""
    conv = await db.conversations.find_one(
        {"id": conversation_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    message = ConversationMessage(
        conversation_id=conversation_id,
        sender_type="shop",
        sender_id=current_user.id,
        sender_name=current_user.full_name,
        content=input.content,
        file_url=input.file_url,
        file_name=input.file_name,
        message_type=MessageType.FILE if input.file_url else MessageType.TEXT
    )
    await db.conversation_messages.insert_one(message.model_dump())
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {
            "last_message_at": datetime.now(timezone.utc).isoformat(),
            "last_message_preview": input.content[:100]
        }, "$inc": {"unread_customer": 1}}
    )
    
    return message.model_dump()

@api_router.post("/shop/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Close a conversation"""
    result = await db.conversations.update_one(
        {"id": conversation_id, "tenant_id": current_user.tenant_id},
        {"$set": {"is_closed": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation closed"}

@api_router.post("/shop/proofs")
async def create_artwork_proof(
    job_id: str,
    file_url: str,
    file_name: str,
    description: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Upload an artwork proof for customer review"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get latest version number
    latest = await db.artwork_proofs.find_one(
        {"job_id": job_id},
        {"_id": 0, "version": 1},
        sort=[("version", -1)]
    )
    version = (latest.get("version", 0) if latest else 0) + 1
    
    proof = ArtworkProof(
        tenant_id=current_user.tenant_id,
        job_id=job_id,
        customer_id=job["customer_id"],
        version=version,
        file_url=file_url,
        file_name=file_name,
        description=description
    )
    await db.artwork_proofs.insert_one(proof.model_dump())
    
    # Create notification for customer
    notification = CustomerNotification(
        tenant_id=current_user.tenant_id,
        customer_id=job["customer_id"],
        notification_type="approval",
        title="New Artwork Proof",
        message=f"A new proof (v{version}) is ready for your review",
        link=f"/portal/proofs/{proof.id}",
        related_id=proof.id
    )
    await db.customer_notifications.insert_one(notification.model_dump())
    
    return proof.model_dump()

@api_router.get("/shop/proofs")
async def get_shop_proofs(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all proofs (shop side)"""
    query = {"tenant_id": current_user.tenant_id}
    if job_id:
        query["job_id"] = job_id
    if status:
        query["status"] = status
    
    proofs = await db.artwork_proofs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with customer/job info
    for proof in proofs:
        job = await db.jobs.find_one({"id": proof["job_id"]}, {"_id": 0, "id": 1, "name": 1})
        customer = await db.customers.find_one({"id": proof["customer_id"]}, {"_id": 0, "id": 1, "name": 1})
        proof["job"] = job
        proof["customer"] = customer
    
    return proofs

@api_router.post("/shop/appointments")
async def create_appointment(
    customer_id: str,
    appointment_type: AppointmentType,
    title: str,
    scheduled_date: str,
    scheduled_time: str,
    job_id: Optional[str] = None,
    description: Optional[str] = None,
    duration_minutes: int = 60,
    location: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create an appointment for a customer"""
    customer = await db.customers.find_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    appointment = Appointment(
        tenant_id=current_user.tenant_id,
        customer_id=customer_id,
        job_id=job_id,
        appointment_type=appointment_type,
        title=title,
        description=description,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        duration_minutes=duration_minutes,
        location=location
    )
    await db.appointments.insert_one(appointment.model_dump())
    
    # Create notification for customer
    notification = CustomerNotification(
        tenant_id=current_user.tenant_id,
        customer_id=customer_id,
        notification_type="appointment",
        title="New Appointment Scheduled",
        message=f"{title} on {scheduled_date} at {scheduled_time}",
        link=f"/portal/appointments/{appointment.id}",
        related_id=appointment.id
    )
    await db.customer_notifications.insert_one(notification.model_dump())
    
    return appointment.model_dump()

@api_router.get("/shop/appointments")
async def get_shop_appointments(
    customer_id: Optional[str] = None,
    upcoming_only: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all appointments (shop side)"""
    query = {"tenant_id": current_user.tenant_id}
    if customer_id:
        query["customer_id"] = customer_id
    if upcoming_only:
        today = datetime.now(timezone.utc).date().isoformat()
        query["scheduled_date"] = {"$gte": today}
    
    appointments = await db.appointments.find(query, {"_id": 0}).sort("scheduled_date", 1).to_list(100)
    
    # Enrich with customer info
    for apt in appointments:
        customer = await db.customers.find_one({"id": apt["customer_id"]}, {"_id": 0, "id": 1, "name": 1, "phone": 1})
        apt["customer"] = customer
    
    return appointments

@api_router.put("/shop/appointments/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: str,
    status: AppointmentStatus,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update appointment status"""
    result = await db.appointments.update_one(
        {"id": appointment_id, "tenant_id": current_user.tenant_id},
        {"$set": {"status": status.value}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {"message": f"Appointment status updated to {status.value}"}

# -------------- DASHBOARD STATS --------------
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Count totals
    total_customers = await db.customers.count_documents({})
    active_jobs = await db.jobs.count_documents({"status": {"$nin": ["complete"]}})
    pending_invoices = await db.invoices.count_documents({"status": {"$in": ["sent", "overdue"]}})
    
    # Get today's sales
    today_sales = await db.sales_entries.find({"date": today}, {"_id": 0}).to_list(100)
    today_revenue = sum(s["amount"] for s in today_sales)
    
    # Get overdue invoices
    overdue_invoices = await db.invoices.find({"status": "overdue"}, {"_id": 0}).to_list(100)
    overdue_total = sum(i["total"] for i in overdue_invoices)
    
    return {
        "total_customers": total_customers,
        "active_jobs": active_jobs,
        "pending_invoices": pending_invoices,
        "today_revenue": today_revenue,
        "overdue_total": overdue_total,
        "overdue_count": len(overdue_invoices)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
