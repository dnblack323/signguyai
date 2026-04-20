"""
All enums used across the SignGuy AI application.
"""
from enum import Enum

# ============== CUSTOMER & CRM ENUMS ==============
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
    QUOTE = "quote"           # Pipeline stage - not approved yet
    APPROVED = "approved"     # Ready to produce
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INVOICED = "invoiced"
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

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"

# ============== PRICING CALCULATOR ENUMS ==============
class PricingCategory(str, Enum):
    PROMOTIONAL = "promotional"
    CUT_VINYL = "cut_vinyl"
    SERVICES = "services"
    DIGITAL_PRINT = "digital_print"
    RIGID_SIGNS = "rigid_signs"
    BANNERS = "banners"
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
    PICKUP = "pickup"
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
    CUSTOM = "custom"

class PromoProductType(str, Enum):
    MAGNETS = "magnets"
    YARD_SIGNS = "yard_signs"
    LICENSE_PLATES = "license_plates"
    STICKERS = "stickers"
    BRANDED_ITEMS = "branded_items"
    CUSTOM = "custom"

# ============== EMPLOYEE & PAYROLL ENUMS ==============
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

# ============== AUTH & TENANT ENUMS ==============
class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    STAFF = "staff"

class TenantPlan(str, Enum):
    """Tenant plan - maps to tier for feature gating"""
    STARTER = "starter"    # Starter tier
    PRO = "pro"            # Pro tier
    BUSINESS = "business"  # Business tier
    FOUNDERS_EDITION = "founders_edition"  # Founders Edition - all features, 150 credits/month

class PaymentMethod(str, Enum):
    CASH = "cash"
    CHECK = "check"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    OTHER = "other"

# ============== CUSTOMER PORTAL ENUMS ==============
class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"

class ProofStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    REJECTED = "rejected"

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    INSTALLATION = "installation"
    PICKUP = "pickup"
    SITE_SURVEY = "site_survey"
    OTHER = "other"

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

# ============== WEBSTORE ENUMS ==============
class WebstoreType(str, Enum):
    B2B = "b2b"
    FUNDRAISER = "fundraiser"
    CREATOR = "creator"

class WebstoreStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
