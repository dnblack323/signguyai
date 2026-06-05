"""
Webstore Routes

This module contains all routes related to:
- Master Product Catalog (sign shop's products)
- Webstores (B2B, Fundraiser, Creator stores)
- Webstore product assignments
- Webstore orders (public ordering)
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import Response
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, ConfigDict
import uuid
from enum import Enum
import os
import stripe

# Import from server module
from server import db, logger, get_current_active_user

from models import UserInDB, JobStatus, JobItemType, JobItemStatus
from models.auth import Permission, user_has_permission
from services.object_storage import put_object, get_object
from services.storage_config import APP_NAME


# Extensions we'll use per content-type for object-storage paths.
_IMAGE_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _webstore_asset_path(webstore_id: str, kind: str, content_type: str) -> str:
    """Deterministic storage path for a webstore asset (logo/banner)."""
    ext = _IMAGE_EXT.get(content_type, ".bin")
    return f"{APP_NAME}/webstores/{webstore_id}/{kind}{ext}"


def _require_permission(user: UserInDB, perm: Permission):
    """Raise 403 if the user's role does not carry the given permission."""
    if not user_has_permission(user.role, perm):
        raise HTTPException(
            status_code=403,
            detail=f"You don't have permission to perform this action ({perm.value}).",
        )


stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

from services.stripe_service import get_stripe_account_checkout_status as _get_stripe_checkout_status
from services.stripe_service import finalize_webstore_stripe_checkout  # noqa: F401 — re-exported for backward compat


# ============== LOCAL MODELS (to be moved to models/webstore.py) ==============

class WebstoreType(str, Enum):
    BUSINESS = "business"
    FUNDRAISER = "fundraiser"
    CREATOR = "creator"
    EVENT = "event"

class WebstoreStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING = "pending"
    # Phase 6 — lifecycle close-out states. Admin sets COMPLETED via the
    # mark_completed stage stamp; CLOSED is reserved for owner-initiated
    # close (e.g. fundraiser ended). Both walk the lifecycle past
    # "store_closed".
    COMPLETED = "completed"
    CLOSED = "closed"

class ProductCategory(str, Enum):
    APPAREL = "apparel"
    SIGNS = "signs"
    DECALS = "decals"
    PROMOTIONAL = "promotional"
    EVENTS = "events"
    OTHER = "other"

# Apparel tiers for default options
class ApparelTier(str, Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"

# Default apparel tier configurations
APPAREL_TIER_DEFAULTS = {
    "economy": {"name": "Economy", "description": "Budget-friendly option", "price_modifier": 0},
    "standard": {"name": "Standard", "description": "Great quality at a good price", "price_modifier": 5},
    "premium": {"name": "Premium", "description": "Top-tier quality materials", "price_modifier": 12}
}

# Common sizes for apparel and decals
APPAREL_SIZES = ["XS", "S", "M", "L", "XL", "2XL", "3XL"]
DECAL_SIZES = ["Small (3\")", "Medium (6\")", "Large (12\")", "XL (18\")", "Custom"]


class LockedSettings(BaseModel):
    """Tenant-controlled financial and operational settings.

    These values are set and locked by the shop admin (tenant).
    They MUST NOT be overwritten by questionnaire answers, store-owner
    actions, or any other non-admin flow.
    """
    # Pricing / cost breakdown
    base_item_cost: Optional[float] = None
    production_cost: Optional[float] = None
    retail_price: Optional[float] = None
    store_owner_profit: Optional[float] = None
    profit_split: Optional[float] = None        # % of net profit to store owner
    # Individual fees
    setup_fee: Optional[float] = None
    shipping_fee: Optional[float] = None
    handling_fee: Optional[float] = None
    # Shipping & handling bundle (overrides individual fees when enabled)
    shipping_handling_enabled: bool = False
    shipping_handling_fee: Optional[float] = None
    shipping_handling_label: Optional[str] = None
    shipping_handling_description: Optional[str] = None


# Webstore-order status lifecycle — used for validated status transitions.
class WebstoreOrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# Statuses at which the webstore owner is owed their payout cut.
# Moving INTO any of these triggers payout_owed += commission_amount (idempotent).
# Moving OUT of these (to cancelled/refunded) triggers the decrement.
PAYOUT_OWED_STATUSES = {WebstoreOrderStatus.COMPLETED.value}


def map_category_to_item_type(category: Optional[str]) -> JobItemType:
    """Map a webstore product category to the nearest job item type.

    Hoisted to module scope so create_webstore_order and create_job_from_order
    share one source of truth.
    """
    category_map = {
        "apparel": JobItemType.OTHER,   # No dedicated apparel type yet
        "signs": JobItemType.BANNER,    # Closest match
        "decals": JobItemType.DECAL,
        "promotional": JobItemType.OTHER,
        "events": JobItemType.OTHER,    # Event tickets / passes / merch — no dedicated type
        "other": JobItemType.OTHER,
    }
    return category_map.get(category or "other", JobItemType.OTHER)


class ProductVariant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    size: Optional[str] = None
    color: Optional[str] = None
    tier: Optional[str] = None  # economy, standard, premium for apparel
    sku: Optional[str] = None
    additional_cost: float = 0
    is_available: bool = True


class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: ProductCategory = ProductCategory.OTHER
    base_cost: Optional[float] = None   # Optional for legacy products created without cost
    retail_price: Optional[float] = None
    # Support up to 3 images
    images: List[str] = []
    image_url: Optional[str] = None  # Legacy field - still support for backwards compat
    has_variants: bool = False
    variants: List[ProductVariant] = []
    is_active: bool = True
    # Product attributes
    size_options: List[str] = []
    color_options: List[str] = []
    is_featured: bool = False
    in_stock: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: ProductCategory = ProductCategory.OTHER
    base_cost: float
    retail_price: float
    images: List[str] = []  # Up to 3 images
    image_url: Optional[str] = None  # Legacy support
    has_variants: bool = False
    variants: List[Dict[str, Any]] = []
    size_options: List[str] = []
    color_options: List[str] = []
    is_featured: bool = False
    in_stock: bool = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    base_cost: Optional[float] = None
    retail_price: Optional[float] = None
    images: Optional[List[str]] = None
    image_url: Optional[str] = None
    has_variants: Optional[bool] = None
    variants: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    size_options: Optional[List[str]] = None
    color_options: Optional[List[str]] = None
    is_featured: Optional[bool] = None
    in_stock: Optional[bool] = None


class WebstoreBranding(BaseModel):
    # Allow the storage_path / content_type metadata fields to flow through
    # so internal handlers see them; response serialization will still emit
    # the public logo_url/banner_url which is what the UI uses.
    model_config = ConfigDict(extra="allow")
    logo_url: Optional[str] = None
    primary_color: str = "#0D9488"
    banner_url: Optional[str] = None


# ── Questionnaire → store-field safe mapping ────────────────────────────────
# Defined at module level so it can be reused by both apply-answers and the
# review-details dry-run endpoint.
# Tuple: (store_field, coerce_fn_or_None)
# locked_settings fields MUST NOT appear here.
def _as_bool_coerce(val):
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("yes", "true", "1", "yes_all", "yes_with_permission")
    return None

def _as_float_coerce(val):
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

QUESTIONNAIRE_SAFE_MAP: dict = {
    "Event Name":                   ("event_name",                   None),
    "Event Date":                   ("event_start_date",             None),
    "Event Location":               ("event_location",               None),
    "When do you want the store to launch?":  ("event_start_date",   None),
    "When should the store close?": ("event_end_date",               None),
    "If pickup is available, what pickup location should be shown?":
                                    ("pickup_delivery_instructions",  None),
    "Pickup date / time instructions":
                                    ("pickup_delivery_instructions",  None),
    "Is this store raising funds for a cause or organization?":
                                    ("fundraiser_enabled",           _as_bool_coerce),
    "Fundraiser Name":              ("fundraiser_name",              None),
    "Fundraiser Description":       ("fundraiser_description",       None),
    "Fundraiser Goal Amount ($)":   ("fundraiser_goal_amount",       _as_float_coerce),
    "Should a fundraiser progress bar be shown on the store?":
                                    ("show_progress_bar",            _as_bool_coerce),
    "Should customers be able to add a donation at checkout?":
                                    ("allow_checkout_donations",     _as_bool_coerce),
    "Donation amount options to offer at checkout":
                                    ("donation_amount_options",      None),
    "Should customers be able to enter a custom donation amount?":
                                    ("allow_custom_donation",        _as_bool_coerce),
    "Should a portion of each product sale be allocated to the fundraiser?":
                                    ("profit_allocation_enabled",    _as_bool_coerce),
    "Profit allocation type":       ("profit_allocation_type",       None),
    "Profit allocation percentage (%)":
                                    ("profit_allocation_percentage", _as_float_coerce),
    "Fixed profit allocation amount per item ($)":
                                    ("fixed_amount_per_item",        _as_float_coerce),
    "Maximum fundraiser cap amount ($)":
                                    ("fundraiser_cap_amount",        _as_float_coerce),
    "Include checkout donations in fundraiser progress total?":
                                    ("include_donations_in_progress", _as_bool_coerce),
    "Include product sale profit allocation in fundraiser progress total?":
                                    ("include_profit_allocation_in_progress", _as_bool_coerce),
    "Show total amount raised publicly on the store?":
                                    ("show_total_raised_publicly",   _as_bool_coerce),
    "Show supporter names on the store?":
                                    ("show_supporter_names",         None),
}


class Webstore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    name: str
    store_type: WebstoreType
    owner_name: str
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    description: Optional[str] = None
    status: WebstoreStatus = WebstoreStatus.PENDING
    is_public: bool = True
    branding: WebstoreBranding = Field(default_factory=WebstoreBranding)
    fundraiser_goal: Optional[float] = None
    fundraiser_start_date: Optional[str] = None
    fundraiser_end_date: Optional[str] = None
    fundraiser_profit_percent: float = 0
    # SEO / Open Graph
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    og_image: Optional[str] = None
    creator_commission_type: str = "percentage"
    creator_commission_value: float = 0
    total_sales: float = 0
    total_orders: int = 0
    total_profit: float = 0
    payout_owed: float = 0
    payout_paid: float = 0
    # Owner Stripe Express account — populated when the owner finishes the
    # magic-link onboarding flow (or the portal flow). When set + charges_enabled,
    # the webstore is allowed to go "active". When orders complete, a Stripe
    # Transfer fires to this account for the owner's commission cut.
    owner_stripe_account_id: Optional[str] = None
    owner_stripe_charges_enabled: bool = False
    owner_stripe_payouts_enabled: bool = False
    owner_stripe_details_submitted: bool = False
    owner_user_id: Optional[str] = None  # set if owner created a portal account
    owner_portal_enabled: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # ── Event-store specific fields ──────────────────────────────────────────
    event_name: Optional[str] = None
    event_type: Optional[str] = None        # one_time | annual | seasonal | recurring
    event_start_date: Optional[str] = None
    event_end_date: Optional[str] = None
    event_location: Optional[str] = None
    order_deadline: Optional[str] = None
    pickup_delivery_date: Optional[str] = None
    pickup_delivery_instructions: Optional[str] = None
    auto_close_after_deadline: bool = False
    allow_late_orders: bool = False
    # ── Event-store fundraiser fields ────────────────────────────────────────
    # These are distinct from the legacy fundraiser_* fields used by
    # store_type=fundraiser stores. They are owned by Event Store setup and
    # are populated primarily through the event_web_store_setup questionnaire.
    fundraiser_enabled: bool = False
    fundraiser_name: Optional[str] = None
    fundraiser_description: Optional[str] = None
    fundraiser_goal_amount: Optional[float] = None  # Optional — no progress bar if None/0
    show_progress_bar: bool = False                  # Only meaningful when goal_amount > 0
    allow_checkout_donations: bool = False
    donation_amount_options: Optional[str] = None   # e.g. "$5, $10, $25"
    allow_custom_donation: bool = False
    profit_allocation_enabled: bool = False
    profit_allocation_type: Optional[str] = None    # percentage | fixed_per_item | manual | na
    profit_allocation_percentage: Optional[float] = None
    fixed_amount_per_item: Optional[float] = None
    fundraiser_cap_amount: Optional[float] = None
    include_donations_in_progress: bool = True
    include_profit_allocation_in_progress: bool = True
    show_total_raised_publicly: bool = False
    show_supporter_names: Optional[str] = None      # yes_with_permission | yes_all | no
    # Running totals — updated as orders arrive
    total_donations: float = 0.0
    total_profit_allocated: float = 0.0
    manual_adjustments: float = 0.0
    total_raised: float = 0.0   # total_donations + total_profit_allocated + manual_adjustments
    # ── Tenant-controlled locked financial settings ──────────────────────────
    # Source of truth for costs/fees/splits. Not editable by store owners.
    locked_settings: LockedSettings = Field(default_factory=LockedSettings)
    # ── SEO slug (read-only after creation) ─────────────────────────────────
    store_slug: Optional[str] = None
    # ── Questionnaire review state ───────────────────────────────────────────
    # Set by the public questionnaire submit endpoint (non-blocking).
    # Staff must review and apply answers before the store can be launched.
    questionnaire_submitted_at: Optional[str] = None
    questionnaire_reviewed: Optional[bool] = None
    questionnaire_reviewed_at: Optional[str] = None


class WebstoreCreate(BaseModel):
    name: str
    store_type: WebstoreType
    owner_name: str
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = True
    branding: Optional[Dict[str, Any]] = None
    fundraiser_goal: Optional[float] = Field(default=None, ge=0)
    fundraiser_start_date: Optional[str] = None
    fundraiser_end_date: Optional[str] = None
    fundraiser_profit_percent: float = Field(default=0, ge=0, le=100)
    creator_commission_type: str = Field(default="percentage", pattern="^(percentage|flat)$")
    creator_commission_value: float = Field(default=0, ge=0)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    og_image: Optional[str] = None
    # Event-store fields
    event_name: Optional[str] = None
    event_type: Optional[str] = None
    event_start_date: Optional[str] = None
    event_end_date: Optional[str] = None
    event_location: Optional[str] = None
    order_deadline: Optional[str] = None
    pickup_delivery_date: Optional[str] = None
    pickup_delivery_instructions: Optional[str] = None
    auto_close_after_deadline: bool = False
    allow_late_orders: bool = False
    # Event-store fundraiser fields
    fundraiser_enabled: bool = False
    fundraiser_name: Optional[str] = None
    fundraiser_description: Optional[str] = None
    fundraiser_goal_amount: Optional[float] = Field(default=None, ge=0)
    show_progress_bar: bool = False
    allow_checkout_donations: bool = False
    donation_amount_options: Optional[str] = None
    allow_custom_donation: bool = False
    profit_allocation_enabled: bool = False
    profit_allocation_type: Optional[str] = None
    profit_allocation_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    fixed_amount_per_item: Optional[float] = Field(default=None, ge=0)
    fundraiser_cap_amount: Optional[float] = Field(default=None, ge=0)
    include_donations_in_progress: bool = True
    include_profit_allocation_in_progress: bool = True
    show_total_raised_publicly: bool = False
    show_supporter_names: Optional[str] = None
    # Tenant-controlled locked settings (admin-only)
    locked_settings: Optional[Dict[str, Any]] = None


class WebstoreUpdate(BaseModel):
    name: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WebstoreStatus] = None
    is_public: Optional[bool] = None
    branding: Optional[Dict[str, Any]] = None
    fundraiser_goal: Optional[float] = Field(default=None, ge=0)
    fundraiser_start_date: Optional[str] = None
    fundraiser_end_date: Optional[str] = None
    fundraiser_profit_percent: Optional[float] = Field(default=None, ge=0, le=100)
    creator_commission_type: Optional[str] = Field(default=None, pattern="^(percentage|flat)$")
    creator_commission_value: Optional[float] = Field(default=None, ge=0)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    og_image: Optional[str] = None
    # Event-store fields
    event_name: Optional[str] = None
    event_type: Optional[str] = None
    event_start_date: Optional[str] = None
    event_end_date: Optional[str] = None
    event_location: Optional[str] = None
    order_deadline: Optional[str] = None
    pickup_delivery_date: Optional[str] = None
    pickup_delivery_instructions: Optional[str] = None
    auto_close_after_deadline: Optional[bool] = None
    allow_late_orders: Optional[bool] = None
    # Event-store fundraiser fields
    fundraiser_enabled: Optional[bool] = None
    fundraiser_name: Optional[str] = None
    fundraiser_description: Optional[str] = None
    fundraiser_goal_amount: Optional[float] = Field(default=None, ge=0)
    show_progress_bar: Optional[bool] = None
    allow_checkout_donations: Optional[bool] = None
    donation_amount_options: Optional[str] = None
    allow_custom_donation: Optional[bool] = None
    profit_allocation_enabled: Optional[bool] = None
    profit_allocation_type: Optional[str] = None
    profit_allocation_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    fixed_amount_per_item: Optional[float] = Field(default=None, ge=0)
    fundraiser_cap_amount: Optional[float] = Field(default=None, ge=0)
    include_donations_in_progress: Optional[bool] = None
    include_profit_allocation_in_progress: Optional[bool] = None
    show_total_raised_publicly: Optional[bool] = None
    show_supporter_names: Optional[str] = None
    # Tenant-controlled locked settings (admin-only)
    locked_settings: Optional[Dict[str, Any]] = None


class WebstoreProduct(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    webstore_id: str
    product_id: str
    is_enabled: bool = True
    price_override: Optional[float] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AddProductToWebstoreRequest(BaseModel):
    """Request body for adding a product to a webstore"""
    product_id: str
    is_enabled: bool = True
    price_override: Optional[float] = Field(default=None, ge=0)


class UpdateWebstoreProductStatusRequest(BaseModel):
    """Body for PUT /webstores/v2/{id}/products/{pid}."""
    is_enabled: bool = True


class UpdateOrderStatusRequest(BaseModel):
    """Body for PUT /webstores/v2/orders/{id}/status."""
    status: WebstoreOrderStatus
    job_id: Optional[str] = None


class RecordPayoutRequest(BaseModel):
    """Body for POST /webstores/v2/{id}/record-payout."""
    amount: float = Field(gt=0)
    notes: Optional[str] = Field(default=None, max_length=500)


class WebstoreOrderItem(BaseModel):
    product_id: str
    product_name: str
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    quantity: int = 1
    unit_price: float
    unit_cost: float
    item_total: float
    item_profit: float


class WebstoreOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    webstore_id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    items: List[WebstoreOrderItem] = []
    subtotal: float = 0
    total_cost: float = 0
    total_profit: float = 0
    commission_amount: float = 0
    # Part 4: Event Store fundraiser amounts captured at checkout.
    donation_amount: float = 0.0
    profit_allocation_amount: float = 0.0
    shipping_handling_amount: float = 0.0
    # Polish: donor opted in to show their name on the public supporters
    # strip. Only meaningful when donation_amount > 0 AND the store has
    # show_supporter_names = "yes_with_permission".
    donor_consent: bool = False
    grand_total: float = 0.0
    # Tracks whether this order's donation/profit-allocation has been rolled
    # into the parent webstore's totals. Used to make webhook + status_check
    # totals idempotent across duplicate Stripe events.
    fundraiser_totals_applied: bool = False
    status: str = "pending"
    job_id: Optional[str] = None
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None
    # Stripe checkout fields (populated by finalize_webstore_stripe_checkout).
    stripe_session_id: Optional[str] = None
    payment_amount: Optional[float] = None
    payment_platform_fee: Optional[float] = None
    payout_recorded_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WebstoreOrderCreate(BaseModel):
    webstore_id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    items: List[Dict[str, Any]]
    notes: Optional[str] = None
    # W17: optional client-supplied key — a resubmit with the same key within
    # the last hour returns the existing order instead of creating a duplicate.
    idempotency_key: Optional[str] = Field(default=None, max_length=128)
    # Part 4: Event Store fundraiser fields — server-validated, server-computed.
    # Set by finalize_webstore_stripe_checkout from the locked Stripe session.
    donation_amount: Optional[float] = Field(default=0.0, ge=0)
    profit_allocation_amount: Optional[float] = Field(default=0.0, ge=0)
    shipping_handling_amount: Optional[float] = Field(default=0.0, ge=0)
    donor_consent: Optional[bool] = False


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_webstore_doc(raw: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    """Normalize legacy/malformed webstore records to avoid list endpoint 500s."""
    now_iso = datetime.now(timezone.utc).isoformat()
    doc = dict(raw or {})

    if not doc.get("id"):
        doc["id"] = str(uuid.uuid4())

    if not doc.get("tenant_id"):
        doc["tenant_id"] = tenant_id

    store_type = str(doc.get("store_type") or "business").lower()
    legacy_type_map = {
        "b2b": "business",
        "corporate": "business",
    }
    store_type = legacy_type_map.get(store_type, store_type)
    if store_type not in {
        WebstoreType.BUSINESS.value, WebstoreType.FUNDRAISER.value,
        WebstoreType.CREATOR.value, WebstoreType.EVENT.value,
    }:
        store_type = WebstoreType.BUSINESS.value
    doc["store_type"] = store_type

    status = str(doc.get("status") or WebstoreStatus.ACTIVE.value).lower()
    if status not in {WebstoreStatus.ACTIVE.value, WebstoreStatus.DISABLED.value, WebstoreStatus.PENDING.value}:
        status = WebstoreStatus.ACTIVE.value
    doc["status"] = status

    if not doc.get("name"):
        doc["name"] = "Untitled Store"
    if not doc.get("owner_name"):
        doc["owner_name"] = "Unknown Owner"

    branding_raw = doc.get("branding")
    if not isinstance(branding_raw, dict):
        branding_raw = {}
    doc["branding"] = {
        "logo_url": branding_raw.get("logo_url") or doc.get("logo_url") or doc.get("logo_image_data"),
        "primary_color": branding_raw.get("primary_color") or "#0D9488",
        "banner_url": branding_raw.get("banner_url") or doc.get("banner_url") or doc.get("banner_image_data"),
    }

    doc["total_sales"] = _coerce_float(doc.get("total_sales"), 0.0)
    doc["total_profit"] = _coerce_float(doc.get("total_profit"), 0.0)
    doc["payout_owed"] = _coerce_float(doc.get("payout_owed"), 0.0)
    doc["payout_paid"] = _coerce_float(doc.get("payout_paid"), 0.0)
    doc["total_orders"] = _coerce_int(doc.get("total_orders"), 0)
    doc["fundraiser_goal"] = _coerce_float(doc.get("fundraiser_goal"), 0.0) if doc.get("fundraiser_goal") is not None else None
    doc["fundraiser_profit_percent"] = _coerce_float(doc.get("fundraiser_profit_percent"), 0.0)

    commission_type = str(doc.get("creator_commission_type") or "percentage").lower()
    if commission_type == "fixed":
        commission_type = "flat"
    if commission_type not in {"percentage", "flat"}:
        commission_type = "percentage"
    doc["creator_commission_type"] = commission_type
    doc["creator_commission_value"] = _coerce_float(doc.get("creator_commission_value"), 0.0)

    doc["is_public"] = bool(doc.get("is_public", True))
    doc["created_at"] = doc.get("created_at") or now_iso
    doc["updated_at"] = doc.get("updated_at") or doc["created_at"]

    # Ensure locked_settings is a dict (never None) so Pydantic can coerce it
    if not isinstance(doc.get("locked_settings"), dict):
        doc["locked_settings"] = {}

    return doc


async def _next_order_number_for_tenant(tenant_id: str) -> str:
    last = await db.orders.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "order_number": 1},
    ).sort("date_created", -1).limit(1).to_list(1)
    if last and last[0].get("order_number"):
        try:
            num = int(last[0]["order_number"].split("-")[-1])
            return f"ORD-{num + 1:04d}"
        except (ValueError, IndexError):
            pass
    count = await db.orders.count_documents({"tenant_id": tenant_id})
    return f"ORD-{count + 1:04d}"


# ── Phase 4 — Customer sync helper ────────────────────────────────────────
#
# Deduplicates a webstore-derived person (owner or buyer) into the global
# customers collection. Email is the primary dedupe key; phone is the
# fallback when no email is present. Tags are always additive — existing
# tags are preserved, the requested tag is added if missing, and the
# returned customer document always has a stable id usable by the rest of
# the pipeline (orders bridge, jobs, etc.).
#
# This function is intentionally light on validation: it trusts that
# caller routes already enforced auth/tenant scoping. Failures fall back
# to a fresh insert so we never block a checkout because of a customer
# write conflict.

import re as _phase4_re


def _normalize_phone(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digits = _phase4_re.sub(r"\D", "", value)
    return digits or None


async def _upsert_webstore_customer(
    *,
    tenant_id: str,
    name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    tag: str,
    company: Optional[str] = None,
) -> Dict[str, Any]:
    """Find-or-create a customer for a webstore actor (owner / buyer)."""
    email_clean = (email or "").strip().lower() or None
    phone_clean = _normalize_phone(phone)
    now_iso = datetime.now(timezone.utc).isoformat()

    existing = None
    if email_clean:
        existing = await db.customers.find_one(
            {"tenant_id": tenant_id, "email": {"$regex": f"^{_phase4_re.escape(email_clean)}$", "$options": "i"}},
            {"_id": 0},
        )
    if not existing and phone_clean:
        # Phone fallback dedupe — compare digits-only so formatting noise
        # does not create duplicates.
        candidates = await db.customers.find(
            {"tenant_id": tenant_id, "phone": {"$ne": None}},
            {"_id": 0, "id": 1, "phone": 1, "email": 1, "name": 1, "company": 1, "tags": 1},
        ).to_list(500)
        for c in candidates:
            if _normalize_phone(c.get("phone")) == phone_clean:
                existing = await db.customers.find_one({"id": c["id"]}, {"_id": 0})
                break

    if existing:
        existing_tags = list(existing.get("tags") or [])
        update_set: Dict[str, Any] = {"updated_at": now_iso}
        # Backfill missing scalar fields without overwriting good data.
        if not existing.get("name") and name:
            update_set["name"] = name
        if not existing.get("email") and email_clean:
            update_set["email"] = email_clean
        if not existing.get("phone") and phone:
            update_set["phone"] = phone
        if not existing.get("company") and company:
            update_set["company"] = company
        # Always add the tag if missing.
        new_tags = existing_tags + [tag] if tag and tag not in existing_tags else existing_tags
        update_set["tags"] = new_tags
        await db.customers.update_one({"id": existing["id"]}, {"$set": update_set})
        existing.update(update_set)
        return existing

    # No match — create a new customer.
    from models import Customer
    customer = Customer(
        name=name or "Webstore Contact",
        email=email_clean,
        phone=phone,
        company=company,
        tenant_id=tenant_id,
        tags=[tag] if tag else [],
    )
    doc = customer.model_dump()
    await db.customers.insert_one(doc)
    doc.pop("_id", None)
    return doc


# ── Phase 4 — Questionnaire template dispatcher by store type ─────────────
#
# Map a webstore's `store_type` (with backward-compatible aliases) to the
# correct questionnaire template key in QUESTIONNAIRE_TEMPLATES. Unknown
# values fall back to the business template so the send-questionnaire
# endpoint never 500s on legacy data.

QUESTIONNAIRE_TEMPLATE_BY_STORE_TYPE = {
    "event":        "event_web_store_setup",
    "fundraiser":   "fundraiser_web_store_setup",
    "team_school":  "team_school_web_store_setup",
    "team":         "team_school_web_store_setup",
    "school":       "team_school_web_store_setup",
    "creator":      "team_school_web_store_setup",
    "business":     "business_web_store_setup",
    "b2b":          "business_web_store_setup",
    "company":      "business_web_store_setup",
}


def _template_key_for_store_type(store_type: Optional[str]) -> str:
    key = (store_type or "").strip().lower()
    return QUESTIONNAIRE_TEMPLATE_BY_STORE_TYPE.get(key, "business_web_store_setup")




async def _ensure_main_order_bridge(
    *,
    webstore_order_doc: Dict[str, Any],
    webstore_doc: Dict[str, Any],
    customer_doc: Dict[str, Any],
    tenant_id: str,
    job_id: str,
) -> str:
    """Ensure a webstore checkout appears in the main Orders list."""
    existing = await db.orders.find_one(
        {"tenant_id": tenant_id, "webstore_order_id": webstore_order_doc["id"]},
        {"_id": 0, "id": 1},
    )
    if existing:
        return existing["id"]

    now_iso = datetime.now(timezone.utc).isoformat()
    order_number = await _next_order_number_for_tenant(tenant_id)
    customer_name = webstore_order_doc.get("customer_name") or customer_doc.get("name") or "Webstore Customer"
    company_name = (
        customer_doc.get("company")
        or customer_doc.get("display_name")
        or webstore_doc.get("name")
        or ""
    )

    order_id = str(uuid.uuid4())
    order_doc = {
        "id": order_id,
        "order_number": order_number,
        "name": f"WEBSTORE-{order_number}",
        "tenant_id": tenant_id,
        "customer_id": customer_doc.get("id", ""),
        "customer_name": customer_name,
        "contact_name": customer_name,
        "phone": webstore_order_doc.get("customer_phone") or customer_doc.get("phone") or "",
        "email": webstore_order_doc.get("customer_email") or customer_doc.get("email") or "",
        "company_name": company_name,
        "order_source": "website",
        # Phase 4 — explicit machine-friendly source marker used by the
        # main Orders list filter (GET /api/orders?source=webstore). Coexists
        # with the legacy human-readable `order_source` field.
        "source": "webstore",
        "date_created": now_iso,
        "created_by": "webstore_checkout",
        "requested_due_date": None,
        "event_date": None,
        "status": "approved",
        "payment_status": "paid",
        "approval_status": "approved",
        "pickup_delivery_method": "ship",
        "pickup_delivery_notes": webstore_order_doc.get("shipping_address") or "",
        "internal_notes": (
            f"Auto-created from webstore checkout. "
            f"Store: {webstore_doc.get('name', 'Unknown')}"
        ),
        "customer_notes": webstore_order_doc.get("notes") or "",
        "linked_quote_ids": [],
        "linked_invoice_ids": [],
        "job_ticket_count": len(webstore_order_doc.get("items") or []),
        "overall_progress": 0.0,
        "final_completion_date": None,
        "is_archived": False,
        "is_active": True,
        "order_title": f"Webstore - {webstore_doc.get('name', 'Store')}",
        "shared_production_notes": "",
        "shared_design_notes": "",
        "shared_install_notes": "",
        "shared_color_brand_notes": "",
        "shared_reference_links": [],
        "default_item_category": None,
        "shared_artwork_default_mode": "ask",
        "updated_at": now_iso,
        "order_total": float(webstore_order_doc.get("total", 0) or 0),
        # Marker fields for UI + traceability
        "is_webstore_order": True,
        "webstore_order_id": webstore_order_doc.get("id"),
        "webstore_id": webstore_doc.get("id"),
        "webstore_name": webstore_doc.get("name"),
        "webstore_job_id": job_id,
        "stripe_session_id": webstore_order_doc.get("stripe_session_id"),
    }

    await db.orders.insert_one(order_doc)
    await db.jobs.update_one(
        {"id": job_id, "tenant_id": tenant_id},
        {"$set": {"order_id": order_id, "updated_at": now_iso}},
    )
    return order_id


# ============== SLUG HELPER ==============

import re as _re

async def _generate_unique_slug(name: str, tenant_id: str) -> str:
    """Generate a unique URL-safe slug from a store name.

    Slugs are stored for future slug-based routing. They do not break the
    existing /store/{storeId} route.  Duplicate names within a tenant get
    a numeric suffix: johnson-benefit-dinner-2026-2, -3, etc.
    """
    base = _re.sub(r"[^a-z0-9\s-]", "", name.lower())
    base = _re.sub(r"[\s_]+", "-", base).strip("-")[:60] or "store"
    slug = base
    counter = 1
    while await db.webstores_v2.find_one(
        {"tenant_id": tenant_id, "store_slug": slug},
        {"_id": 0, "id": 1},
    ):
        slug = f"{base}-{counter}"
        counter += 1
    return slug


# ============== ROUTERS ==============

products_router = APIRouter(prefix="/products", tags=["Products"])
webstores_router = APIRouter(prefix="/webstores/v2", tags=["Webstores"])
# Public storefront router - no authentication required
storefront_router = APIRouter(prefix="/storefront", tags=["Storefront (Public)"])


# ============== PUBLIC STOREFRONT ROUTES (No Auth) ==============

# Safe fields to expose publicly for webstores
WEBSTORE_PUBLIC_FIELDS = [
    "id", "name", "store_type", "owner_name", "description",
    "status", "is_public", "branding",
    # Legacy fundraiser-type fields (store_type=fundraiser stores)
    "fundraiser_goal", "fundraiser_start_date", "fundraiser_end_date",
    "total_sales", "total_orders",
    "seo_title", "seo_description", "og_image",
    "checkout_enabled", "checkout_status", "checkout_message",
    # Event-store fields (non-financial)
    "event_name", "event_type", "event_start_date", "event_end_date",
    "event_location", "order_deadline", "pickup_delivery_date",
    "pickup_delivery_instructions",
    # Event-store fundraiser public fields
    "fundraiser_enabled", "fundraiser_name", "fundraiser_description",
    "fundraiser_goal_amount", "show_progress_bar",
    "show_total_raised_publicly", "show_supporter_names",
    "total_donations", "total_profit_allocated", "total_raised",
    # Donation/checkout fields (used by Storefront donation UI)
    "allow_checkout_donations", "donation_amount_options",
    "allow_custom_donation",
    # Slug for future URL routing
    "store_slug",
]


def _parse_donation_presets(raw: Optional[str]) -> List[float]:
    """Parse a comma/space/dollar-sign separated string of donation presets.

    Accepts values like "$5, $10, $25" or "5 10 25" → [5.0, 10.0, 25.0].
    Filters non-numeric/negative entries. Returns at most 8 presets to keep
    the UI sane.
    """
    if not raw:
        return []
    import re as _re_d
    tokens = _re_d.split(r"[\s,;|]+", str(raw))
    out: List[float] = []
    for tok in tokens:
        cleaned = tok.replace("$", "").replace(",", "").strip()
        if not cleaned:
            continue
        try:
            val = float(cleaned)
        except ValueError:
            continue
        if val > 0 and val not in out:
            out.append(val)
        if len(out) >= 8:
            break
    return out


def _public_locked_settings(locked: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Strip locked_settings down to ONLY the fields safe to expose publicly.

    Public fields: shipping_fee, handling_fee, plus the shipping+handling
    bundle (label/description/fee/enabled). Internal cost/profit/split fields
    are NEVER exposed.
    """
    if not isinstance(locked, dict):
        return {}
    return {
        "shipping_fee": locked.get("shipping_fee"),
        "handling_fee": locked.get("handling_fee"),
        "shipping_handling_enabled": bool(locked.get("shipping_handling_enabled")),
        "shipping_handling_fee": locked.get("shipping_handling_fee"),
        "shipping_handling_label": locked.get("shipping_handling_label"),
        "shipping_handling_description": locked.get("shipping_handling_description"),
    }


def _compute_shipping_handling_total(locked: Optional[Dict[str, Any]]) -> float:
    """Return the per-order shipping+handling fee from locked_settings.

    Honors the shipping_handling_enabled bundle when set; otherwise sums
    the individual shipping_fee and handling_fee fields. Always pulled from
    locked_settings — never from the frontend.
    """
    if not isinstance(locked, dict):
        return 0.0
    if locked.get("shipping_handling_enabled"):
        return round(float(locked.get("shipping_handling_fee") or 0), 2)
    ship = float(locked.get("shipping_fee") or 0)
    hand = float(locked.get("handling_fee") or 0)
    return round(ship + hand, 2)


def compute_event_profit_allocation(
    webstore: Dict[str, Any],
    order_items: List[Any],
    total_profit: float,
) -> float:
    """Compute the fundraiser profit-allocation amount for an Event Store order.

    Honors the store's profit_allocation_type setting:
      - "percentage": % of total_profit (profit_allocation_percentage)
      - "fixed_per_item": fixed_amount_per_item × total quantity
      - "manual" / "na" / unknown: 0 (handled out-of-band by the shop owner)

    Returns 0 if profit_allocation_enabled is false. Always non-negative,
    rounded to 2 decimals. Caps the result at fundraiser_cap_amount (minus
    what's already been allocated) when the cap is set.
    """
    if not webstore.get("profit_allocation_enabled"):
        return 0.0

    alloc_type = (webstore.get("profit_allocation_type") or "").lower()
    raw_amount = 0.0

    if alloc_type == "percentage":
        pct = float(webstore.get("profit_allocation_percentage") or 0)
        if pct > 0 and total_profit > 0:
            raw_amount = total_profit * (pct / 100.0)
    elif alloc_type == "fixed_per_item":
        per_item = float(webstore.get("fixed_amount_per_item") or 0)
        if per_item > 0:
            qty = sum(int(getattr(i, "quantity", 0) or 0) for i in order_items)
            raw_amount = per_item * qty
    # "manual" / "na" / other: 0 — store owner records adjustments manually.

    if raw_amount <= 0:
        return 0.0

    # Apply optional cap.
    cap = webstore.get("fundraiser_cap_amount")
    if cap is not None and float(cap) > 0:
        already_allocated = float(webstore.get("total_profit_allocated") or 0)
        remaining = max(float(cap) - already_allocated, 0.0)
        raw_amount = min(raw_amount, remaining)

    return round(max(raw_amount, 0.0), 2)


async def _apply_fundraiser_totals(
    order_id: str,
    webstore_id: str,
    donation_amount: float,
    profit_allocation_amount: float,
) -> bool:
    """Idempotently add donation + profit-allocation to the webstore totals.

    Uses a conditional update on the order's `fundraiser_totals_applied`
    flag so duplicate webhook deliveries (or success-URL retries) cannot
    double-count toward total_raised.

    Returns True when the increment was applied (first time), False otherwise.
    """
    donation_amount = round(float(donation_amount or 0), 2)
    profit_allocation_amount = round(float(profit_allocation_amount or 0), 2)
    if donation_amount <= 0 and profit_allocation_amount <= 0:
        return False

    # Conditional flip: only increment if this order hasn't been counted yet.
    res = await db.webstore_orders_v2.update_one(
        {"id": order_id, "fundraiser_totals_applied": {"$ne": True}},
        {"$set": {"fundraiser_totals_applied": True,
                  "fundraiser_totals_applied_at": datetime.now(timezone.utc).isoformat()}},
    )
    if res.modified_count == 0:
        return False

    total_added = round(donation_amount + profit_allocation_amount, 2)
    await db.webstores_v2.update_one(
        {"id": webstore_id},
        {"$inc": {
            "total_donations": donation_amount,
            "total_profit_allocated": profit_allocation_amount,
            "total_raised": total_added,
        }}
    )
    return True

def sanitize_webstore_for_public(webstore: dict) -> dict:
    """Return only safe fields for public consumption"""
    safe = {k: webstore.get(k) for k in WEBSTORE_PUBLIC_FIELDS if k in webstore}

    # Expose donation presets as a parsed list (the raw string stays too).
    safe["donation_presets"] = _parse_donation_presets(webstore.get("donation_amount_options"))

    # Expose only the public subset of locked_settings (shipping/handling).
    safe["locked_settings"] = _public_locked_settings(webstore.get("locked_settings"))

    # Backward compatibility: older docs may store banner/logo on top-level
    # keys (banner_url/logo_url or *_image_data) instead of branding.
    branding_raw = safe.get("branding")
    if not isinstance(branding_raw, dict):
        branding_raw = {}
    safe["branding"] = {
        "logo_url": branding_raw.get("logo_url") or webstore.get("logo_url") or webstore.get("logo_image_data"),
        "primary_color": branding_raw.get("primary_color") or "#0D9488",
        "banner_url": branding_raw.get("banner_url") or webstore.get("banner_url") or webstore.get("banner_image_data"),
    }
    return safe


# ---- Audit trail helper -----------------------------------------------

async def _log_stage_event(
    webstore_id: str,
    tenant_id: str,
    event_type: str,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """Insert one row into the additive `webstore_stage_events` audit collection.

    Failures are swallowed so that audit logging never blocks a business
    operation.
    """
    try:
        doc = {
            "id": str(__import__("uuid").uuid4()),
            "webstore_id": webstore_id,
            "tenant_id": tenant_id,
            "event_type": event_type,
            "actor_id": actor_id,
            "actor_email": actor_email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            doc.update(extra)
        await db.webstore_stage_events.insert_one(doc)
    except Exception as _exc:  # noqa: BLE001
        logger.warning(f"webstore_stage_events insert failed (non-fatal): {_exc}")


@storefront_router.get("/{webstore_id}/asset/{kind}")
async def get_public_webstore_asset(webstore_id: str, kind: str):
    """Public fetch for a webstore logo/banner (W12).

    Streams the bytes from object storage with long cache-control headers.
    Returns 404 if the webstore has not uploaded the requested asset.
    """
    if kind not in ("logo", "banner"):
        raise HTTPException(status_code=404, detail="Unknown asset")

    webstore = await db.webstores_v2.find_one({"id": webstore_id}, {"_id": 0, "branding": 1, "is_public": 1})
    if not webstore or not webstore.get("is_public", True):
        raise HTTPException(status_code=404, detail="Webstore not found")

    branding = webstore.get("branding") or {}
    storage_path = branding.get(f"{kind}_storage_path")
    if not storage_path:
        raise HTTPException(status_code=404, detail=f"No {kind} set")

    try:
        data, content_type = get_object(storage_path)
    except Exception:
        # Don't expose storage errors to the public; just 404.
        raise HTTPException(status_code=404, detail=f"{kind.capitalize()} unavailable")

    return Response(
        content=data,
        media_type=branding.get(f"{kind}_content_type") or content_type or "application/octet-stream",
        headers={"Cache-Control": "public, max-age=300"},
    )


@storefront_router.get("/{webstore_id}")
async def get_public_store(webstore_id: str):
    """
    Get a public webstore details (no auth required).
    Returns only safe/public fields - never exposes tenant_id, payout info, etc.
    """
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id}, 
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Only return if store is public
    if not webstore.get("is_public", True):
        raise HTTPException(status_code=404, detail="Store not found")

    # For non-active stores return a limited "status page" payload so the
    # frontend can render a branded Coming-Soon / Closed / Unavailable screen
    # without exposing any internal data.
    if webstore.get("status") != "active":
        branding_raw = webstore.get("branding") or {}
        return {
            "id": webstore.get("id"),
            "name": webstore.get("name"),
            "store_type": webstore.get("store_type"),
            "status": webstore.get("status"),
            "description": webstore.get("description"),
            "order_deadline": webstore.get("order_deadline"),
            "pickup_delivery_date": webstore.get("pickup_delivery_date"),
            "pickup_delivery_instructions": webstore.get("pickup_delivery_instructions"),
            "event_name": webstore.get("event_name"),
            "branding": {
                "logo_url": (branding_raw.get("logo_url")
                             or webstore.get("logo_url")
                             or webstore.get("logo_image_data")),
                "primary_color": branding_raw.get("primary_color") or "#0D9488",
                "banner_url": (branding_raw.get("banner_url")
                               or webstore.get("banner_url")
                               or webstore.get("banner_image_data")),
            },
            "_status_page": True,
        }

    public_webstore = sanitize_webstore_for_public(webstore)
    tenant = await db.tenants.find_one({"id": webstore.get("tenant_id")}, {"_id": 0})
    checkout = _get_stripe_checkout_status(tenant.get("stripe_connect_account_id") if tenant else None)
    public_webstore["checkout_enabled"] = checkout["enabled"]
    public_webstore["checkout_status"] = checkout["status"]
    public_webstore["checkout_message"] = checkout["message"]
    return public_webstore


@storefront_router.get("/{webstore_id}/preview")
async def get_public_store_preview(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Admin preview of a webstore regardless of its live status.

    Requires a valid admin JWT so non-staff cannot bypass the status check.
    Returns the same sanitized public payload as the live endpoint PLUS an
    `is_admin_preview: true` flag so the frontend can render a preview banner.
    Also logs an `admin_preview_accessed` stage event.
    """
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    public_webstore = sanitize_webstore_for_public(webstore)
    tenant = await db.tenants.find_one({"id": webstore.get("tenant_id")}, {"_id": 0})
    checkout = _get_stripe_checkout_status(tenant.get("stripe_connect_account_id") if tenant else None)
    public_webstore["checkout_enabled"] = checkout["enabled"]
    public_webstore["checkout_status"] = checkout["status"]
    public_webstore["checkout_message"] = checkout["message"]
    public_webstore["is_admin_preview"] = True

    await _log_stage_event(
        webstore_id=webstore_id,
        tenant_id=current_user.tenant_id,
        event_type="admin_preview_accessed",
        actor_id=current_user.id,
        actor_email=current_user.email,
    )
    return public_webstore


@storefront_router.get("/{webstore_id}/supporters")
async def get_public_store_supporters(webstore_id: str, limit: int = 5):
    """Public Top Donors / Recent Supporters strip.

    Returns the most recent N supporters (donation_amount > 0) for an Event
    Store fundraiser. Honors `show_supporter_names`:
      - "no"                 → endpoint returns []  (UI hides the strip)
      - "yes_with_permission"→ shows name only when donor opted in
                               (`donor_consent=True` on the order doc); others
                               fall back to "Anonymous Supporter"
      - "yes_all"            → shows names whenever available
    Never exposes email, phone, payment metadata, or session ids.
    """
    if limit <= 0 or limit > 10:
        limit = 5

    ws = await db.webstores_v2.find_one(
        {"id": webstore_id},
        {"_id": 0, "store_type": 1, "fundraiser_enabled": 1,
         "show_supporter_names": 1, "is_public": 1, "status": 1},
    )
    if not ws or not ws.get("is_public", True) or ws.get("status") != "active":
        raise HTTPException(status_code=404, detail="Store not found")

    # Only Event Stores with fundraiser_enabled expose supporters.
    if ws.get("store_type") != "event" or not ws.get("fundraiser_enabled"):
        return []

    show_mode = (ws.get("show_supporter_names") or "no").lower()
    if show_mode == "no":
        return []

    orders = await db.webstore_orders_v2.find(
        {
            "webstore_id": webstore_id,
            "donation_amount": {"$gt": 0},
            "status": {"$nin": ["cancelled", "refunded"]},
        },
        {
            "_id": 0,
            "id": 1, "customer_name": 1, "donation_amount": 1,
            "donor_consent": 1, "created_at": 1,
        },
    ).sort("created_at", -1).limit(limit).to_list(limit)

    out = []
    for o in orders:
        donation = round(float(o.get("donation_amount") or 0), 2)
        if donation <= 0:
            continue
        if show_mode == "yes_with_permission":
            allow_name = bool(o.get("donor_consent"))
        else:  # yes_all
            allow_name = True
        raw_name = (o.get("customer_name") or "").strip()
        display_name = raw_name if (allow_name and raw_name) else "Anonymous Supporter"
        out.append({
            "name": display_name,
            "amount": donation,
            "created_at": o.get("created_at"),
        })
    return out


@storefront_router.get("/{webstore_id}/products")
async def get_public_store_products(webstore_id: str, admin_preview: bool = False):
    """
    Get products for a public webstore (no auth required).
    Ensures products belong to the same tenant as the webstore.
    Pass ?admin_preview=true to bypass the active-status gate (used by admin preview).
    """
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id}, 
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Only return if store is public
    if not webstore.get("is_public", True):
        raise HTTPException(status_code=404, detail="Store not found")
    
    if not admin_preview and webstore.get("status") != "active":
        raise HTTPException(status_code=404, detail="Store is not currently available")
    
    tenant_id = webstore.get("tenant_id")
    
    # Get all enabled product assignments for this webstore
    assignments = await db.webstore_products.find(
        {"webstore_id": webstore_id, "is_enabled": True}, 
        {"_id": 0}
    ).to_list(500)

    # W10: batch-fetch all products in a single $in query instead of one-per-assignment.
    product_ids = [a["product_id"] for a in assignments]
    if not product_ids:
        return []
    products_cursor = db.products.find(
        {"id": {"$in": product_ids}, "tenant_id": tenant_id},
        {"_id": 0},
    )
    products_by_id = {p["id"]: p async for p in products_cursor}

    # Enrich, preserving the assignment order from above.
    results = []
    for a in assignments:
        product = products_by_id.get(a["product_id"])
        if not product or not product.get("is_active", True):
            continue
        # Structure for storefront consumption - exclude sensitive fields
        enriched = {
            "product_id": product["id"],
            "product": {
                "id": product["id"],
                "name": product["name"],
                "description": product.get("description"),
                "category": product.get("category"),
                "retail_price": product.get("retail_price"),
                "images": product.get("images", []),
                "image_url": product.get("image_url"),
                "has_variants": product.get("has_variants", False),
                "variants": [
                    {
                        "id": v.get("id"),
                        "name": v.get("name"),
                        "size": v.get("size"),
                        "color": v.get("color"),
                        "additional_cost": v.get("additional_cost", 0),
                        "is_available": v.get("is_available", True)
                    }
                    for v in product.get("variants", [])
                    if v.get("is_available", True)
                ]
            },
            "price_override": a.get("price_override"),
            "effective_price": a.get("price_override") or product["retail_price"]
        }
        results.append(enriched)

    return results


# ============== PRODUCT ROUTES ==============

@products_router.post("", response_model=Product)
async def create_product(
    input: ProductCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new product in the master catalog"""
    _require_permission(current_user, Permission.PRODUCTS_CREATE)
    variants = []
    if input.has_variants and input.variants:
        for v in input.variants:
            variant = ProductVariant(
                name=v.get("name", ""),
                size=v.get("size"),
                color=v.get("color"),
                tier=v.get("tier"),  # Support apparel tier
                sku=v.get("sku"),
                additional_cost=v.get("additional_cost", 0),
                is_available=v.get("is_available", True)
            )
            variants.append(variant.model_dump())
    
    # Handle images - limit to 3
    images = input.images[:3] if input.images else []
    # Legacy support: if image_url is set but images is empty, use image_url
    if input.image_url and not images:
        images = [input.image_url]
    
    product = Product(
        tenant_id=current_user.tenant_id,
        name=input.name,
        description=input.description,
        category=input.category,
        base_cost=input.base_cost,
        retail_price=input.retail_price,
        images=images,
        image_url=images[0] if images else None,  # Keep legacy field populated
        has_variants=input.has_variants,
        variants=variants,
        size_options=input.size_options,
        color_options=input.color_options,
        is_featured=input.is_featured,
        in_stock=input.in_stock,
    )
    doc = product.model_dump()
    await db.products.insert_one(doc)
    return product


@products_router.get("/defaults/apparel-options")
async def get_apparel_defaults():
    """Get default apparel tier options and sizes"""
    return {
        "tiers": APPAREL_TIER_DEFAULTS,
        "apparel_sizes": APPAREL_SIZES,
        "decal_sizes": DECAL_SIZES
    }


@products_router.get("", response_model=List[Product])
async def get_products(
    category: Optional[ProductCategory] = None,
    is_active: Optional[bool] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all products in the master catalog"""
    query = {"tenant_id": current_user.tenant_id}
    if category:
        query["category"] = category.value
    if is_active is not None:
        query["is_active"] = is_active
    products = await db.products.find(query, {"_id": 0}).to_list(500)
    return products


@products_router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific product"""
    product = await db.products.find_one(
        {"id": product_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@products_router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: str, 
    input: ProductUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a product"""
    _require_permission(current_user, Permission.PRODUCTS_MANAGE)
    # First verify the product belongs to this tenant
    existing = await db.products.find_one(
        {"id": product_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    # Handle images - limit to 3 and maintain consistency with image_url
    if "images" in update_data:
        images = update_data["images"][:3] if update_data["images"] else []
        update_data["images"] = images
        # Keep legacy image_url field in sync
        update_data["image_url"] = images[0] if images else None
    elif "image_url" in update_data and update_data["image_url"]:
        # If only image_url is provided, add it to images array
        if not update_data.get("images"):
            update_data["images"] = [update_data["image_url"]]
    
    if "variants" in update_data and update_data["variants"]:
        variants = []
        for v in update_data["variants"]:
            if "id" not in v:
                v["id"] = str(uuid.uuid4())
            variants.append(v)
        update_data["variants"] = variants
    
    if update_data:
        # Always set updated_at on product update
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.products.update_one(
            {"id": product_id, "tenant_id": current_user.tenant_id}, 
            {"$set": update_data}
        )
    product = await db.products.find_one(
        {"id": product_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    return product


@products_router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a product"""
    _require_permission(current_user, Permission.PRODUCTS_MANAGE)
    result = await db.products.delete_one(
        {"id": product_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    # Also remove from all webstore assignments
    await db.webstore_products.delete_many({"product_id": product_id})
    return {"message": "Product deleted"}


# ============== WEBSTORE ROUTES ==============

@webstores_router.post("", response_model=Webstore)
async def create_webstore(
    input: WebstoreCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new webstore"""
    _require_permission(current_user, Permission.WEBSTORES_CREATE)
    # Enforce unique name per tenant
    existing = await db.webstores_v2.find_one(
        {"tenant_id": current_user.tenant_id, "name": input.name},
        {"_id": 0, "id": 1}
    )
    if existing:
        raise HTTPException(status_code=409, detail="A webstore with this name already exists.")
    branding = WebstoreBranding(**(input.branding or {}))
    store_slug = await _generate_unique_slug(input.name, current_user.tenant_id)
    webstore = Webstore(
        tenant_id=current_user.tenant_id,
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
        creator_commission_value=input.creator_commission_value,
        seo_title=input.seo_title,
        seo_description=input.seo_description,
        og_image=input.og_image,
        # Event-store fields
        event_name=input.event_name,
        event_type=input.event_type,
        event_start_date=input.event_start_date,
        event_end_date=input.event_end_date,
        event_location=input.event_location,
        order_deadline=input.order_deadline,
        pickup_delivery_date=input.pickup_delivery_date,
        pickup_delivery_instructions=input.pickup_delivery_instructions,
        auto_close_after_deadline=input.auto_close_after_deadline,
        allow_late_orders=input.allow_late_orders,
        # Event-store fundraiser fields
        fundraiser_enabled=input.fundraiser_enabled,
        fundraiser_name=input.fundraiser_name,
        fundraiser_description=input.fundraiser_description,
        fundraiser_goal_amount=input.fundraiser_goal_amount,
        show_progress_bar=input.show_progress_bar,
        allow_checkout_donations=input.allow_checkout_donations,
        donation_amount_options=input.donation_amount_options,
        allow_custom_donation=input.allow_custom_donation,
        profit_allocation_enabled=input.profit_allocation_enabled,
        profit_allocation_type=input.profit_allocation_type,
        profit_allocation_percentage=input.profit_allocation_percentage,
        fixed_amount_per_item=input.fixed_amount_per_item,
        fundraiser_cap_amount=input.fundraiser_cap_amount,
        include_donations_in_progress=input.include_donations_in_progress,
        include_profit_allocation_in_progress=input.include_profit_allocation_in_progress,
        show_total_raised_publicly=input.show_total_raised_publicly,
        show_supporter_names=input.show_supporter_names,
        # Tenant-controlled locked settings
        locked_settings=LockedSettings(**(input.locked_settings or {})),
        # URL slug
        store_slug=store_slug,
    )
    doc = webstore.model_dump()
    await db.webstores_v2.insert_one(doc)

    # Phase 4 — sync the store owner into Customers with webstore_owner tag.
    # Non-fatal: a failure here must not block store creation.
    try:
        if webstore.owner_email or webstore.owner_name:
            await _upsert_webstore_customer(
                tenant_id=current_user.tenant_id,
                name=webstore.owner_name,
                email=webstore.owner_email,
                phone=webstore.owner_phone,
                tag="webstore_owner",
                company=webstore.name,
            )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Owner customer sync failed for store %s: %s", webstore.id, exc)

    return webstore


@webstores_router.get("", response_model=List[Webstore])
async def get_webstores(
    store_type: Optional[WebstoreType] = None,
    status: Optional[WebstoreStatus] = None,
    is_public: Optional[bool] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all webstores"""
    query = {"tenant_id": current_user.tenant_id}
    if store_type:
        query["store_type"] = store_type.value
    if status:
        query["status"] = status.value
    if is_public is not None:
        query["is_public"] = is_public
    raw_webstores = await db.webstores_v2.find(query, {"_id": 0}).to_list(500)

    sanitized: List[Dict[str, Any]] = []
    skipped = 0
    for raw in raw_webstores:
        try:
            normalized = _normalize_webstore_doc(raw, current_user.tenant_id)
            sanitized.append(Webstore(**normalized).model_dump())
        except Exception as exc:
            skipped += 1
            logger.warning(
                f"Skipping invalid webstore record id={raw.get('id')} tenant={current_user.tenant_id}: {exc}"
            )

    if skipped:
        logger.warning(
            f"get_webstores sanitized response for tenant={current_user.tenant_id}; skipped_invalid={skipped}"
        )

    return sanitized


# ============== WEBSTORE ORDERS (defined early to prevent route conflict) ==============

@webstores_router.get("/orders", response_model=List[WebstoreOrder])
async def get_webstore_orders(
    webstore_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List webstore orders for this tenant's webstores"""
    # Get all webstores for this tenant
    tenant_webstores = await db.webstores_v2.find(
        {"tenant_id": current_user.tenant_id},
        {"id": 1, "_id": 0}
    ).to_list(500)
    webstore_ids = [w["id"] for w in tenant_webstores]
    
    if not webstore_ids:
        return []
    
    query = {"webstore_id": {"$in": webstore_ids}}
    if webstore_id:
        # If specific webstore requested, verify it belongs to tenant
        if webstore_id not in webstore_ids:
            raise HTTPException(status_code=404, detail="Webstore not found")
        query["webstore_id"] = webstore_id
    if status:
        query["status"] = status
    
    orders = await db.webstore_orders_v2.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return orders


@webstores_router.get("/orders/{order_id}", response_model=WebstoreOrder)
async def get_webstore_order(
    order_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific order"""
    order = await db.webstore_orders_v2.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify access by checking if webstore belongs to tenant
    webstore = await db.webstores_v2.find_one(
        {"id": order["webstore_id"], "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


async def _maybe_auto_transfer_owner_commission(
    *,
    order: dict,
    tenant_id: str,
    commission: float,
    update_set: Dict[str, Any],
) -> None:
    """If the webstore has a connected owner Stripe Express account, fire a
    Stripe Transfer for the owner's commission. Idempotent via
    ``order.owner_transfer_id``.

    Sets ``update_set['owner_transfer_id']`` and ``update_set['owner_transfer_amount']``
    so the caller persists them on the order.
    """
    if order.get("owner_transfer_id"):
        return  # already transferred

    webstore = await db.webstores_v2.find_one(
        {"id": order["webstore_id"], "tenant_id": tenant_id},
        {
            "_id": 0,
            "owner_stripe_account_id": 1,
            "owner_stripe_charges_enabled": 1,
        },
    )
    if not webstore:
        return
    owner_acct = webstore.get("owner_stripe_account_id")
    if not owner_acct or not webstore.get("owner_stripe_charges_enabled"):
        return  # no auto-transfer; falls back to manual payout flow

    # Lazy import to avoid module-load circularity
    import stripe as _stripe
    import os as _os
    _stripe.api_key = _os.environ.get("STRIPE_SECRET_KEY") or _os.environ.get("STRIPE_API_KEY")

    amount_cents = int(round(commission * 100))
    if amount_cents <= 0:
        return

    # Use a deterministic idempotency key so duplicate webhook deliveries don't
    # double-pay the owner.
    idem_key = f"order_{order['id']}_owner_commission"

    transfer = _stripe.Transfer.create(
        amount=amount_cents,
        currency="usd",
        destination=owner_acct,
        transfer_group=f"order_{order['id']}",
        metadata={
            "signguy_order_id": order["id"],
            "signguy_webstore_id": order["webstore_id"],
            "signguy_tenant_id": tenant_id,
            "commission_amount": str(commission),
        },
        idempotency_key=idem_key,
    )

    update_set["owner_transfer_id"] = transfer.id
    update_set["owner_transfer_amount"] = commission
    update_set["owner_transfer_at"] = datetime.now(timezone.utc).isoformat()

    # Decrement payout_owed since the owner has now been paid automatically.
    await db.webstores_v2.update_one(
        {"id": order["webstore_id"], "tenant_id": tenant_id},
        {
            "$inc": {"payout_owed": -commission, "payout_paid": commission},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )


async def _apply_order_status_transition(
    order: dict,
    new_status: str,
    tenant_id: str,
    job_id: Optional[str] = None,
) -> dict:
    """Internal: apply a webstore-order status transition + payout-book
    side effects. Idempotent via `payout_recorded_at`. Safe to call from
    both the HTTP endpoint and internal flows (e.g. Stripe webhook).
    Returns an update-set dict that was applied.
    """
    now = datetime.now(timezone.utc).isoformat()
    commission = float(order.get("commission_amount") or 0)
    payout_recorded = bool(order.get("payout_recorded_at"))
    update_set: Dict[str, Any] = {"status": new_status, "updated_at": now}
    if job_id is not None:
        update_set["job_id"] = job_id

    # Transitioning INTO a payout-eligible status — credit once.
    if new_status in PAYOUT_OWED_STATUSES and not payout_recorded and commission > 0:
        await db.webstores_v2.update_one(
            {"id": order["webstore_id"], "tenant_id": tenant_id},
            {"$inc": {"payout_owed": commission}, "$set": {"updated_at": now}},
        )
        update_set["payout_recorded_at"] = now

        # NEW: If the webstore's owner has connected their Stripe Express
        # account, fire an automatic Transfer for the owner's commission cut.
        # Falls back to the manual payout flow (payout_owed) if owner not
        # connected. Idempotent — checks order.owner_transfer_id first.
        try:
            await _maybe_auto_transfer_owner_commission(
                order=order,
                tenant_id=tenant_id,
                commission=commission,
                update_set=update_set,
            )
        except Exception as exc:  # noqa: BLE001
            # Never block the order transition on a transfer failure — it'll
            # surface as a retryable item in the operator dashboard.
            logger.exception(
                "owner-commission transfer failed for order %s: %s",
                order.get("id"),
                exc,
            )
    # Leaving payout-eligible state via cancel/refund — reverse the credit.
    elif (
        new_status in {WebstoreOrderStatus.CANCELLED.value, WebstoreOrderStatus.REFUNDED.value}
        and payout_recorded
        and commission > 0
    ):
        await db.webstores_v2.update_one(
            {"id": order["webstore_id"], "tenant_id": tenant_id},
            {"$inc": {"payout_owed": -commission}, "$set": {"updated_at": now}},
        )
        update_set["payout_recorded_at"] = None

    await db.webstore_orders_v2.update_one({"id": order["id"]}, {"$set": update_set})
    return update_set


@webstores_router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    data: UpdateOrderStatusRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update order status. See `_apply_order_status_transition` for side-effects."""
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    order = await db.webstore_orders_v2.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    webstore = await db.webstores_v2.find_one(
        {"id": order["webstore_id"], "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Order not found")

    prev_status = order.get("status")
    new_status = data.status.value
    await _apply_order_status_transition(
        order=order,
        new_status=new_status,
        tenant_id=current_user.tenant_id,
        job_id=data.job_id,
    )
    return {"message": "Status updated", "status": new_status, "previous_status": prev_status}


@webstores_router.get("/{webstore_id}", response_model=Webstore)
async def get_webstore(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific webstore"""
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    return webstore


@webstores_router.get("/{webstore_id}/admin-progress")
async def get_webstore_admin_progress(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Phase 6 — admin-facing lifecycle progress + actions + finance.

    Tenant-scoped variant of the owner-portal progress endpoint. Reuses the
    same payload builder so admin and owner see identical numbers. Admin
    sees the same privacy-safe payload (no internal cost / margin / supplier
    fields) — admins access the rich internal data through other routes.
    """
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    from routes.webstore_owners import _build_store_progress_payload
    return await _build_store_progress_payload(webstore)


class AdminStageStampRequest(BaseModel):
    """Phase 6 — additive stage-stamp fields admins can flip."""
    preview_ready_at: Optional[str] = None
    owner_approved_at: Optional[str] = None
    production_started_at: Optional[str] = None
    ready_for_pickup_at: Optional[str] = None
    completed_at: Optional[str] = None
    # Convenience flags — when set true and no timestamp provided, we stamp
    # the current UTC iso datetime. When false and a timestamp exists, we
    # clear that timestamp so admins can undo a mistaken stamp.
    mark_preview_ready: Optional[bool] = None
    mark_owner_approved: Optional[bool] = None
    mark_production_started: Optional[bool] = None
    mark_ready_for_pickup: Optional[bool] = None
    mark_completed: Optional[bool] = None


_STAGE_STAMP_FIELDS = (
    ("mark_preview_ready",     "preview_ready_at"),
    ("mark_owner_approved",    "owner_approved_at"),
    ("mark_production_started","production_started_at"),
    ("mark_ready_for_pickup",  "ready_for_pickup_at"),
    ("mark_completed",         "completed_at"),
)


@webstores_router.patch("/{webstore_id}/admin-progress")
async def patch_webstore_admin_progress(
    webstore_id: str,
    payload: AdminStageStampRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Admin stamps a lifecycle stage timestamp on the store.

    Additive only: writes to `preview_ready_at`, `owner_approved_at`,
    `production_started_at`, `ready_for_pickup_at`, `completed_at`. When
    `mark_completed=true` the store status also flips to "completed" so
    the lifecycle progress walks all 15 stages. Otherwise the status field
    is left alone.
    """
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    update_set: Dict[str, Any] = {"updated_at": now_iso}
    update_unset: Dict[str, str] = {}

    # Convert convenience flags into timestamp set/clear.
    for flag, field in _STAGE_STAMP_FIELDS:
        v = getattr(payload, flag, None)
        if v is True:
            update_set[field] = now_iso
        elif v is False:
            update_unset[field] = ""

    # Explicit timestamp values override the convenience flag where both are sent.
    for field in (
        "preview_ready_at", "owner_approved_at",
        "production_started_at", "ready_for_pickup_at", "completed_at",
    ):
        v = getattr(payload, field, None)
        if v is not None:
            update_set[field] = v

    if payload.mark_completed is True:
        update_set["status"] = "completed"

    mongo_update: Dict[str, Any] = {"$set": update_set}
    if update_unset:
        mongo_update["$unset"] = update_unset

    await db.webstores_v2.update_one({"id": webstore_id}, mongo_update)

    # Audit: log each stamp that was applied.
    stamped = [flag for flag, _ in _STAGE_STAMP_FIELDS if getattr(payload, flag, None) is True]
    if stamped:
        await _log_stage_event(
            webstore_id=webstore_id,
            tenant_id=current_user.tenant_id,
            event_type="stage_stamped",
            actor_id=current_user.id,
            actor_email=current_user.email,
            extra={"stamps_applied": stamped},
        )

    fresh = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    from routes.webstore_owners import _build_store_progress_payload
    return await _build_store_progress_payload(fresh)



@webstores_router.get("/{webstore_id}/analytics")
async def get_webstore_analytics(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get analytics data for a webstore.
    Returns summary stats, sales trends, top products, and fundraiser metrics if applicable.
    """
    # Verify webstore exists and belongs to tenant
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    # Get all orders for this webstore
    orders = await db.webstore_orders_v2.find(
        {"webstore_id": webstore_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Calculate summary stats
    total_orders = len(orders)
    total_revenue = sum(o.get("subtotal", 0) for o in orders)
    total_profit = sum(o.get("total_profit", 0) for o in orders)
    total_commission = sum(o.get("commission_amount", 0) for o in orders)
    
    # Shop profit = total profit - commission paid to store owner
    shop_profit = total_profit - total_commission
    
    pending_orders = len([o for o in orders if o.get("status") in ["pending", "processing"]])
    completed_orders = len([o for o in orders if o.get("status") == "completed"])
    
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Calculate sales by day (last 14 days)
    now = datetime.now(timezone.utc)
    sales_by_day = []
    for i in range(13, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_label = day.strftime("%b %d")
        
        # Sum sales for this day
        day_total = 0
        for order in orders:
            order_date = order.get("created_at", "")
            if order_date and order_date.startswith(day_str):
                day_total += order.get("subtotal", 0)
        
        sales_by_day.append({
            "date": day_str,
            "label": day_label,
            "amount": day_total
        })
    
    # Calculate top products
    product_sales = {}
    for order in orders:
        for item in order.get("items", []):
            pid = item.get("product_id")
            if pid:
                if pid not in product_sales:
                    product_sales[pid] = {
                        "product_id": pid,
                        "product_name": item.get("product_name", "Unknown"),
                        "quantity_sold": 0,
                        "total_revenue": 0
                    }
                product_sales[pid]["quantity_sold"] += item.get("quantity", 0)
                product_sales[pid]["total_revenue"] += item.get("item_total", 0)
    
    # Sort by revenue and take top 5
    top_products = sorted(
        product_sales.values(),
        key=lambda x: x["total_revenue"],
        reverse=True
    )[:5]
    
    # Transform to match frontend expectations (name, quantity, revenue)
    top_products_formatted = [
        {
            "product_id": p["product_id"],
            "name": p["product_name"],
            "quantity": p["quantity_sold"],
            "revenue": p["total_revenue"]
        }
        for p in top_products
    ]
    
    # Payout info
    total_owed = webstore.get("payout_owed", 0)
    total_paid = webstore.get("payout_paid", 0)
    
    payout_info = {
        "total_owed": total_owed,
        "total_paid": total_paid,
        "pending_payout": total_owed,
        "commission_rate": webstore.get("fundraiser_profit_percent", 0) if webstore.get("store_type") == "fundraiser" else webstore.get("creator_commission_value", 0)
    }
    
    # Fundraiser metrics (if applicable)
    fundraiser_metrics = None
    if webstore.get("store_type") == "fundraiser":
        goal = webstore.get("fundraiser_goal", 0) or 0
        raised = total_commission  # What the fundraiser has earned
        progress_percent = (raised / goal * 100) if goal > 0 else 0
        
        # Calculate days remaining
        days_remaining = None
        end_date_str = webstore.get("fundraiser_end_date")
        if end_date_str:
            try:
                # Handle both ISO format and date-only format
                if "T" in end_date_str:
                    end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                else:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_remaining = max(0, (end_date - now).days)
            except Exception:
                pass
        
        fundraiser_metrics = {
            "goal": goal,
            "raised": raised,
            "progress_percent": min(progress_percent, 100),  # Cap at 100%
            "days_remaining": days_remaining,
            "profit_percent": webstore.get("fundraiser_profit_percent", 0)
        }
    
    return {
        "summary": {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "total_profit": total_profit,
            "shop_profit": shop_profit,
            "avg_order_value": avg_order_value
        },
        "payout_info": payout_info,
        "sales_by_day": sales_by_day,
        "top_products": top_products_formatted,
        "fundraiser_metrics": fundraiser_metrics
    }


@webstores_router.get("/{webstore_id}/payouts")
async def get_webstore_payouts(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get payout history for a webstore.
    Returns list of recorded payouts.
    """
    # Verify webstore exists and belongs to tenant
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    # Get payouts from collection
    payouts = await db.webstore_payouts.find(
        {"webstore_id": webstore_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return payouts


@webstores_router.post("/{webstore_id}/record-payout")
async def record_webstore_payout(
    webstore_id: str,
    data: RecordPayoutRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Record a payout to the webstore owner.
    Updates the webstore's payout_owed and payout_paid fields.
    """
    # Moving money — OWNER always has both; ADMIN has webstores:manage via role.
    if not (
        user_has_permission(current_user.role, Permission.FINANCIALS_MANAGE)
        or user_has_permission(current_user.role, Permission.WEBSTORES_MANAGE)
    ):
        raise HTTPException(status_code=403, detail="You don't have permission to record payouts.")
    # Verify webstore exists and belongs to tenant
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    amount = data.amount
    notes = data.notes

    # Atomic guard: only debit payout_owed if it covers the amount. This closes
    # the TOCTOU race where two concurrent payouts each see the same balance.
    current_paid = webstore.get("payout_paid", 0)
    now = datetime.now(timezone.utc).isoformat()
    guard = await db.webstores_v2.update_one(
        {
            "id": webstore_id,
            "tenant_id": current_user.tenant_id,
            "payout_owed": {"$gte": amount},
        },
        {
            "$inc": {"payout_owed": -amount, "payout_paid": amount},
            "$set": {"updated_at": now},
        },
    )
    if guard.modified_count == 0:
        current_owed = webstore.get("payout_owed", 0)
        raise HTTPException(
            status_code=400,
            detail=f"Payout amount (${amount:.2f}) exceeds amount owed (${current_owed:.2f})",
        )

    payout = {
        "id": str(uuid.uuid4()),
        "webstore_id": webstore_id,
        "tenant_id": current_user.tenant_id,
        "amount": amount,
        "notes": notes,
        "recorded_by": current_user.email,
        "created_at": now,
    }
    await db.webstore_payouts.insert_one(payout)

    logger.info(f"Recorded payout of ${amount:.2f} for webstore {webstore_id}")
    new_owed = webstore.get("payout_owed", 0) - amount
    return {
        "message": "Payout recorded",
        "payout_id": payout["id"],
        "new_balance_owed": new_owed,
        "total_paid": current_paid + amount,
    }


@webstores_router.put("/{webstore_id}", response_model=Webstore)
async def update_webstore(
    webstore_id: str, 
    input: WebstoreUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a webstore"""
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Read current status before any mutation (needed for audit trail).
    pre_update = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "status": 1},
    )
    old_status = (pre_update or {}).get("status")

    new_status = update_data.get("status")

    # ── Activation gate ─────────────────────────────────────────────────────
    # Before switching to "active" ensure all required setup steps are done.
    if new_status is not None:
        # Normalise to string value for comparison
        new_status_str = new_status.value if hasattr(new_status, "value") else str(new_status)
        if new_status_str == "active":
            full_store = await db.webstores_v2.find_one(
                {"id": webstore_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
            )
            blockers: list[str] = []

            # Must have at least 1 product assigned
            product_count = await db.webstore_products.count_documents(
                {"webstore_id": webstore_id, "tenant_id": current_user.tenant_id}
            )
            if product_count == 0:
                blockers.append("Assign at least one product before going live.")

            # If a questionnaire was submitted, staff must review it first
            if (full_store or {}).get("questionnaire_submitted_at") and not (full_store or {}).get("questionnaire_reviewed"):
                blockers.append("Questionnaire submitted but not yet reviewed. Apply or dismiss the owner's answers first.")

            if blockers:
                raise HTTPException(
                    status_code=400,
                    detail="Store cannot be activated yet. " + " | ".join(blockers),
                )

    # Gate: cannot move a webstore to "active" until the owner has finished
    # their Stripe Express onboarding (charges_enabled). Tenants must invite
    # the owner via the quick-link or portal-link flow first.
    # (new_status already set above; skip re-declaration)
    if new_status == WebstoreStatus.ACTIVE.value or new_status == WebstoreStatus.ACTIVE:
        existing = await db.webstores_v2.find_one(
            {"id": webstore_id, "tenant_id": current_user.tenant_id},
            {"_id": 0, "owner_stripe_account_id": 1, "owner_stripe_charges_enabled": 1}
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Webstore not found")
        if not (existing.get("owner_stripe_account_id") and existing.get("owner_stripe_charges_enabled")):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Owner has not finished Stripe onboarding. Send them the "
                    "quick connect link or portal invite before activating the store."
                ),
            )
    
    result = await db.webstores_v2.update_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Webstore not found")
    webstore = await db.webstores_v2.find_one({"id": webstore_id}, {"_id": 0})

    # Audit: log status changes to webstore_stage_events.
    if new_status:
        # Ensure we store the plain string value, not the enum repr.
        to_status_str = new_status.value if hasattr(new_status, "value") else str(new_status)
        await _log_stage_event(
            webstore_id=webstore_id,
            tenant_id=current_user.tenant_id,
            event_type="status_changed",
            actor_id=current_user.id,
            actor_email=current_user.email,
            extra={"to_status": to_status_str, "from_status": str(old_status)},
        )

    return webstore


@webstores_router.delete("/{webstore_id}")
async def delete_webstore(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a webstore"""
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    result = await db.webstores_v2.delete_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webstore not found")
    # Clean up product assignments
    await db.webstore_products.delete_many({"webstore_id": webstore_id})
    return {"message": "Webstore deleted"}


@webstores_router.post("/{webstore_id}/upload-logo")
async def upload_webstore_logo(
    webstore_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Upload a logo image for a webstore.

    W12: file is pushed to object storage; the webstore doc only stores the
    storage path + a short public URL pointing to our `/storefront/{id}/asset/logo`
    route. Keeps Mongo docs small and avoids 16MB limit issues.
    """
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    if file.content_type not in _IMAGE_EXT:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: PNG, JPEG, WebP, GIF"
        )

    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 2MB")

    storage_path = _webstore_asset_path(webstore_id, "logo", file.content_type)
    try:
        put_object(storage_path, contents, file.content_type)
    except Exception as exc:
        logger.exception(f"Failed to upload logo for webstore {webstore_id}: {exc}")
        raise HTTPException(status_code=502, detail="Storage upload failed; please retry.")

    now = datetime.now(timezone.utc).isoformat()
    # Append a cache-busting timestamp so browsers refresh after re-upload.
    public_url = f"/api/storefront/{webstore_id}/asset/logo?v={int(datetime.now(timezone.utc).timestamp())}"
    current_branding = webstore.get("branding") or {}
    current_branding["logo_url"] = public_url
    current_branding["logo_storage_path"] = storage_path
    current_branding["logo_content_type"] = file.content_type

    await db.webstores_v2.update_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"$set": {"branding": current_branding, "updated_at": now}}
    )

    logger.info(f"Logo uploaded to object storage for webstore {webstore_id}")
    return {"message": "Logo uploaded successfully", "logo_url": public_url}


@webstores_router.post("/{webstore_id}/upload-banner")
async def upload_webstore_banner(
    webstore_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Upload a banner image for a webstore (object storage, see W12)."""
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    if file.content_type not in _IMAGE_EXT:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: PNG, JPEG, WebP, GIF"
        )

    contents = await file.read()
    # Banners are typically larger than logos.
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")

    storage_path = _webstore_asset_path(webstore_id, "banner", file.content_type)
    try:
        put_object(storage_path, contents, file.content_type)
    except Exception as exc:
        logger.exception(f"Failed to upload banner for webstore {webstore_id}: {exc}")
        raise HTTPException(status_code=502, detail="Storage upload failed; please retry.")

    now = datetime.now(timezone.utc).isoformat()
    public_url = f"/api/storefront/{webstore_id}/asset/banner?v={int(datetime.now(timezone.utc).timestamp())}"
    current_branding = webstore.get("branding") or {}
    current_branding["banner_url"] = public_url
    current_branding["banner_storage_path"] = storage_path
    current_branding["banner_content_type"] = file.content_type

    await db.webstores_v2.update_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"$set": {"branding": current_branding, "updated_at": now}}
    )

    logger.info(f"Banner uploaded to object storage for webstore {webstore_id}")
    return {"message": "Banner uploaded successfully", "banner_url": public_url}


# ============== WEBSTORE PRODUCT ASSIGNMENTS ==============

@webstores_router.post("/{webstore_id}/products")
async def add_product_to_webstore(
    webstore_id: str,
    request: AddProductToWebstoreRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Assign a product to a webstore.
    Validates that both webstore and product belong to the same tenant.
    """
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    # Verify webstore exists and belongs to tenant
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    # Verify product exists AND belongs to same tenant
    product = await db.products.find_one(
        {"id": request.product_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Double-check tenant match (should be guaranteed by queries above, but be explicit)
    if product.get("tenant_id") != webstore.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Product does not belong to the same tenant as webstore")
    
    # Check if already assigned
    existing = await db.webstore_products.find_one({
        "webstore_id": webstore_id, 
        "product_id": request.product_id
    })
    if existing:
        # Update price override and enabled status
        await db.webstore_products.update_one(
            {"id": existing["id"]},
            {"$set": {
                "price_override": request.price_override, 
                "is_enabled": request.is_enabled,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {"message": "Product assignment updated", "assignment_id": existing["id"]}
    
    # Create assignment
    assignment = WebstoreProduct(
        webstore_id=webstore_id,
        product_id=request.product_id,
        is_enabled=request.is_enabled,
        price_override=request.price_override
    )
    await db.webstore_products.insert_one(assignment.model_dump())
    return {"message": "Product added to webstore", "assignment_id": assignment.id}


@webstores_router.get("/{webstore_id}/products")
async def get_webstore_products(
    webstore_id: str,
    include_disabled: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all products assigned to a webstore"""
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    # Build query - include disabled if requested
    query = {"webstore_id": webstore_id}
    if not include_disabled:
        query["is_enabled"] = True
    
    assignments = await db.webstore_products.find(query, {"_id": 0}).to_list(500)

    # W10: batch-fetch all products in one tenant-scoped $in query.
    product_ids = [a["product_id"] for a in assignments]
    if not product_ids:
        return []
    products_cursor = db.products.find(
        {"id": {"$in": product_ids}, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    products_by_id = {p["id"]: p async for p in products_cursor}

    products = []
    for a in assignments:
        product = products_by_id.get(a["product_id"])
        if not product:
            continue
        product["price_override"] = a.get("price_override")
        product["effective_price"] = a.get("price_override") or product["retail_price"]
        product["is_enabled"] = a.get("is_enabled", True)
        product["webstore_product_id"] = a.get("id")
        products.append(product)

    return products


@webstores_router.delete("/{webstore_id}/products/{product_id}")
async def remove_product_from_webstore(
    webstore_id: str,
    product_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Remove a product from a webstore"""
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    # Verify webstore belongs to this tenant before mutating assignments (W1).
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1},
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    result = await db.webstore_products.delete_one({
        "webstore_id": webstore_id,
        "product_id": product_id,
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product assignment not found")
    return {"message": "Product removed from webstore"}


@webstores_router.put("/{webstore_id}/products/{product_id}")
async def update_webstore_product_status(
    webstore_id: str,
    product_id: str,
    data: UpdateWebstoreProductStatusRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a product's enabled status in a webstore"""
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    # Verify webstore belongs to this tenant before mutating assignments (W1).
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1},
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    result = await db.webstore_products.update_one(
        {"webstore_id": webstore_id, "product_id": product_id},
        {"$set": {"is_enabled": data.is_enabled, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product assignment not found")
    return {"message": "Product status updated", "is_enabled": data.is_enabled}


# ============== WEBSTORE ORDERS ==============

@webstores_router.post("/orders", response_model=WebstoreOrder)
async def create_webstore_order(input: WebstoreOrderCreate):
    """
    Create a new order (public endpoint for customers) - auto-creates a job.
    
    Validates:
    - All products exist and belong to the webstore's tenant
    - All products are assigned and enabled in the webstore
    - All variants exist and are available
    - Quantities are >= 1
    - Prices are non-negative
    """
    # SECURITY: Public webstore orders must be finalized from a real paid
    # Stripe checkout session recorded in payment_transactions.
    idempotency_key = (input.idempotency_key or "").strip()
    if not idempotency_key.startswith("stripe:"):
        raise HTTPException(
            status_code=402,
            detail="Stripe checkout is required before creating a webstore order",
        )

    session_id = idempotency_key.replace("stripe:", "", 1).strip()
    if not session_id:
        raise HTTPException(status_code=402, detail="Missing Stripe session")

    payment_tx = await db.payment_transactions.find_one(
        {"stripe_session_id": session_id, "type": "webstore_order"},
        {"_id": 0, "status": 1, "reference_id": 1},
    )
    if not payment_tx or payment_tx.get("reference_id") != input.webstore_id:
        raise HTTPException(
            status_code=402,
            detail="Valid paid Stripe checkout session is required",
        )
    if payment_tx.get("status") != "paid":
        raise HTTPException(
            status_code=402,
            detail="Stripe payment is not completed yet",
        )

    # W17: honor idempotency — if the same (webstore_id, idempotency_key) was
    # submitted within the last hour, return the existing order. Guards against
    # double-click submits and retried network requests.
    if idempotency_key:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        existing = await db.webstore_orders_v2.find_one(
            {
                "webstore_id": input.webstore_id,
                "idempotency_key": idempotency_key,
                "created_at": {"$gte": cutoff},
            },
            {"_id": 0},
        )
        if existing:
            logger.info(
                f"Idempotent order replay matched key={idempotency_key[:8]}… "
                f"returning existing order {existing.get('id')}"
            )
            # Safety: if a prior partial run never rolled this order's
            # donation/profit-allocation into fundraiser totals, do it now.
            # _apply_fundraiser_totals is itself idempotent (flag-guarded).
            try:
                d_amt = float(existing.get("donation_amount") or 0)
                p_amt = float(existing.get("profit_allocation_amount") or 0)
                if (d_amt > 0 or p_amt > 0) and not existing.get("fundraiser_totals_applied"):
                    await _apply_fundraiser_totals(
                        order_id=existing["id"],
                        webstore_id=input.webstore_id,
                        donation_amount=d_amt,
                        profit_allocation_amount=p_amt,
                    )
                    existing["fundraiser_totals_applied"] = True
            except Exception as exc:
                logger.exception(f"backfill fundraiser totals failed: {exc}")
            return existing

    # Get webstore
    webstore = await db.webstores_v2.find_one({"id": input.webstore_id}, {"_id": 0})
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    if webstore.get("status") != "active":
        raise HTTPException(status_code=400, detail="This store is not accepting orders")
    
    if not webstore.get("is_public", True):
        raise HTTPException(status_code=400, detail="This store is not available for orders")
    
    tenant_id = webstore.get("tenant_id")
    
    # ==================== VALIDATION PHASE ====================
    invalid_items = []
    validation_errors = []
    
    for idx, item in enumerate(input.items):
        product_id = item.get("product_id")
        
        # Validate quantity
        quantity = item.get("quantity", 1)
        if quantity < 1:
            validation_errors.append(f"Item {idx}: quantity must be >= 1 (got {quantity})")
            continue
        
        # Check product exists AND belongs to same tenant
        product = await db.products.find_one(
            {"id": product_id, "tenant_id": tenant_id}, 
            {"_id": 0}
        )
        if not product:
            invalid_items.append(product_id)
            continue
        
        # Check product is active
        if not product.get("is_active", True):
            invalid_items.append(product_id)
            continue
        
        # Check product is assigned AND enabled in this webstore
        assignment = await db.webstore_products.find_one({
            "webstore_id": input.webstore_id,
            "product_id": product_id,
            "is_enabled": True
        }, {"_id": 0})
        
        if not assignment:
            validation_errors.append(f"Product '{product.get('name', product_id)}' is not available in this store")
            continue
        
        # Validate variant if provided
        variant_id = item.get("variant_id")
        if variant_id:
            variants = product.get("variants") or []
            if not variants:
                # W6: caller supplied a variant_id but the product has no variants.
                # Reject rather than silently dropping it.
                validation_errors.append(
                    f"Product '{product.get('name', product_id)}' has no variants "
                    f"but variant_id '{variant_id}' was provided"
                )
                continue
            matched = next((v for v in variants if v["id"] == variant_id), None)
            if not matched:
                validation_errors.append(
                    f"Invalid variant '{variant_id}' for product '{product.get('name')}'"
                )
            elif not matched.get("is_available", True):
                validation_errors.append(
                    f"Variant '{matched.get('name', variant_id)}' is not available"
                )
    
    # Return errors if any validation failed
    if invalid_items:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid or unavailable products: {invalid_items}"
        )
    
    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail={"message": "Order validation failed", "errors": validation_errors}
        )
    
    # ==================== PROCESSING PHASE ====================
    order_items = []
    subtotal = 0
    total_cost = 0
    total_profit = 0
    
    for item in input.items:
        product = await db.products.find_one(
            {"id": item["product_id"], "tenant_id": tenant_id}, 
            {"_id": 0}
        )
        
        # Get price override from assignment
        assignment = await db.webstore_products.find_one({
            "webstore_id": input.webstore_id,
            "product_id": item["product_id"]
        }, {"_id": 0})
        
        unit_price = (assignment.get("price_override") if assignment and assignment.get("price_override") 
                      else product.get("retail_price") or 0)
        base_cost = float(product.get("base_cost") or 0)
        
        # Validate price is non-negative
        if unit_price < 0:
            raise HTTPException(status_code=400, detail=f"Invalid price for product '{product['name']}'")
        
        # Handle variant
        variant_name = None
        variant_id = item.get("variant_id")
        if variant_id and product.get("variants"):
            for v in product["variants"]:
                if v["id"] == variant_id:
                    variant_name = v.get("name")
                    base_cost += v.get("additional_cost", 0)
                    unit_price += v.get("additional_cost", 0)  # Add to retail price too
                    break
        
        quantity = item.get("quantity", 1)
        item_total = unit_price * quantity
        item_cost = base_cost * quantity
        item_profit = item_total - item_cost
        
        order_items.append(WebstoreOrderItem(
            product_id=product["id"],
            product_name=product["name"],
            variant_id=variant_id,
            variant_name=variant_name,
            quantity=quantity,
            unit_price=unit_price,
            unit_cost=base_cost,
            item_total=item_total,
            item_profit=item_profit
        ))
        
        subtotal += item_total
        total_cost += item_cost
        total_profit += item_profit
    
    # ==================== COMMISSION CALCULATION ====================
    commission_amount = 0
    store_type = webstore.get("store_type")
    
    if store_type == "fundraiser":
        # Fundraiser: use fundraiser_profit_percent
        profit_percent = webstore.get("fundraiser_profit_percent", 0)
        commission_amount = total_profit * (profit_percent / 100)
    elif store_type == "creator":
        # Creator: use creator_commission_type/value
        if webstore.get("creator_commission_type") == "percentage":
            commission_amount = total_profit * (webstore.get("creator_commission_value", 0) / 100)
        else:
            commission_amount = webstore.get("creator_commission_value", 0)
    # Business stores: no commission (shop keeps all profit)

    # ==================== FUNDRAISER PROFIT ALLOCATION (Event Stores) =========
    # We accept the server-computed allocation passed in from
    # finalize_webstore_stripe_checkout (it's locked from the Stripe session
    # metadata at checkout time). As a defensive recompute, we also derive
    # it from locked_settings + store config and use whichever is smaller —
    # that way the frontend can never inflate the allocation.
    donation_amount = round(float(input.donation_amount or 0), 2)
    shipping_handling_amount = round(float(input.shipping_handling_amount or 0), 2)
    profit_allocation_amount = round(float(input.profit_allocation_amount or 0), 2)
    if profit_allocation_amount > 0 and store_type == "event":
        server_recomputed = compute_event_profit_allocation(
            webstore=webstore,
            order_items=order_items,
            total_profit=total_profit,
        )
        # Trust the smaller of the two so the frontend can never inflate.
        profit_allocation_amount = round(min(profit_allocation_amount, server_recomputed), 2)
    
    # ==================== CUSTOMER & JOB CREATION ====================
    
    # Phase 4 — find-or-create the buyer with webstore_customer tag.
    customer = await _upsert_webstore_customer(
        tenant_id=tenant_id,
        name=input.customer_name,
        email=input.customer_email,
        phone=input.customer_phone,
        tag="webstore_customer",
    )
    
    # Auto-create job
    from models import Job, JobItem
    job = Job(
        customer_id=customer["id"],
        name=f"Webstore Order - {input.customer_name}",
        description=f"Order from: {webstore['name']}\nCustomer: {input.customer_name}\nEmail: {input.customer_email}",
        status=JobStatus.APPROVED,
        tenant_id=tenant_id
    )
    await db.jobs.insert_one(job.model_dump())
    
    # Create job items from order with back-references
    for order_item in order_items:
        # Get the product to determine category
        product = await db.products.find_one(
            {"id": order_item.product_id, "tenant_id": tenant_id},
            {"_id": 0, "category": 1}
        )
        item_type = map_category_to_item_type(product.get("category") if product else "other")
        
        job_item = JobItem(
            job_id=job.id,
            item_type=item_type,
            description=f"{order_item.product_name}" + (f" - {order_item.variant_name}" if order_item.variant_name else ""),
            quantity=order_item.quantity,
            unit_price=order_item.unit_price,
            line_total=order_item.item_total,
            status=JobItemStatus.PENDING
        )
        
        # Store job item with back-references
        job_item_data = job_item.model_dump()
        job_item_data["webstore_order_id"] = None  # Will be set after order is created
        job_item_data["webstore_order_item_product_id"] = order_item.product_id
        job_item_data["variant_id"] = order_item.variant_id
        
        await db.job_items.insert_one(job_item_data)
    
    # Update job subtotal
    await db.jobs.update_one(
        {"id": job.id},
        {"$set": {"subtotal": subtotal}}
    )
    
    # Create order with job link
    order = WebstoreOrder(
        webstore_id=input.webstore_id,
        customer_name=input.customer_name,
        customer_email=input.customer_email,
        customer_phone=input.customer_phone,
        items=[i.model_dump() for i in order_items],
        subtotal=subtotal,
        total_cost=total_cost,
        total_profit=total_profit,
        commission_amount=commission_amount,
        donation_amount=donation_amount,
        profit_allocation_amount=profit_allocation_amount,
        shipping_handling_amount=shipping_handling_amount,
        donor_consent=bool(input.donor_consent and donation_amount > 0),
        grand_total=round(subtotal + shipping_handling_amount + donation_amount, 2),
        notes=input.notes,
        job_id=job.id,  # Link to auto-created job
        status="processing",  # Already in processing since job was created
        idempotency_key=idempotency_key,
    )
    
    await db.webstore_orders_v2.insert_one(order.model_dump())

    order_doc = order.model_dump()

    # Ensure the checkout order appears in the main Orders list and is marked
    # as a webstore-origin order for filtering/visibility.
    main_order_id = await _ensure_main_order_bridge(
        webstore_order_doc=order_doc,
        webstore_doc=webstore,
        customer_doc=customer,
        tenant_id=tenant_id,
        job_id=job.id,
    )
    await db.webstore_orders_v2.update_one(
        {"id": order.id},
        {"$set": {"main_order_id": main_order_id}},
    )
    order_doc["main_order_id"] = main_order_id
    
    # Update job items with back-reference to order ID
    await db.job_items.update_many(
        {"job_id": job.id, "webstore_order_id": None},
        {"$set": {"webstore_order_id": order.id}}
    )
    
    # Update webstore stats. payout_owed is NOT incremented here — it's deferred
    # to the status transition to "completed" (see update_order_status / W4) so
    # phantom/unpaid orders don't inflate what the shop owes the owner.
    await db.webstores_v2.update_one(
        {"id": input.webstore_id},
        {"$inc": {
            "total_sales": subtotal,
            "total_orders": 1,
            "total_profit": total_profit,
        }}
    )

    # Roll donation + profit-allocation into fundraiser totals (idempotent).
    if (donation_amount > 0 or profit_allocation_amount > 0) and store_type == "event":
        await _apply_fundraiser_totals(
            order_id=order.id,
            webstore_id=input.webstore_id,
            donation_amount=donation_amount,
            profit_allocation_amount=profit_allocation_amount,
        )
        order_doc["fundraiser_totals_applied"] = True

    logger.info(f"Order {order.id} created with auto-created job {job.id}")
    
    return order_doc


@webstores_router.post("/orders/{order_id}/create-job")
async def create_job_from_order(
    order_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create a job from a webstore order.
    
    IDEMPOTENT: If job already exists for this order, returns existing job_id.
    """
    order = await db.webstore_orders_v2.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify the webstore belongs to this tenant
    webstore = await db.webstores_v2.find_one(
        {"id": order["webstore_id"], "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # IDEMPOTENT: If job already exists, return it instead of error
    if order.get("job_id"):
        return {"message": "Job already exists for this order", "job_id": order["job_id"]}
    
    # Phase 4 — find-or-create the buyer when admin manually creates a job
    # from an existing webstore order. Same dedupe + tagging rules as checkout.
    customer = await _upsert_webstore_customer(
        tenant_id=current_user.tenant_id,
        name=order["customer_name"],
        email=order["customer_email"],
        phone=order.get("customer_phone"),
        tag="webstore_customer",
    )
    
    # Create job
    from models import Job, JobItem
    job = Job(
        customer_id=customer["id"],
        name=f"Webstore Order #{order_id[:8]}",
        description=f"From: {webstore['name'] if webstore else 'Unknown Store'}\nCustomer: {order['customer_name']}",
        status=JobStatus.APPROVED,
        tenant_id=current_user.tenant_id
    )
    await db.jobs.insert_one(job.model_dump())
    
    # Create job items with proper type mapping and back-references
    for item in order.get("items", []):
        # Get product to determine category
        product = await db.products.find_one(
            {"id": item.get("product_id"), "tenant_id": current_user.tenant_id},
            {"_id": 0, "category": 1}
        )
        item_type = map_category_to_item_type(product.get("category") if product else "other")
        
        job_item = JobItem(
            job_id=job.id,
            item_type=item_type,
            description=f"{item['product_name']}" + (f" - {item['variant_name']}" if item.get('variant_name') else ""),
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            line_total=item["item_total"],
            status=JobItemStatus.PENDING
        )
        
        # Add back-references
        job_item_data = job_item.model_dump()
        job_item_data["webstore_order_id"] = order_id
        job_item_data["webstore_order_item_product_id"] = item.get("product_id")
        job_item_data["variant_id"] = item.get("variant_id")
        
        await db.job_items.insert_one(job_item_data)
    
    # Update job subtotal
    await db.jobs.update_one(
        {"id": job.id},
        {"$set": {"subtotal": order["subtotal"]}}
    )
    
    # Link order to job
    await db.webstore_orders_v2.update_one(
        {"id": order_id},
        {"$set": {"job_id": job.id, "status": "processing"}}
    )
    
    return {"message": "Job created", "job_id": job.id}


# ============== EVENT STORE QUESTIONNAIRE ENDPOINTS ==============

class SendEventStoreQuestionnairePayload(BaseModel):
    email: Optional[str] = None          # override; falls back to owner_email
    customer_name: Optional[str] = None  # override; falls back to owner_name
    message: Optional[str] = None        # optional custom email intro
    public_url: Optional[str] = None     # frontend origin for building the link


@webstores_router.get("/{webstore_id}/questionnaire")
async def get_webstore_questionnaire_status(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Return the questionnaire linked to an Event Store, plus the latest response summary."""
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1, "name": 1, "store_type": 1},
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    questionnaire = await db.questionnaires.find_one(
        {"webstore_id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1, "name": 1, "status": 1,
         "response_count": 1, "last_sent_at": 1, "updated_at": 1},
    )
    if not questionnaire:
        return {"linked": False, "questionnaire": None, "latest_response": None}

    responses = await db.questionnaire_responses.find(
        {"questionnaire_id": questionnaire["id"]},
        {"_id": 0, "id": 1, "submitted_at": 1, "customer_name": 1, "customer_email": 1,
         "applied_to_webstore": 1},
    ).sort("submitted_at", -1).limit(1).to_list(1)
    latest_response = responses[0] if responses else None

    return {
        "linked": True,
        "questionnaire": questionnaire,
        "latest_response": latest_response,
    }


@webstores_router.get("/{webstore_id}/event-setup-checklist")
async def get_event_store_setup_checklist(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Admin Event Store quick-status checklist.

    Returns a structured list of setup steps with completion flags. All
    values are derived from existing data (no separate tracking table).
    """
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    # Event details — at minimum we want event_name + dates (start or end)
    # plus either an order_deadline or a pickup_delivery_date.
    has_event_basics = bool(
        webstore.get("event_name")
        and (webstore.get("event_start_date") or webstore.get("event_end_date"))
    )
    has_event_logistics = bool(
        webstore.get("order_deadline") or webstore.get("pickup_delivery_date")
    )
    event_details_complete = bool(has_event_basics and has_event_logistics)

    # Questionnaire status — sent + completed + applied
    questionnaire = await db.questionnaires.find_one(
        {"webstore_id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1, "status": 1, "last_sent_at": 1, "response_count": 1},
    )
    questionnaire_sent = bool(questionnaire and questionnaire.get("last_sent_at"))
    latest_response = None
    questionnaire_completed = False
    safe_answers_applied = False
    if questionnaire:
        latest_response = await db.questionnaire_responses.find_one(
            {"questionnaire_id": questionnaire["id"]},
            {"_id": 0, "id": 1, "submitted_at": 1, "applied_to_webstore": 1},
            sort=[("submitted_at", -1)],
        )
        questionnaire_completed = bool(latest_response and latest_response.get("submitted_at"))
        safe_answers_applied = bool(latest_response and latest_response.get("applied_to_webstore"))

    # Stripe onboarding (owner-side)
    stripe_invite_sent = bool(
        await db.webstore_owner_invites.find_one(
            {"webstore_id": webstore_id, "tenant_id": current_user.tenant_id},
            {"_id": 0, "id": 1},
        )
        or webstore.get("owner_stripe_account_id")
    )
    stripe_complete = bool(webstore.get("owner_stripe_charges_enabled"))

    # Products assigned to this webstore
    products_count = await db.webstore_products.count_documents({
        "webstore_id": webstore_id,
    })
    products_assigned = products_count > 0

    # Store live = status==active
    store_live = (webstore.get("status") == "active")

    # First order received
    first_order = await db.webstore_orders_v2.find_one(
        {"webstore_id": webstore_id},
        {"_id": 0, "id": 1, "created_at": 1},
        sort=[("created_at", 1)],
    )
    first_order_received = bool(first_order)

    fundraiser_enabled = bool(webstore.get("fundraiser_enabled"))

    items = [
        {"key": "event_details", "label": "Event details completed", "done": event_details_complete,
         "hint": None if event_details_complete else "Add event name, dates, and order deadline."},
        {"key": "questionnaire_sent", "label": "Setup questionnaire sent", "done": questionnaire_sent,
         "hint": None if questionnaire_sent else "Send the setup questionnaire to the store owner."},
        {"key": "questionnaire_completed", "label": "Questionnaire completed by owner",
         "done": questionnaire_completed,
         "hint": None if questionnaire_completed else "Waiting on the store owner to submit."},
        {"key": "safe_answers_applied", "label": "Safe answers applied to store",
         "done": safe_answers_applied,
         "hint": None if safe_answers_applied else "Review and apply the submitted answers."},
        {"key": "stripe_invite_sent", "label": "Stripe onboarding invite sent", "done": stripe_invite_sent,
         "hint": None if stripe_invite_sent else "Send a Quick Connect or Owner Portal invite."},
        {"key": "stripe_complete", "label": "Stripe onboarding complete", "done": stripe_complete,
         "hint": None if stripe_complete else "Owner still needs to finish Stripe onboarding."},
        {"key": "fundraiser_enabled", "label": "Fundraiser enabled (optional)", "done": fundraiser_enabled,
         "optional": True,
         "hint": None if fundraiser_enabled else "Toggle on in Event Settings if this is a fundraiser."},
        {"key": "products_assigned", "label": "Products assigned to store", "done": products_assigned,
         "hint": None if products_assigned else "Assign at least one product from the catalog."},
        {"key": "store_live", "label": "Store live (status = active)", "done": store_live,
         "hint": None if store_live else "Activate the store once Stripe + products are ready."},
        {"key": "first_order_received", "label": "First order received", "done": first_order_received,
         "optional": True,
         "hint": None if first_order_received else "No orders yet — share the public store link to launch."},
    ]
    # Required steps for the headline "complete" percent.
    required = [i for i in items if not i.get("optional")]
    done = sum(1 for i in required if i["done"])
    return {
        "webstore_id": webstore_id,
        "store_type": webstore.get("store_type"),
        "items": items,
        "required_count": len(required),
        "required_done": done,
        "percent_complete": round((done / len(required)) * 100) if required else 0,
    }


@webstores_router.post("/{webstore_id}/questionnaire/send")
async def send_event_store_questionnaire(
    webstore_id: str,
    payload: SendEventStoreQuestionnairePayload,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Ensure an event_web_store_setup questionnaire exists for this Event Store,
    set it to ACTIVE, pre-fill/lock tenant-controlled fields, and email it to
    the store owner.

    The questionnaire is created from the template exactly once per webstore.
    Re-sending uses the same questionnaire document (idempotent).
    locked_settings values are pre-filled in the questionnaire but NEVER auto-applied
    back from store-owner answers — only admin can do that via apply-answers.
    """
    from services.email_service import email_service
    from models.questionnaires import (
        Questionnaire, Question, QuestionType, QuestionnaireCategory,
        QuestionnaireStatus, QUESTIONNAIRE_TEMPLATES,
    )

    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    # Idempotent: reuse existing questionnaire if one is already linked
    existing = await db.questionnaires.find_one(
        {"webstore_id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1},
    )

    if existing:
        questionnaire_id = existing["id"]
        now = datetime.now(timezone.utc).isoformat()
        await db.questionnaires.update_one(
            {"id": questionnaire_id},
            {"$set": {"status": "active", "last_sent_at": now, "updated_at": now}},
        )
    else:
        # Create from template — Phase 4 picks the right template based on
        # the store_type. Event continues to be the rich event template;
        # fundraiser / team-school / business get their own templates.
        template_key = _template_key_for_store_type(webstore.get("store_type"))
        template = QUESTIONNAIRE_TEMPLATES.get(template_key)
        if not template:
            raise HTTPException(
                status_code=500,
                detail=f"Questionnaire template '{template_key}' not found",
            )

        questions: list[Question] = []
        for i, q in enumerate(template["questions"]):
            questions.append(Question(
                id=str(uuid.uuid4()),
                type=QuestionType(q["type"]),
                label=q["label"],
                description=q.get("description"),
                placeholder=q.get("placeholder"),
                required=q.get("required", False),
                options=[{"value": o["value"], "label": o["label"]}
                         for o in q.get("options", [])],
                order=q.get("order", i),
                accept_file_types=q.get("accept_file_types"),
                max_file_size_mb=q.get("max_file_size_mb", 10),
            ))

        # ── Build prefill/locked maps from event fields + locked_settings ──
        ls = webstore.get("locked_settings") or {}
        prefill_answers: dict = {}
        locked_answer_ids: list = []

        # Map of question label → prefill value (from event store fields)
        store_prefills = {
            "Event Name": webstore.get("event_name"),
            "Event Date": webstore.get("event_start_date"),
            "Event Location": webstore.get("event_location"),
            "What should the store be called?": webstore.get("name"),
            "Pickup date / time instructions": webstore.get("pickup_delivery_instructions"),
        }
        # Map of question label → locked value (from locked_settings, admin-controlled)
        locked_prefills = {
            "If adding profit, how much should be added per item?": (
                f"${float(ls['store_owner_profit']):.2f} per item"
                if ls.get("store_owner_profit") is not None else None
            ),
            "Best email to receive the Stripe Connect setup link": webstore.get("owner_email"),
        }

        for q_obj in questions:
            label = q_obj.label
            val = store_prefills.get(label)
            if val:
                prefill_answers[q_obj.id] = val
            locked_val = locked_prefills.get(label)
            if locked_val:
                prefill_answers[q_obj.id] = locked_val
                locked_answer_ids.append(q_obj.id)

        # Build a human-friendly questionnaire name per store type.
        store_type_label = {
            "event":       "Event Store Setup",
            "fundraiser":  "Fundraiser Store Setup",
            "team_school": "Team / School Store Setup",
            "team":        "Team / School Store Setup",
            "school":      "Team / School Store Setup",
            "creator":     "Team / School Store Setup",
            "business":    "Business Store Setup",
            "b2b":         "Business Store Setup",
            "company":     "Business Store Setup",
        }.get((webstore.get("store_type") or "").lower(), "Store Setup")
        now = datetime.now(timezone.utc).isoformat()
        q_doc = Questionnaire(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            name=f"{store_type_label} — {webstore['name']}",
            description=template["description"],
            category=QuestionnaireCategory(template["category"]),
            questions=questions,
            status=QuestionnaireStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            created_by=current_user.id,
            webstore_id=webstore_id,
            prefill_answers=prefill_answers,
            locked_answer_ids=locked_answer_ids,
            last_sent_at=now,
        )
        await db.questionnaires.insert_one(q_doc.model_dump())
        questionnaire_id = q_doc.id

    # ── Resolve recipient ──
    to_email = (payload.email or "").strip() or webstore.get("owner_email", "")
    if not to_email:
        raise HTTPException(
            status_code=400,
            detail=(
                "No email address found for the store owner. "
                "Add an owner email to the store or provide one in the request."
            ),
        )

    # ── Build public link ──
    origin = (payload.public_url or os.environ.get("META_PUBLIC_URL", "") or "").rstrip("/")
    link = (
        f"{origin}/questionnaire/{questionnaire_id}"
        if origin
        else f"/questionnaire/{questionnaire_id}"
    )

    # ── Tenant branding ──
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    company_name = (tenant or {}).get("company_name") or (tenant or {}).get("name") or "SignGuy AI"

    greeting_name = (
        (payload.customer_name or webstore.get("owner_name") or "").strip() or "there"
    )
    intro = payload.message or (
        f"We need a few details to set up the event web store for "
        f"<strong>{webstore.get('name')}</strong>. "
        "Please complete the questionnaire below at your earliest convenience."
    )

    subject = f"Event Store Setup: {webstore.get('name')} — Please Complete"
    html_content = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;
                padding:24px;color:#0F172A;">
      <h2 style="color:#0F172A;margin-bottom:8px;">Event Web Store Setup</h2>
      <p style="color:#475569;margin-top:0;">From {company_name}</p>
      <p>Hi {greeting_name},</p>
      <p>{intro}</p>
      <p style="margin:28px 0;">
        <a href="{link}"
           style="background:#F97316;color:#ffffff;padding:12px 24px;
                  border-radius:8px;text-decoration:none;display:inline-block;
                  font-weight:600;">
          Complete Event Store Setup
        </a>
      </p>
      <p style="color:#475569;font-size:13px;">
        Or copy &amp; paste this link:<br/>
        <a href="{link}" style="color:#F97316;">{link}</a>
      </p>
      <hr style="border:none;border-top:1px solid #E2E8F0;margin:24px 0;"/>
      <p style="color:#94A3B8;font-size:12px;">Sent by {company_name}</p>
    </div>
    """
    plain_content = (
        f"Event Store Setup: {webstore.get('name')}\n\n"
        f"Hi {greeting_name},\n\n{intro}\n\nOpen: {link}\n\n— {company_name}"
    )

    result = await email_service.send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        plain_content=plain_content,
        tenant_id=current_user.tenant_id,
    )

    if not result.get("success"):
        # Email failed but questionnaire was created — still usable via link
        return {
            "success": False,
            "questionnaire_id": questionnaire_id,
            "link": link,
            "email_sent": False,
            "email": to_email,
            "warning": (
                result.get("error")
                or "Email sending failed. Check SendGrid configuration. "
                   "Share the link manually."
            ),
        }

    return {
        "success": True,
        "questionnaire_id": questionnaire_id,
        "link": link,
        "email_sent": True,
        "email": to_email,
    }


@webstores_router.get("/{webstore_id}/questionnaire/review-details")
async def get_questionnaire_review_details(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Dry-run preview of questionnaire answer mapping without writing to DB."""
    _require_permission(current_user, Permission.WEBSTORES_MANAGE)
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    questionnaire = await db.questionnaires.find_one({"webstore_id": webstore_id}, {"_id": 0})
    if not questionnaire:
        return {
            "has_questionnaire": False,
            "questionnaire_reviewed": webstore.get("questionnaire_reviewed", False),
            "questionnaire_submitted_at": webstore.get("questionnaire_submitted_at"),
        }

    response = await db.questionnaire_responses.find_one(
        {"questionnaire_id": questionnaire["id"]},
        {"_id": 0},
        sort=[("submitted_at", -1)],
    )
    if not response:
        return {
            "has_questionnaire": True, "has_response": False,
            "questionnaire": {"id": questionnaire["id"], "name": questionnaire.get("name"), "last_sent_at": questionnaire.get("last_sent_at")},
            "questionnaire_reviewed": webstore.get("questionnaire_reviewed", False),
            "questionnaire_submitted_at": webstore.get("questionnaire_submitted_at"),
        }

    # Build label ↔ id maps; walk both flat questions and nested sections.
    q_label_to_id: dict = {}
    q_id_to_label: dict = {}
    for q in questionnaire.get("questions", []) or []:
        if isinstance(q, dict) and q.get("id") and q.get("label"):
            q_label_to_id[q["label"]] = q["id"]
            q_id_to_label[q["id"]] = q["label"]
    for section in questionnaire.get("sections", []) or []:
        for q in (section.get("questions", []) or []):
            if isinstance(q, dict) and q.get("id") and q.get("label"):
                q_label_to_id[q["label"]] = q["id"]
                q_id_to_label[q["id"]] = q["label"]

    # answers stored as {question_id: value}; convert to {label: value}.
    raw_answers = response.get("answers") or {}
    all_answers: dict = {}
    if isinstance(raw_answers, dict):
        for q_id, val in raw_answers.items():
            label = q_id_to_label.get(q_id, "")
            if label and val not in (None, "", []):
                all_answers[label] = val

    locked_ids: set = set(questionnaire.get("locked_answer_ids") or [])

    safe_fields = []
    suggested_changes = []
    for label, (store_field, coerce_fn) in QUESTIONNAIRE_SAFE_MAP.items():
        raw_val = all_answers.get(label)
        if raw_val is None:
            continue
        val = coerce_fn(raw_val) if coerce_fn else raw_val
        if val is None:
            continue
        q_id = q_label_to_id.get(label)
        if q_id in locked_ids:
            suggested_changes.append({"field": store_field, "label": label, "suggested_value": val, "reason": "Locked by store provider"})
        else:
            safe_fields.append({"field": store_field, "label": label, "value": val, "current_value": webstore.get(store_field)})

    mapped_labels = set(QUESTIONNAIRE_SAFE_MAP.keys())
    admin_review_answers = [
        {"label": label, "answer": val}
        for label, val in all_answers.items()
        if label and label not in mapped_labels and val not in (None, "", [])
    ]
    return {
        "has_questionnaire": True, "has_response": True,
        "questionnaire": {"id": questionnaire["id"], "name": questionnaire.get("name"), "last_sent_at": questionnaire.get("last_sent_at")},
        "response": {
            "id": response["id"], "submitted_at": response.get("submitted_at"),
            "customer_name": response.get("customer_name"), "customer_email": response.get("customer_email"),
            "applied_to_webstore": response.get("applied_to_webstore", False),
        },
        "safe_fields": safe_fields,
        "suggested_changes": suggested_changes,
        "admin_review_answers": admin_review_answers,
        "pending_review_changes": webstore.get("pending_review_changes", []),
        "questionnaire_reviewed": webstore.get("questionnaire_reviewed", False),
        "questionnaire_reviewed_at": webstore.get("questionnaire_reviewed_at"),
        "questionnaire_submitted_at": webstore.get("questionnaire_submitted_at"),
    }


@webstores_router.post("/{webstore_id}/questionnaire/apply-answers")
async def apply_questionnaire_answers_to_event_store(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Map safe questionnaire answers into Event Store fields.

    NEVER touches locked_settings — those remain admin-controlled.
    Returns applied_fields (immediately saved) and suggested_changes
    (fields that would overwrite locked values; saved for admin review only).
    """
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")

    questionnaire = await db.questionnaires.find_one(
        {"webstore_id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not questionnaire:
        raise HTTPException(status_code=404, detail="No questionnaire is linked to this event store")

    # Latest response
    responses = await db.questionnaire_responses.find(
        {"questionnaire_id": questionnaire["id"]},
        {"_id": 0},
    ).sort("submitted_at", -1).limit(1).to_list(1)
    if not responses:
        raise HTTPException(status_code=404, detail="No questionnaire responses found")
    response = responses[0]

    # Build label → question_id map; walk both flat questions and nested sections.
    q_label_to_id: dict = {}
    for q in questionnaire.get("questions", []) or []:
        if isinstance(q, dict) and q.get("label") and q.get("id"):
            q_label_to_id[q["label"]] = q["id"]
    for section in questionnaire.get("sections", []) or []:
        for q in (section.get("questions", []) or []):
            if isinstance(q, dict) and q.get("label") and q.get("id"):
                q_label_to_id[q["label"]] = q["id"]
    answers = response.get("answers", {})
    locked_ids = set(questionnaire.get("locked_answer_ids") or [])

    def _answer(label: str):
        q_id = q_label_to_id.get(label)
        if not q_id:
            return None
        val = answers.get(q_id)
        if not val or (isinstance(val, list) and len(val) == 0):
            return None
        return val

    def _as_bool(val) -> Optional[bool]:
        """Convert questionnaire yes/no answers to bool."""
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("yes", "true", "1", "yes_all", "yes_with_permission")
        return None

    def _as_float(val) -> Optional[float]:
        """Convert questionnaire number answers to float."""
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    # Uses the module-level QUESTIONNAIRE_SAFE_MAP (label → (store_field, coerce_fn)).
    # Never touches locked_settings — those remain admin-controlled.
    SAFE_MAP: dict = QUESTIONNAIRE_SAFE_MAP

    applied: dict = {}
    suggested_changes: list = []
    now = datetime.now(timezone.utc).isoformat()

    for label, (store_field, coerce_fn) in SAFE_MAP.items():
        raw_val = _answer(label)
        if raw_val is None:
            continue
        val = coerce_fn(raw_val) if coerce_fn else raw_val
        if val is None:
            continue
        q_id = q_label_to_id.get(label)
        if q_id in locked_ids:
            # Locked field — save as suggested, do not auto-apply
            suggested_changes.append({
                "field": store_field,
                "label": label,
                "suggested_value": val,
                "reason": "This field is locked (set by store provider). Admin review required.",
            })
        else:
            applied[store_field] = val

    if applied:
        applied["updated_at"] = now
        await db.webstores_v2.update_one({"id": webstore_id}, {"$set": applied})
        await db.questionnaire_responses.update_one(
            {"id": response["id"]},
            {"$set": {"applied_to_webstore": True, "applied_at": now}},
        )

    # Persist the review outcome to the webstore regardless of whether
    # safe fields were applied, so the Setup flow can show review status.
    review_update = {
        "questionnaire_reviewed": True,
        "questionnaire_reviewed_at": now,
        "pending_review_changes": suggested_changes,
    }
    await db.webstores_v2.update_one({"id": webstore_id}, {"$set": review_update})

    return {
        "applied_fields": {k: v for k, v in applied.items() if k != "updated_at"},
        "suggested_changes": suggested_changes,
        "response_id": response["id"],
        "message": (
            f"Applied {len(applied) - (1 if 'updated_at' in applied else 0)} field(s)."
            + (f" {len(suggested_changes)} field(s) require admin review." if suggested_changes else "")
        ),
        "questionnaire_reviewed": True,
    }
