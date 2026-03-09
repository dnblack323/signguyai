"""
Pricing Calculator Routes

This module contains all routes related to:
- Price calculation for various product categories
- Pricing defaults management
- Pricing templates (saved configurations)
- Materials catalog
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from models import (
    UserInDB, PricingCategory,
    PricingDefaults, PricingCalculation, JobItemPricingData,
    PricingTemplate, PricingTemplateCreate
)

# Import from server module
from server import (
    db, logger,
    get_current_active_user,
    get_pricing_defaults, calculate_pricing
)

router = APIRouter(prefix="/pricing", tags=["Pricing"])


# ============== PRICING CALCULATION ==============

class PriceCalculateRequest:
    """Request model for price calculation"""
    def __init__(
        self,
        category: PricingCategory,
        pricing_data: Dict[str, Any],
        quantity: float = 1
    ):
        self.category = category
        self.pricing_data = pricing_data
        self.quantity = quantity


@router.post("/calculate")
async def calculate_price(
    request: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Calculate pricing for an item (real-time preview)"""
    try:
        category = PricingCategory(request.get("category", "custom"))
        pricing_data = JobItemPricingData(**request.get("pricing_data", {}))
        quantity = request.get("quantity", 1)
        
        calculation = await calculate_pricing(
            category,
            pricing_data,
            quantity,
            current_user.tenant_id
        )
        return calculation.model_dump()
    except Exception as e:
        logger.error(f"Pricing calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


# ============== PRICING DEFAULTS ==============

@router.get("/defaults")
async def get_my_pricing_defaults(current_user: UserInDB = Depends(get_current_active_user)):
    """Get pricing defaults for current tenant"""
    defaults = await get_pricing_defaults(current_user.tenant_id)
    return defaults


@router.put("/defaults")
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


# ============== MATERIALS CATALOG ==============

@router.get("/materials")
async def get_materials(
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get available materials (for dropdowns)"""
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


# ============== PRICING TEMPLATES ==============

@router.get("/templates")
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


@router.post("/templates")
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


@router.put("/templates/{template_id}")
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


@router.delete("/templates/{template_id}")
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


@router.put("/templates/{template_id}/favorite")
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



# ============== MATERIALS CATALOG ==============

import uuid
from pydantic import BaseModel, Field

class MaterialCreate(BaseModel):
    """Create a new material"""
    name: str
    category: str = "vinyl"  # vinyl, print_media, laminate, substrate, hardware, supplies, other
    cost: float = 0
    unit: str = "sqft"  # sqft, lnft, each, roll, sheet, gallon, pack
    markup_percent: float = 100
    description: Optional[str] = None
    sku: Optional[str] = None
    supplier: Optional[str] = None
    min_order_qty: int = 1
    is_active: bool = True

class MaterialUpdate(BaseModel):
    """Update a material"""
    name: Optional[str] = None
    category: Optional[str] = None
    cost: Optional[float] = None
    unit: Optional[str] = None
    markup_percent: Optional[float] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    supplier: Optional[str] = None
    min_order_qty: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/materials/catalog")
async def get_materials_catalog(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all materials from the tenant's custom catalog"""
    query = {"tenant_id": current_user.tenant_id}
    if category:
        query["category"] = category
    if is_active is not None:
        query["is_active"] = is_active
    
    materials = await db.materials.find(query, {"_id": 0}).sort("category", 1).to_list(500)
    return materials


@router.post("/materials")
async def create_material(
    data: MaterialCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new material"""
    now = datetime.now(timezone.utc)
    
    material = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "name": data.name,
        "category": data.category,
        "cost": data.cost,
        "unit": data.unit,
        "markup_percent": data.markup_percent,
        "description": data.description,
        "sku": data.sku,
        "supplier": data.supplier,
        "min_order_qty": data.min_order_qty,
        "is_active": data.is_active,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.materials.insert_one(material)
    material.pop("_id", None)
    
    return material


@router.get("/materials/{material_id}")
async def get_material(
    material_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific material"""
    material = await db.materials.find_one(
        {"id": material_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.put("/materials/{material_id}")
async def update_material(
    material_id: str,
    data: MaterialUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a material"""
    # Build update dict with only provided fields
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.materials.update_one(
        {"id": material_id, "tenant_id": current_user.tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Material not found")
    
    material = await db.materials.find_one({"id": material_id}, {"_id": 0})
    return material


@router.delete("/materials/{material_id}")
async def delete_material(
    material_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a material"""
    result = await db.materials.delete_one(
        {"id": material_id, "tenant_id": current_user.tenant_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Material not found")
    
    return {"message": "Material deleted"}


# ============== COMMON SIGN SHOP MATERIALS (PRESETS) ==============

@router.post("/materials/seed-defaults")
async def seed_default_materials(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Seed common sign shop materials as starting point"""
    now = datetime.now(timezone.utc)
    
    # Check if tenant already has materials
    existing = await db.materials.count_documents({"tenant_id": current_user.tenant_id})
    if existing > 0:
        raise HTTPException(status_code=400, detail="Materials already exist. Delete existing materials first to re-seed.")
    
    default_materials = [
        # Vinyl & Film
        {"name": "Cast Vinyl (3M 1080)", "category": "vinyl", "cost": 3.50, "unit": "sqft", "markup_percent": 100, "description": "Premium cast vinyl for vehicle wraps"},
        {"name": "Calendered Vinyl (Oracal 651)", "category": "vinyl", "cost": 0.75, "unit": "sqft", "markup_percent": 150, "description": "General purpose adhesive vinyl"},
        {"name": "Reflective Vinyl", "category": "vinyl", "cost": 4.00, "unit": "sqft", "markup_percent": 100, "description": "DOT reflective for signs"},
        {"name": "Window Perf (50/50)", "category": "vinyl", "cost": 2.25, "unit": "sqft", "markup_percent": 100, "description": "Perforated window film"},
        {"name": "Clear Optically Clear", "category": "vinyl", "cost": 2.50, "unit": "sqft", "markup_percent": 100, "description": "Clear film for glass"},
        {"name": "HTV (Heat Transfer Vinyl)", "category": "vinyl", "cost": 1.50, "unit": "sqft", "markup_percent": 150, "description": "For apparel heat press"},
        
        # Print Media
        {"name": "Glossy Banner (13oz)", "category": "print_media", "cost": 0.35, "unit": "sqft", "markup_percent": 200, "description": "Standard banner material"},
        {"name": "Matte Banner (15oz)", "category": "print_media", "cost": 0.45, "unit": "sqft", "markup_percent": 200, "description": "Heavy duty banner"},
        {"name": "Printable Vinyl (Avery)", "category": "print_media", "cost": 1.25, "unit": "sqft", "markup_percent": 150, "description": "White printable adhesive vinyl"},
        {"name": "Canvas", "category": "print_media", "cost": 2.00, "unit": "sqft", "markup_percent": 150, "description": "Artist canvas for prints"},
        {"name": "Photo Paper", "category": "print_media", "cost": 0.50, "unit": "sqft", "markup_percent": 200, "description": "Glossy photo paper"},
        {"name": "Backlit Film", "category": "print_media", "cost": 1.75, "unit": "sqft", "markup_percent": 150, "description": "For lightboxes"},
        
        # Laminate
        {"name": "Gloss Laminate", "category": "laminate", "cost": 0.40, "unit": "sqft", "markup_percent": 150, "description": "Glossy overlaminate"},
        {"name": "Matte Laminate", "category": "laminate", "cost": 0.45, "unit": "sqft", "markup_percent": 150, "description": "Matte overlaminate"},
        {"name": "Anti-Graffiti Laminate", "category": "laminate", "cost": 1.25, "unit": "sqft", "markup_percent": 100, "description": "Protective anti-vandal"},
        {"name": "Floor Laminate", "category": "laminate", "cost": 1.50, "unit": "sqft", "markup_percent": 100, "description": "Non-slip floor graphic lam"},
        
        # Substrates
        {"name": "Coroplast (4mm)", "category": "substrate", "cost": 0.45, "unit": "sqft", "markup_percent": 200, "description": "Corrugated plastic"},
        {"name": "Aluminum Composite (3mm)", "category": "substrate", "cost": 2.50, "unit": "sqft", "markup_percent": 100, "description": "ACM/Dibond panel"},
        {"name": "PVC Board (3mm)", "category": "substrate", "cost": 0.75, "unit": "sqft", "markup_percent": 150, "description": "Sintra/Forex"},
        {"name": "Foam Board (3/16\")", "category": "substrate", "cost": 0.35, "unit": "sqft", "markup_percent": 200, "description": "Gator board"},
        {"name": "MDO Plywood", "category": "substrate", "cost": 1.50, "unit": "sqft", "markup_percent": 150, "description": "Medium density overlay"},
        {"name": "Acrylic (1/4\")", "category": "substrate", "cost": 4.00, "unit": "sqft", "markup_percent": 100, "description": "Clear acrylic sheet"},
        
        # Hardware & Mounting
        {"name": "H-Stakes (Wire)", "category": "hardware", "cost": 1.25, "unit": "each", "markup_percent": 100, "description": "Yard sign stakes"},
        {"name": "Grommets", "category": "hardware", "cost": 0.25, "unit": "each", "markup_percent": 200, "description": "Brass grommets for banners"},
        {"name": "Pole Pockets", "category": "hardware", "cost": 2.50, "unit": "lnft", "markup_percent": 100, "description": "Sewn pole pocket"},
        {"name": "Standoffs (1\" Chrome)", "category": "hardware", "cost": 3.50, "unit": "each", "markup_percent": 100, "description": "Sign mounting standoffs"},
        {"name": "Banner Hanging Kit", "category": "hardware", "cost": 15.00, "unit": "each", "markup_percent": 75, "description": "Ropes and carabiners"},
        {"name": "Suction Cups (Heavy)", "category": "hardware", "cost": 2.00, "unit": "each", "markup_percent": 100, "description": "Window sign suction cups"},
        
        # Supplies
        {"name": "Transfer Tape (Med Tack)", "category": "supplies", "cost": 0.15, "unit": "sqft", "markup_percent": 200, "description": "Application tape"},
        {"name": "Rivet Tape", "category": "supplies", "cost": 0.50, "unit": "lnft", "markup_percent": 150, "description": "For banner hems"},
        {"name": "Edge Sealer", "category": "supplies", "cost": 25.00, "unit": "each", "markup_percent": 50, "description": "Per bottle, edge protection"},
        {"name": "Cleaning Solution", "category": "supplies", "cost": 15.00, "unit": "gallon", "markup_percent": 50, "description": "Surface prep cleaner"},
    ]
    
    materials_to_insert = []
    for mat in default_materials:
        materials_to_insert.append({
            "id": str(uuid.uuid4()),
            "tenant_id": current_user.tenant_id,
            **mat,
            "is_active": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        })
    
    await db.materials.insert_many(materials_to_insert)
    
    return {"message": f"Added {len(materials_to_insert)} default materials", "count": len(materials_to_insert)}
