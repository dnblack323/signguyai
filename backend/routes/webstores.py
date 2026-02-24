"""
Webstore Routes

This module contains all routes related to:
- Master Product Catalog (sign shop's products)
- Webstores (B2B, Fundraiser, Creator stores)
- Webstore product assignments
- Webstore orders (public ordering)
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
import uuid
import base64
from enum import Enum

# Import from server module
from server import db, logger, get_current_active_user

from models import UserInDB, JobStatus, JobItemType, JobItemStatus


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
    fundraiser_goal: Optional[float] = None
    fundraiser_start_date: Optional[str] = None
    fundraiser_end_date: Optional[str] = None
    fundraiser_profit_percent: float = 0
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
    price_override: Optional[float] = None


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WebstoreOrderCreate(BaseModel):
    webstore_id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    items: List[Dict[str, Any]]
    notes: Optional[str] = None


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
    return {k: webstore.get(k) for k in WEBSTORE_PUBLIC_FIELDS if k in webstore}


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
    
    # Return sanitized response
    return sanitize_webstore_for_public(webstore)


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
    
    # Enrich with product details - TENANT SAFE
    products = []
    for a in assignments:
        # Ensure product belongs to same tenant as webstore
        product = await db.products.find_one(
            {"id": a["product_id"], "tenant_id": tenant_id}, 
            {"_id": 0}
        )
        if product and product.get("is_active", True):
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
            products.append(enriched)
    
    return products


# ============== PRODUCT ROUTES ==============

@products_router.post("", response_model=Product)
async def create_product(
    input: ProductCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new product in the master catalog"""
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
    webstores = await db.webstores_v2.find(query, {"_id": 0}).to_list(500)
    return webstores


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


@webstores_router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update order status"""
    # Verify access first
    order = await db.webstore_orders_v2.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    webstore = await db.webstores_v2.find_one(
        {"id": order["webstore_id"], "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Order not found")
    
    await db.webstore_orders_v2.update_one(
        {"id": order_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Status updated"}


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


@webstores_router.put("/{webstore_id}", response_model=Webstore)
async def update_webstore(
    webstore_id: str, 
    input: WebstoreUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a webstore"""
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
    """Upload a logo image for a webstore"""
    # Verify webstore exists and belongs to tenant
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Allowed: PNG, JPEG, WebP, GIF"
        )
    
    # Read and encode the file
    contents = await file.read()
    
    # Check file size (max 2MB)
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 2MB")
    
    # Convert to base64 data URL
    base64_encoded = base64.b64encode(contents).decode('utf-8')
    logo_data_url = f"data:{file.content_type};base64,{base64_encoded}"
    
    # Update the webstore branding with the logo
    current_branding = webstore.get("branding", {})
    current_branding["logo_url"] = logo_data_url
    
    await db.webstores_v2.update_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"$set": {
            "branding": current_branding,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Logo uploaded for webstore {webstore_id}")
    
    return {"message": "Logo uploaded successfully", "logo_url": logo_data_url}


@webstores_router.post("/{webstore_id}/upload-banner")
async def upload_webstore_banner(
    webstore_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Upload a banner image for a webstore"""
    # Verify webstore exists and belongs to tenant
    webstore = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not webstore:
        raise HTTPException(status_code=404, detail="Webstore not found")
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Allowed: PNG, JPEG, WebP, GIF"
        )
    
    # Read and encode the file
    contents = await file.read()
    
    # Check file size (max 5MB for banners - they're typically larger)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
    
    # Convert to base64 data URL
    base64_encoded = base64.b64encode(contents).decode('utf-8')
    banner_data_url = f"data:{file.content_type};base64,{base64_encoded}"
    
    # Update the webstore branding with the banner
    current_branding = webstore.get("branding", {})
    current_branding["banner_url"] = banner_data_url
    
    await db.webstores_v2.update_one(
        {"id": webstore_id, "tenant_id": current_user.tenant_id},
        {"$set": {
            "branding": current_branding,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Banner uploaded for webstore {webstore_id}")
    
    return {"message": "Banner uploaded successfully", "banner_url": banner_data_url}


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
    
    # Enrich with product details
    products = []
    for a in assignments:
        product = await db.products.find_one({"id": a["product_id"]}, {"_id": 0})
        if product:
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
    result = await db.webstore_products.delete_one({
        "webstore_id": webstore_id, 
        "product_id": product_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product assignment not found")
    return {"message": "Product removed from webstore"}


@webstores_router.put("/{webstore_id}/products/{product_id}")
async def update_webstore_product_status(
    webstore_id: str,
    product_id: str,
    is_enabled: bool = True,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a product's enabled status in a webstore"""
    result = await db.webstore_products.update_one(
        {"webstore_id": webstore_id, "product_id": product_id},
        {"$set": {"is_enabled": is_enabled, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product assignment not found")
    return {"message": "Product status updated", "is_enabled": is_enabled}


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
        if variant_id and product.get("variants"):
            variant_found = False
            for v in product["variants"]:
                if v["id"] == variant_id:
                    if not v.get("is_available", True):
                        validation_errors.append(f"Variant '{v.get('name', variant_id)}' is not available")
                    else:
                        variant_found = True
                    break
            if not variant_found and variant_id not in [v["id"] for v in product["variants"]]:
                validation_errors.append(f"Invalid variant '{variant_id}' for product '{product.get('name')}'")
    
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
    
    # Helper to map product category to job item type
    def map_category_to_item_type(category: str) -> JobItemType:
        """Map webstore product category to job item type"""
        category_map = {
            "apparel": JobItemType.OTHER,  # No direct apparel type
            "signs": JobItemType.BANNER,   # Use banner as closest match
            "decals": JobItemType.DECAL,
            "promotional": JobItemType.OTHER,
            "other": JobItemType.OTHER,
        }
        return category_map.get(category, JobItemType.OTHER)
    
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
        status="processing"  # Already in processing since job was created
    )
    
    await db.webstore_orders_v2.insert_one(order.model_dump())
    
    # Update job items with back-reference to order ID
    await db.job_items.update_many(
        {"job_id": job.id, "webstore_order_id": None},
        {"$set": {"webstore_order_id": order.id}}
    )
    
    # Update webstore stats - increment payout_owed
    await db.webstores_v2.update_one(
        {"id": input.webstore_id},
        {"$inc": {
            "total_sales": subtotal,
            "total_orders": 1,
            "total_profit": total_profit,
            "payout_owed": commission_amount
        }}
    )
    
    logger.info(f"Order {order.id} created with auto-created job {job.id}")
    
    return order


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
    
    # Helper to map product category to job item type
    def map_category_to_item_type(category: str) -> JobItemType:
        """Map webstore product category to job item type"""
        category_map = {
            "apparel": JobItemType.OTHER,  # No direct apparel type
            "signs": JobItemType.BANNER,   # Use banner as closest match
            "decals": JobItemType.DECAL,
            "promotional": JobItemType.OTHER,
            "other": JobItemType.OTHER,
        }
        return category_map.get(category, JobItemType.OTHER)
    
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
