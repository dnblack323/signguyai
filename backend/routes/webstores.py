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
    base_cost: float
    retail_price: float
    # Support up to 3 images
    images: List[str] = []
    image_url: Optional[str] = None  # Legacy field - still support for backwards compat
    has_variants: bool = False
    variants: List[ProductVariant] = []
    is_active: bool = True
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


class WebstoreBranding(BaseModel):
    # Allow the storage_path / content_type metadata fields to flow through
    # so internal handlers see them; response serialization will still emit
    # the public logo_url/banner_url which is what the UI uses.
    model_config = ConfigDict(extra="allow")
    logo_url: Optional[str] = None
    primary_color: str = "#0D9488"
    banner_url: Optional[str] = None


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
    status: WebstoreStatus = WebstoreStatus.ACTIVE
    is_public: bool = True
    branding: WebstoreBranding = Field(default_factory=WebstoreBranding)
    fundraiser_goal: Optional[float] = None
    fundraiser_start_date: Optional[str] = None
    fundraiser_end_date: Optional[str] = None
    fundraiser_profit_percent: float = 0
    creator_commission_type: str = "percentage"
    creator_commission_value: float = 0
    total_sales: float = 0
    total_orders: int = 0
    total_profit: float = 0
    payout_owed: float = 0
    payout_paid: float = 0
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
    fundraiser_goal: Optional[float] = Field(default=None, ge=0)
    fundraiser_start_date: Optional[str] = None
    fundraiser_end_date: Optional[str] = None
    fundraiser_profit_percent: float = Field(default=0, ge=0, le=100)
    creator_commission_type: str = Field(default="percentage", pattern="^(percentage|flat)$")
    creator_commission_value: float = Field(default=0, ge=0)


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
    if store_type not in {WebstoreType.BUSINESS.value, WebstoreType.FUNDRAISER.value, WebstoreType.CREATOR.value}:
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
    "fundraiser_goal", "fundraiser_start_date", "fundraiser_end_date",
    "total_sales", "total_orders"  # Allow for fundraiser progress display
]

def sanitize_webstore_for_public(webstore: dict) -> dict:
    """Return only safe fields for public consumption"""
    safe = {k: webstore.get(k) for k in WEBSTORE_PUBLIC_FIELDS if k in webstore}

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
    
    # Only return if store is public and active
    if not webstore.get("is_public", True):
        raise HTTPException(status_code=404, detail="Store not found")
    
    if webstore.get("status") != "active":
        raise HTTPException(status_code=404, detail="Store is not currently available")
    
    public_webstore = sanitize_webstore_for_public(webstore)
    tenant = await db.tenants.find_one({"id": webstore.get("tenant_id")}, {"_id": 0})
    checkout = _get_stripe_checkout_status(tenant.get("stripe_connect_account_id") if tenant else None)
    public_webstore["checkout_enabled"] = checkout["enabled"]
    public_webstore["checkout_status"] = checkout["status"]
    public_webstore["checkout_message"] = checkout["message"]
    return public_webstore


@storefront_router.get("/{webstore_id}/products")
async def get_public_store_products(webstore_id: str):
    """
    Get products for a public webstore (no auth required).
    Ensures products belong to the same tenant as the webstore.
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
    
    if webstore.get("status") != "active":
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
        variants=variants
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
    branding = WebstoreBranding(**(input.branding or {}))
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
        creator_commission_value=input.creator_commission_value
    )
    doc = webstore.model_dump()
    await db.webstores_v2.insert_one(doc)
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
    
    result = await db.webstores_v2.update_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Webstore not found")
    webstore = await db.webstores_v2.find_one({"id": webstore_id}, {"_id": 0})
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
                      else product["retail_price"])
        base_cost = product["base_cost"]
        
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
    
    # ==================== CUSTOMER & JOB CREATION ====================
    
    # Auto-create or find customer
    customer = await db.customers.find_one(
        {"email": input.customer_email, "tenant_id": tenant_id}, 
        {"_id": 0}
    )
    if not customer:
        from models import Customer
        customer = Customer(
            name=input.customer_name,
            email=input.customer_email,
            phone=input.customer_phone,
            tenant_id=tenant_id
        )
        await db.customers.insert_one(customer.model_dump())
        customer = customer.model_dump()
    
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
    
    # Create or find customer (tenant-filtered)
    customer = await db.customers.find_one(
        {"email": order["customer_email"], "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not customer:
        from models import Customer
        customer = Customer(
            name=order["customer_name"],
            email=order["customer_email"],
            phone=order.get("customer_phone"),
            tenant_id=current_user.tenant_id
        )
        await db.customers.insert_one(customer.model_dump())
        customer = customer.model_dump()
    
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
